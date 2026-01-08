"""GitHub adapter for repository and workflow management."""

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from app.adapters.base import AdapterHealth, AdapterMode, BaseAdapter


class WorkflowStatus(str, Enum):
    """GitHub Actions workflow status."""

    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class WorkflowConclusion(str, Enum):
    """GitHub Actions workflow conclusion."""

    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


class PRState(str, Enum):
    """Pull request state."""

    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


@dataclass
class Repository:
    """GitHub repository representation."""

    id: str
    name: str
    full_name: str
    description: str | None
    default_branch: str
    private: bool
    html_url: str
    clone_url: str
    created_at: datetime
    updated_at: datetime
    language: str | None = None
    topics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "default_branch": self.default_branch,
            "private": self.private,
            "html_url": self.html_url,
            "clone_url": self.clone_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "language": self.language,
            "topics": self.topics,
        }


@dataclass
class Commit:
    """GitHub commit representation."""

    sha: str
    message: str
    author: str
    author_email: str
    timestamp: datetime
    url: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sha": self.sha,
            "message": self.message,
            "author": self.author,
            "author_email": self.author_email,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
        }


@dataclass
class Branch:
    """GitHub branch representation."""

    name: str
    sha: str
    protected: bool
    ahead_by: int = 0
    behind_by: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "sha": self.sha,
            "protected": self.protected,
            "ahead_by": self.ahead_by,
            "behind_by": self.behind_by,
        }


@dataclass
class PullRequest:
    """GitHub pull request representation."""

    id: str
    number: int
    title: str
    body: str | None
    state: PRState
    author: str
    source_branch: str
    target_branch: str
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None = None
    html_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "state": self.state.value,
            "author": self.author,
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "merged_at": self.merged_at.isoformat() if self.merged_at else None,
            "html_url": self.html_url,
        }


@dataclass
class WorkflowRun:
    """GitHub Actions workflow run representation."""

    id: str
    name: str
    status: WorkflowStatus
    conclusion: WorkflowConclusion | None
    head_branch: str
    head_sha: str
    run_number: int
    created_at: datetime
    updated_at: datetime
    html_url: str
    duration_seconds: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "conclusion": self.conclusion.value if self.conclusion else None,
            "head_branch": self.head_branch,
            "head_sha": self.head_sha,
            "run_number": self.run_number,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "html_url": self.html_url,
            "duration_seconds": self.duration_seconds,
        }


