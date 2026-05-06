"""
Tests for GitHub webhook routing.

Specifically: workflow_run / workflow_job events should be published to the
github-actions topic, while other GH events keep going to the github topic.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings


def _gh_payload(repo: str = "owner/repo") -> str:
    return json.dumps({
        "action": "completed",
        "repository": {"full_name": repo},
        "sender": {"login": "ci-bot"},
    })


class TestGitHubActionsRouting:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("event_header", ["workflow_run", "workflow_job"])
    async def test_workflow_events_route_to_github_actions_topic(
        self, client, event_header,
    ):
        with patch(
            "app.routes.webhooks.producer.publish",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_publish:
            resp = await client.post(
                "/webhook/github",
                content=_gh_payload(),
                headers={
                    "content-type": "application/json",
                    "x-github-event": event_header,
                },
            )
        assert resp.status_code == 200
        assert mock_publish.called
        published_topic = mock_publish.call_args.args[0]
        assert published_topic == settings.kafka_topic_github_actions

    @pytest.mark.asyncio
    @pytest.mark.parametrize("event_header", ["push", "pull_request", "issues"])
    async def test_non_workflow_events_keep_github_topic(self, client, event_header):
        with patch(
            "app.routes.webhooks.producer.publish",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_publish:
            resp = await client.post(
                "/webhook/github",
                content=_gh_payload(),
                headers={
                    "content-type": "application/json",
                    "x-github-event": event_header,
                },
            )
        assert resp.status_code == 200
        assert mock_publish.called
        published_topic = mock_publish.call_args.args[0]
        assert published_topic == settings.kafka_topic_github
