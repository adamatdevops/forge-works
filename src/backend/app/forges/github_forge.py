"""GitHub Forge - Bidirectional bridge between GitHub and ForgeWorks.

This Forge enables GitHub to truly collaborate with ForgeWorks by:
1. LISTENING to GitHub webhooks (PRs, workflows, releases)
2. CORRELATING GitHub events with ForgeWorks services
3. BROADCASTING real-time updates to the dashboard
4. BRIDGING GitHub Actions status to Kubernetes deployments

The Gap It Fills:
- GitHub knows build status, but can't tell Kubernetes
- Kubernetes knows deployment health, but can't tell GitHub
- GitHub Forge bridges this gap

Example Use Case (from user's vision):
"If Kubernetes can't natively access GitHub Runners and generate
its own reports, ForgeWorks can create a template that makes it happen."

This Forge:
1. Listens for GitHub Actions workflow completions
2. Correlates them with Kubernetes deployments
3. Updates deployment status based on build results
4. Generates reports connecting build → deploy → health
"""

import random
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.events import (
    broadcast_anomaly_detected,
    broadcast_pipeline_completed,
    broadcast_pipeline_failed,
    broadcast_pipeline_started,
    broadcast_service_status_changed,
)
from app.forges.base import (
    ForgeAdapter,
    ForgeConfig,
    ReconciliationStrategy,
    StateDiff,
    WebhookPayload,
)