class GitHubAdapter(BaseAdapter):
    """GitHub adapter for repository and CI/CD integration.

    In mock mode, returns realistic data for IDP demonstrations.
    In live mode, connects to GitHub API (requires token configuration).
    """

    def __init__(
        self,
        mode: AdapterMode = AdapterMode.MOCK,
        token: str | None = None,
        org: str = "forge-org",
    ) -> None:
        """Initialize GitHub adapter."""
        super().__init__(mode)
        self.token = token
        self.org = org
        self._mock_repos = self._generate_mock_repos()

    @property
    def name(self) -> str:
        """Return adapter name."""
        return "github"

    async def health_check(self) -> AdapterHealth:
        """Check GitHub API connectivity."""
        self._last_health_check = datetime.now(timezone.utc)

        if self.is_mock():
            # Simulate slight latency
            await asyncio.sleep(0.01)
            return AdapterHealth(
                name=self.name,
                healthy=True,
                mode=self.mode,
                latency_ms=10.5,
                last_check=self._last_health_check,
            )

        # Live mode - would make actual API call
        # TODO: Implement actual GitHub API health check
        return AdapterHealth(
            name=self.name,
            healthy=False,
            mode=self.mode,
            last_check=self._last_health_check,
            error="Live mode not yet implemented",
        )

    async def get_repository(self, repo_name: str) -> Repository | None:
        """Get repository details by name."""
        if self.is_mock():
            return self._mock_repos.get(repo_name)

        # TODO: Implement actual GitHub API call
        raise NotImplementedError("Live mode not yet implemented")

    async def list_repositories(
        self,
        limit: int = 100,
        language: str | None = None,
    ) -> list[Repository]:
        """List organization repositories."""
        if self.is_mock():
            repos = list(self._mock_repos.values())
            if language:
                repos = [r for r in repos if r.language == language]
            return repos[:limit]

        raise NotImplementedError("Live mode not yet implemented")

    async def get_branches(self, repo_name: str) -> list[Branch]:
        """Get branches for a repository."""
        if self.is_mock():
            return self._generate_mock_branches(repo_name)

        raise NotImplementedError("Live mode not yet implemented")

    async def get_recent_commits(
        self,
        repo_name: str,
        branch: str = "main",
        limit: int = 10,
    ) -> list[Commit]:
        """Get recent commits for a repository branch."""
        if self.is_mock():
            return self._generate_mock_commits(repo_name, branch, limit)

        raise NotImplementedError("Live mode not yet implemented")

    async def get_pull_requests(
        self,
        repo_name: str,
        state: PRState | None = None,
        limit: int = 20,
    ) -> list[PullRequest]:
        """Get pull requests for a repository."""
        if self.is_mock():
            return self._generate_mock_prs(repo_name, state, limit)

        raise NotImplementedError("Live mode not yet implemented")

    async def get_workflow_runs(
        self,
        repo_name: str,
        workflow_name: str | None = None,
        limit: int = 10,
    ) -> list[WorkflowRun]:
        """Get recent workflow runs for a repository."""
        if self.is_mock():
            return self._generate_mock_workflow_runs(repo_name, workflow_name, limit)

        raise NotImplementedError("Live mode not yet implemented")

    async def create_repository_from_template(
        self,
        template_repo: str,
        new_repo_name: str,
        description: str | None = None,
        private: bool = True,
    ) -> Repository:
        """Create a new repository from a template (Golden Path)."""
        if self.is_mock():
            now = datetime.now(timezone.utc)
            repo = Repository(
                id=f"repo-{new_repo_name}",
                name=new_repo_name,
                full_name=f"{self.org}/{new_repo_name}",
                description=description or f"Created from template {template_repo}",
                default_branch="main",
                private=private,
                html_url=f"https://github.com/{self.org}/{new_repo_name}",
                clone_url=f"https://github.com/{self.org}/{new_repo_name}.git",
                created_at=now,
                updated_at=now,
                language="Python",
                topics=["golden-path", "generated"],
            )
            self._mock_repos[new_repo_name] = repo
            return repo

        raise NotImplementedError("Live mode not yet implemented")

    def _generate_mock_repos(self) -> dict[str, Repository]:
        """Generate mock repository data for demonstrations."""
        now = datetime.now(timezone.utc)
        repos = {}

        mock_data = [
            {
                "name": "user-service",
                "description": "User authentication and profile management API",
                "language": "Python",
                "topics": ["api", "auth", "golden-path"],
                "age_days": 180,
            },
            {
                "name": "order-service",
                "description": "Order processing and fulfillment service",
                "language": "Python",
                "topics": ["api", "orders", "golden-path"],
                "age_days": 120,
            },
            {
                "name": "payment-gateway",
                "description": "Payment processing integration service",
                "language": "Go",
                "topics": ["api", "payments", "critical"],
                "age_days": 90,
            },
            {
                "name": "notification-service",
                "description": "Multi-channel notification delivery service",
                "language": "Python",
                "topics": ["async", "notifications", "golden-path"],
                "age_days": 60,
            },
            {
                "name": "analytics-pipeline",
                "description": "Real-time analytics data pipeline",
                "language": "Python",
                "topics": ["data", "streaming", "kafka"],
                "age_days": 45,
            },
            {
                "name": "ml-recommendation-engine",
                "description": "ML-powered product recommendation service",
                "language": "Python",
                "topics": ["ml", "recommendations", "golden-path"],
                "age_days": 30,
            },
            {
                "name": "inventory-tracker",
                "description": "Real-time inventory management service",
                "language": "Go",
                "topics": ["api", "inventory", "high-performance"],
                "age_days": 150,
            },
            {
                "name": "api-gateway",
                "description": "Central API gateway and rate limiting",
                "language": "Go",
                "topics": ["gateway", "infrastructure", "critical"],
                "age_days": 200,
            },
        ]

        for data in mock_data:
            created = now - timedelta(days=data["age_days"])
            updated = now - timedelta(hours=random.randint(1, 48))
            name = data["name"]

            repos[name] = Repository(
                id=f"repo-{name}",
                name=name,
                full_name=f"{self.org}/{name}",
                description=data["description"],
                default_branch="main",
                private=True,
                html_url=f"https://github.com/{self.org}/{name}",
                clone_url=f"https://github.com/{self.org}/{name}.git",
                created_at=created,
                updated_at=updated,
                language=data["language"],
                topics=data["topics"],
            )

        return repos

    def _generate_mock_branches(self, repo_name: str) -> list[Branch]:
        """Generate mock branch data."""
        branches = [
            Branch(
                name="main",
                sha=f"abc{random.randint(1000, 9999)}def",
                protected=True,
            ),
            Branch(
                name="develop",
                sha=f"def{random.randint(1000, 9999)}ghi",
                protected=True,
                ahead_by=random.randint(0, 5),
            ),
        ]

        # Add some feature branches
        feature_branches = [
            "feature/add-caching",
            "feature/improve-logging",
            "fix/memory-leak",
            "chore/update-deps",
        ]

        for fb in random.sample(feature_branches, k=random.randint(1, 3)):
            branches.append(
                Branch(
                    name=fb,
                    sha=f"fea{random.randint(1000, 9999)}ture",
                    protected=False,
                    ahead_by=random.randint(1, 10),
                    behind_by=random.randint(0, 3),
                )
            )

        return branches

    def _generate_mock_commits(
        self,
        repo_name: str,
        branch: str,
        limit: int,
    ) -> list[Commit]:
        """Generate mock commit data."""
        now = datetime.now(timezone.utc)
        commits = []

        messages = [
            "feat: add request validation middleware",
            "fix: resolve race condition in cache layer",
            "chore: update dependencies to latest versions",
            "docs: improve API documentation",
            "refactor: extract common utilities",
            "test: add integration tests for auth flow",
            "perf: optimize database queries",
            "fix: handle edge case in error handler",
            "feat: implement rate limiting",
            "chore: configure CI pipeline",
        ]

        authors = [
            ("Alice Chen", "alice@forge.dev"),
            ("Bob Smith", "bob@forge.dev"),
            ("Carol Davis", "carol@forge.dev"),
            ("Dan Lee", "dan@forge.dev"),
        ]

        for i in range(min(limit, len(messages))):
            author = random.choice(authors)
            sha = f"{random.randint(1000000, 9999999):07x}{random.randint(1000000, 9999999):07x}"

            commits.append(
                Commit(
                    sha=sha,
                    message=messages[i],
                    author=author[0],
                    author_email=author[1],
                    timestamp=now - timedelta(hours=i * random.randint(2, 8)),
                    url=f"https://github.com/{self.org}/{repo_name}/commit/{sha}",
                )
            )

        return commits

    def _generate_mock_prs(
        self,
        repo_name: str,
        state: PRState | None,
        limit: int,
    ) -> list[PullRequest]:
        """Generate mock pull request data."""
        now = datetime.now(timezone.utc)
        prs = []

        pr_data = [
            {
                "title": "feat: Add request caching layer",
                "branch": "feature/add-caching",
                "state": PRState.OPEN,
                "age_hours": 4,
            },
            {
                "title": "fix: Resolve authentication timeout",
                "branch": "fix/auth-timeout",
                "state": PRState.MERGED,
                "age_hours": 24,
            },
            {
                "title": "chore: Update to Python 3.12",
                "branch": "chore/python-upgrade",
                "state": PRState.OPEN,
                "age_hours": 12,
            },
            {
                "title": "feat: Implement webhook notifications",
                "branch": "feature/webhooks",
                "state": PRState.MERGED,
                "age_hours": 72,
            },
            {
                "title": "docs: Add API usage examples",
                "branch": "docs/api-examples",
                "state": PRState.CLOSED,
                "age_hours": 48,
            },
        ]

        authors = ["alice", "bob", "carol", "dan"]

        for i, data in enumerate(pr_data[:limit]):
            if state and data["state"] != state:
                continue

            created = now - timedelta(hours=data["age_hours"])
            merged_at = None
            if data["state"] == PRState.MERGED:
                merged_at = created + timedelta(hours=random.randint(2, 12))

            prs.append(
                PullRequest(
                    id=f"pr-{repo_name}-{i + 1}",
                    number=100 + i,
                    title=data["title"],
                    body=f"This PR implements {data['title'].lower()}.",
                    state=data["state"],
                    author=random.choice(authors),
                    source_branch=data["branch"],
                    target_branch="main",
                    created_at=created,
                    updated_at=now - timedelta(hours=random.randint(0, 4)),
                    merged_at=merged_at,
                    html_url=f"https://github.com/{self.org}/{repo_name}/pull/{100 + i}",
                )
            )

        return prs

    def _generate_mock_workflow_runs(
        self,
        repo_name: str,
        workflow_name: str | None,
        limit: int,
    ) -> list[WorkflowRun]:
        """Generate mock workflow run data."""
        now = datetime.now(timezone.utc)
        runs = []

        workflows = ["CI", "Deploy", "Security Scan", "Release"]
        if workflow_name:
            workflows = [workflow_name]

        for i in range(limit):
            wf_name = random.choice(workflows)
            age_hours = i * random.randint(1, 4)
            created = now - timedelta(hours=age_hours)
            duration = random.randint(60, 600)

            # Most runs succeed, some fail
            if random.random() > 0.85:
                status = WorkflowStatus.COMPLETED
                conclusion = WorkflowConclusion.FAILURE
            elif random.random() > 0.95:
                status = WorkflowStatus.IN_PROGRESS
                conclusion = None
                duration = None
            else:
                status = WorkflowStatus.COMPLETED
                conclusion = WorkflowConclusion.SUCCESS

            runs.append(
                WorkflowRun(
                    id=f"run-{repo_name}-{i + 1}",
                    name=wf_name,
                    status=status,
                    conclusion=conclusion,
                    head_branch="main" if random.random() > 0.3 else "develop",
                    head_sha=f"{random.randint(1000000, 9999999):07x}",
                    run_number=500 + i,
                    created_at=created,
                    updated_at=created + timedelta(seconds=duration or 0),
                    html_url=f"https://github.com/{self.org}/{repo_name}/actions/runs/{500 + i}",
                    duration_seconds=duration,
                )
            )

        return runs


# Singleton instance for the application
_github_adapter: GitHubAdapter | None = None


def get_github_adapter(
    mode: AdapterMode = AdapterMode.MOCK,
    token: str | None = None,
) -> GitHubAdapter:
    """Get or create the GitHub adapter instance."""
    global _github_adapter
    if _github_adapter is None:
        _github_adapter = GitHubAdapter(mode=mode, token=token)
    return _github_adapter