class GitHubForge(ForgeAdapter):
    """Bidirectional bridge between GitHub and ForgeWorks.

    Handles:
    - Pull Request events (opened, closed, merged)
    - Workflow Run events (started, completed, failed)
    - Release events (published)
    - Push events (for deployment triggers)

    Bridges:
    - Build status → Service health
    - PR status → Deployment readiness
    - Workflow results → Anomaly detection
    """

    def __init__(
        self,
        config: ForgeConfig | None = None,
        github_org: str = "forge-works",
    ) -> None:
        """Initialize GitHub Forge.

        Args:
            config: Forge configuration
            github_org: GitHub organization to monitor
        """
        super().__init__(
            config
            or ForgeConfig(
                reconciliation_strategy=ReconciliationStrategy.EXTERNAL_WINS,
                reconcile_interval_seconds=60,
            )
        )
        self.github_org = github_org

        # Cache for correlating GitHub → ForgeWorks entities
        self._repo_to_service: dict[str, str] = {}  # repo_name → service_id
        self._workflow_to_service: dict[str, str] = {}  # workflow_id → service_id
        self._pr_cache: dict[str, dict[str, Any]] = {}  # pr_id → pr_data
        self._workflow_cache: dict[str, dict[str, Any]] = {}  # workflow_id → run_data

    @property
    def forge_name(self) -> str:
        return "github-forge"

    @property
    def supported_webhook_events(self) -> list[str]:
        return [
            "pull_request.opened",
            "pull_request.closed",
            "pull_request.merged",
            "pull_request.synchronize",
            "workflow_run.requested",
            "workflow_run.in_progress",
            "workflow_run.completed",
            "push",
            "release.published",
            "check_run.completed",
            "check_suite.completed",
        ]

    # =========================================================================
    # Webhook Event Handlers
    # =========================================================================

    async def handle_webhook_event(self, payload: WebhookPayload) -> None:
        """Route webhook to appropriate handler."""
        handlers = {
            "pull_request.opened": self._handle_pr_opened,
            "pull_request.closed": self._handle_pr_closed,
            "pull_request.merged": self._handle_pr_merged,
            "pull_request.synchronize": self._handle_pr_updated,
            "workflow_run.requested": self._handle_workflow_started,
            "workflow_run.in_progress": self._handle_workflow_in_progress,
            "workflow_run.completed": self._handle_workflow_completed,
            "push": self._handle_push,
            "release.published": self._handle_release,
        }

        handler = handlers.get(payload.event_type)
        if handler:
            await handler(payload)

    async def _handle_pr_opened(self, payload: WebhookPayload) -> None:
        """Handle new pull request - track for deployment readiness."""
        pr = payload.raw_payload.get("pull_request", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")

        pr_data = {
            "number": pr.get("number"),
            "title": pr.get("title"),
            "author": pr.get("user", {}).get("login"),
            "state": "open",
            "repo": repo,
            "branch": pr.get("head", {}).get("ref"),
            "base": pr.get("base", {}).get("ref"),
            "url": pr.get("html_url"),
            "created_at": pr.get("created_at"),
        }

        pr_id = f"{repo}/{pr.get('number')}"
        self._pr_cache[pr_id] = pr_data

        # Correlate with service if we have a mapping
        service_id = self._repo_to_service.get(repo)
        if service_id:
            # Broadcast that a PR affects this service
            await broadcast_service_status_changed(
                service_id=service_id,
                old_status="stable",
                new_status="pending_changes",
            )

    async def _handle_pr_closed(self, payload: WebhookPayload) -> None:
        """Handle PR closed (merged or rejected)."""
        pr = payload.raw_payload.get("pull_request", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")
        merged = pr.get("merged", False)

        pr_id = f"{repo}/{pr.get('number')}"

        if merged:
            await self._handle_pr_merged(payload)
        else:
            # PR was closed without merging
            if pr_id in self._pr_cache:
                self._pr_cache[pr_id]["state"] = "closed"

    async def _handle_pr_merged(self, payload: WebhookPayload) -> None:
        """Handle PR merged - trigger deployment readiness check."""
        pr = payload.raw_payload.get("pull_request", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")
        base_branch = pr.get("base", {}).get("ref", "main")

        pr_id = f"{repo}/{pr.get('number')}"
        if pr_id in self._pr_cache:
            self._pr_cache[pr_id]["state"] = "merged"

        # If merged to main/master, service is ready for deployment
        if base_branch in ("main", "master"):
            service_id = self._repo_to_service.get(repo)
            if service_id:
                await broadcast_service_status_changed(
                    service_id=service_id,
                    old_status="pending_changes",
                    new_status="ready_to_deploy",
                )

    async def _handle_pr_updated(self, payload: WebhookPayload) -> None:
        """Handle PR synchronize (new commits pushed)."""
        pr = payload.raw_payload.get("pull_request", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")

        pr_id = f"{repo}/{pr.get('number')}"
        if pr_id in self._pr_cache:
            self._pr_cache[pr_id]["updated_at"] = datetime.now(UTC).isoformat()

    async def _handle_workflow_started(self, payload: WebhookPayload) -> None:
        """Handle workflow run started - broadcast pipeline started."""
        workflow = payload.raw_payload.get("workflow_run", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")

        workflow_data = {
            "id": workflow.get("id"),
            "name": workflow.get("name"),
            "repo": repo,
            "status": "queued",
            "branch": workflow.get("head_branch"),
            "commit_sha": workflow.get("head_sha"),
            "url": workflow.get("html_url"),
            "started_at": workflow.get("created_at"),
        }

        workflow_id = str(workflow.get("id"))
        self._workflow_cache[workflow_id] = workflow_data

        await broadcast_pipeline_started(
            {
                "pipeline_id": workflow_id,
                "name": workflow.get("name"),
                "repo": repo,
                "branch": workflow.get("head_branch"),
                "trigger": "github_actions",
            }
        )

    async def _handle_workflow_in_progress(self, payload: WebhookPayload) -> None:
        """Handle workflow run in progress."""
        workflow = payload.raw_payload.get("workflow_run", {})
        workflow_id = str(workflow.get("id"))

        if workflow_id in self._workflow_cache:
            self._workflow_cache[workflow_id]["status"] = "in_progress"
            self._workflow_cache[workflow_id]["running_at"] = datetime.now(UTC).isoformat()

    async def _handle_workflow_completed(self, payload: WebhookPayload) -> None:
        """Handle workflow completed - THE KEY BRIDGE EVENT.

        This is where ForgeWorks fills the gap:
        - GitHub knows the build passed/failed
        - Kubernetes needs to know if it should deploy
        - ForgeWorks bridges this by correlating build → service → deployment
        """
        workflow = payload.raw_payload.get("workflow_run", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")
        conclusion = workflow.get("conclusion", "unknown")  # success, failure, cancelled

        workflow_id = str(workflow.get("id"))
        workflow_name = workflow.get("name", "")

        if workflow_id in self._workflow_cache:
            self._workflow_cache[workflow_id]["status"] = "completed"
            self._workflow_cache[workflow_id]["conclusion"] = conclusion
            self._workflow_cache[workflow_id]["completed_at"] = datetime.now(UTC).isoformat()

        # Calculate duration if we have start time
        duration = None
        if workflow_id in self._workflow_cache:
            started = self._workflow_cache[workflow_id].get("started_at")
            if started:
                try:
                    start_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
                    duration = (datetime.now(UTC) - start_dt.replace(tzinfo=None)).total_seconds()
                except ValueError:
                    pass

        # Broadcast pipeline completion
        if conclusion == "success":
            await broadcast_pipeline_completed(
                pipeline_id=workflow_id,
                status="success",
                duration_seconds=duration,
            )

            # KEY BRIDGE: Update service status based on build success
            service_id = self._repo_to_service.get(repo)
            if service_id:
                await broadcast_service_status_changed(
                    service_id=service_id,
                    old_status="building",
                    new_status="ready_to_deploy",
                )

        elif conclusion == "failure":
            await broadcast_pipeline_failed(
                pipeline_id=workflow_id,
                error=f"Workflow '{workflow_name}' failed",
            )

            # KEY BRIDGE: Create anomaly when build fails
            await broadcast_anomaly_detected(
                {
                    "type": "build_failure",
                    "severity": "high",
                    "source": "github_forge",
                    "title": f"Build failed: {workflow_name}",
                    "description": f"GitHub Actions workflow '{workflow_name}' failed in {repo}",
                    "metadata": {
                        "repo": repo,
                        "workflow": workflow_name,
                        "workflow_id": workflow_id,
                        "branch": workflow.get("head_branch"),
                        "commit": workflow.get("head_sha"),
                        "url": workflow.get("html_url"),
                    },
                }
            )

            # Update service status to indicate build failure
            service_id = self._repo_to_service.get(repo)
            if service_id:
                await broadcast_service_status_changed(
                    service_id=service_id,
                    old_status="building",
                    new_status="build_failed",
                )

    async def _handle_push(self, payload: WebhookPayload) -> None:
        """Handle push event - track commits for deployment correlation."""
        repo = payload.raw_payload.get("repository", {}).get("name", "")
        ref = payload.raw_payload.get("ref", "")
        payload.raw_payload.get("commits", [])

        if ref in ("refs/heads/main", "refs/heads/master"):
            # Push to main branch - service may need deployment
            service_id = self._repo_to_service.get(repo)
            if service_id:
                await broadcast_service_status_changed(
                    service_id=service_id,
                    old_status="stable",
                    new_status="building",
                )

    async def _handle_release(self, payload: WebhookPayload) -> None:
        """Handle release published - track for version correlation."""
        release = payload.raw_payload.get("release", {})
        repo = payload.raw_payload.get("repository", {}).get("name", "")

        {
            "tag": release.get("tag_name"),
            "name": release.get("name"),
            "body": release.get("body"),
            "prerelease": release.get("prerelease", False),
            "url": release.get("html_url"),
        }

        # Store for correlation with deployments
        service_id = self._repo_to_service.get(repo)
        if service_id:
            await broadcast_service_status_changed(
                service_id=service_id,
                old_status="ready_to_deploy",
                new_status="release_available",
            )

    # =========================================================================
    # Service Correlation
    # =========================================================================

    def register_service_repo(self, service_id: str, repo_name: str) -> None:
        """Register a mapping between a ForgeWorks service and a GitHub repo.

        This is the key to bridging: knowing which GitHub events
        affect which ForgeWorks services.
        """
        self._repo_to_service[repo_name] = service_id

    def unregister_service_repo(self, repo_name: str) -> None:
        """Remove a service-repo mapping."""
        self._repo_to_service.pop(repo_name, None)

    def get_service_for_repo(self, repo_name: str) -> str | None:
        """Get the service ID for a given repo."""
        return self._repo_to_service.get(repo_name)

    # =========================================================================
    # State Management
    # =========================================================================

    async def fetch_external_state(self) -> dict[str, Any]:
        """Fetch current state from GitHub (PRs, workflows, etc.)."""
        # In live mode, this would call GitHub API
        # For now, return cached state
        return {
            "pull_requests": dict(self._pr_cache),
            "workflows": dict(self._workflow_cache),
            "repos": list(self._repo_to_service.keys()),
        }

    async def get_local_state(self) -> dict[str, Any]:
        """Get local state from ForgeWorks database."""
        # Would query database for service states
        return {
            "services": {},
            "repo_mappings": dict(self._repo_to_service),
        }

    async def apply_external_state(self, diff: StateDiff) -> bool:
        """Apply GitHub state to local database."""
        # Update local cache with external state
        if diff.entity_type == "pull_requests":
            self._pr_cache[diff.entity_id] = diff.external_state
        elif diff.entity_type == "workflows":
            self._workflow_cache[diff.entity_id] = diff.external_state
        return True

    async def push_local_state(self, diff: StateDiff) -> bool:
        """Push local state to GitHub (usually not needed)."""
        # GitHub is typically source of truth
        # This would only be used for automated PR creation, etc.
        return True

    # =========================================================================
    # Mock Event Generation
    # =========================================================================

    async def generate_mock_events(self) -> list[WebhookPayload]:
        """Generate realistic mock events for development/demos."""
        events: list[WebhookPayload] = []

        # Generate a random event type
        event_type = random.choice(
            [
                "workflow_run.completed",
                "pull_request.opened",
                "push",
            ]
        )

        repos = list(self._repo_to_service.keys()) or ["user-service", "api-gateway"]
        repo = random.choice(repos)

        if event_type == "workflow_run.completed":
            workflow_id = random.randint(1000000, 9999999)
            conclusion = random.choice(["success", "success", "success", "failure"])  # 75% success

            events.append(
                WebhookPayload(
                    source="github",
                    event_type=event_type,
                    timestamp=datetime.now(UTC),
                    raw_payload={
                        "action": "completed",
                        "workflow_run": {
                            "id": workflow_id,
                            "name": "CI/CD Pipeline",
                            "head_branch": "main",
                            "head_sha": f"abc{random.randint(1000, 9999)}def",
                            "conclusion": conclusion,
                            "html_url": f"https://github.com/{self.github_org}/{repo}/actions/runs/{workflow_id}",
                            "created_at": (datetime.now(UTC) - timedelta(minutes=5)).isoformat(),
                        },
                        "repository": {
                            "name": repo,
                            "full_name": f"{self.github_org}/{repo}",
                        },
                    },
                )
            )

        elif event_type == "pull_request.opened":
            pr_number = random.randint(100, 999)
            events.append(
                WebhookPayload(
                    source="github",
                    event_type=event_type,
                    timestamp=datetime.now(UTC),
                    raw_payload={
                        "action": "opened",
                        "pull_request": {
                            "number": pr_number,
                            "title": f"Feature: Add new functionality #{pr_number}",
                            "user": {"login": random.choice(["alice", "bob", "charlie"])},
                            "head": {"ref": f"feature/new-{pr_number}"},
                            "base": {"ref": "main"},
                            "html_url": f"https://github.com/{self.github_org}/{repo}/pull/{pr_number}",
                            "created_at": datetime.now(UTC).isoformat(),
                        },
                        "repository": {
                            "name": repo,
                            "full_name": f"{self.github_org}/{repo}",
                        },
                    },
                )
            )

        elif event_type == "push":
            events.append(
                WebhookPayload(
                    source="github",
                    event_type=event_type,
                    timestamp=datetime.now(UTC),
                    raw_payload={
                        "ref": "refs/heads/main",
                        "commits": [
                            {
                                "id": f"abc{random.randint(1000, 9999)}",
                                "message": "Update configuration",
                                "author": {"name": random.choice(["Alice", "Bob"])},
                            }
                        ],
                        "repository": {
                            "name": repo,
                            "full_name": f"{self.github_org}/{repo}",
                        },
                    },
                )
            )

        return events


# Singleton instance for the GitHub Forge
_github_forge: GitHubForge | None = None


def get_github_forge(config: ForgeConfig | None = None) -> GitHubForge:
    """Get or create the GitHub Forge singleton."""
    global _github_forge
    if _github_forge is None:
        _github_forge = GitHubForge(config)
    return _github_forge
