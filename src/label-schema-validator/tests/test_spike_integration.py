from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
from forge_works.dr.label_schema_validator.examples.spike_integration import (
    DeployEvent,
    LabelValidationRejected,
    MockLabelDerivationService,
    generate_deploy_fixture,
)

if TYPE_CHECKING:
    from forge_works.dr.label_schema_validator import EstimandCatalog

FIXTURE_SIZE = 100


@pytest.fixture
def deriver(catalog: EstimandCatalog) -> MockLabelDerivationService:
    return MockLabelDerivationService(catalog=catalog)


def test_rfc_73_fixture_100_events_zero_rejects(deriver: MockLabelDerivationService) -> None:
    fixture = generate_deploy_fixture(FIXTURE_SIZE)
    assert len(fixture) == FIXTURE_SIZE

    for deploy in fixture:
        result = deriver.derive_and_emit(deploy)
        assert result.is_valid, f"deploy {deploy.deploy_id} produced invalid label"

    assert len(deriver.emitted) == FIXTURE_SIZE


def test_fixture_covers_all_eligibility_shapes(deriver: MockLabelDerivationService) -> None:
    fixture = generate_deploy_fixture(FIXTURE_SIZE)
    for deploy in fixture:
        deriver.derive_and_emit(deploy)

    eligibilities = {label["eligibility"] for label in deriver.emitted}
    assert "eligible" in eligibilities
    assert "censored" in eligibilities
    assert "missing_data" in eligibilities


def test_halt_on_reject_raises(catalog: EstimandCatalog) -> None:
    class BrokenDeriver(MockLabelDerivationService):
        def _derive(self, deploy: DeployEvent) -> dict[str, Any]:
            label = super()._derive(deploy)
            label.pop("label_id")
            return label

    broken = BrokenDeriver(catalog=catalog)
    fixture = generate_deploy_fixture(3)
    with pytest.raises(LabelValidationRejected) as exc_info:
        broken.derive_and_emit(fixture[0])

    assert exc_info.value.deploy.deploy_id == fixture[0].deploy_id
    assert any(err.code == "MissingRequiredField" for err in exc_info.value.result.errors)
    assert len(broken.emitted) == 0


def test_censored_labels_carry_original_horizon_end(deriver: MockLabelDerivationService) -> None:
    fixture = generate_deploy_fixture(FIXTURE_SIZE)
    for deploy in fixture:
        deriver.derive_and_emit(deploy)

    censored = [label for label in deriver.emitted if label["eligibility"] == "censored"]
    assert len(censored) > 0
    for label in censored:
        assert "original_horizon_end" in label
        assert label["observation_window"]["end"] < label["original_horizon_end"]
        assert "outcome" not in label


def test_eligible_labels_carry_outcome(deriver: MockLabelDerivationService) -> None:
    fixture = generate_deploy_fixture(FIXTURE_SIZE)
    for deploy in fixture:
        deriver.derive_and_emit(deploy)

    eligible = [label for label in deriver.emitted if label["eligibility"] == "eligible"]
    assert len(eligible) > 0
    for label in eligible:
        assert label["outcome"] in ("slo_breach_occurred", "slo_breach_absent")


def test_no_stale_warnings(deriver: MockLabelDerivationService) -> None:
    fixture = generate_deploy_fixture(FIXTURE_SIZE)
    for deploy in fixture:
        deriver.derive_and_emit(deploy)

    seen_codes = set(deriver.warnings_seen)
    assert "GovernanceEnvelopeMinimal" not in seen_codes
    assert "CensoredWindowUnverifiable" not in seen_codes


def test_synthetic_fixture_is_deterministic() -> None:
    first = generate_deploy_fixture(FIXTURE_SIZE)
    second = generate_deploy_fixture(FIXTURE_SIZE)
    assert [d.deploy_id for d in first] == [d.deploy_id for d in second]
    assert [d.commit_sha for d in first] == [d.commit_sha for d in second]


def test_hand_authored_censored_deploy_via_spike(
    catalog: EstimandCatalog, deriver: MockLabelDerivationService
) -> None:
    base = datetime(2026, 7, 24, 10, 15, 3, tzinfo=UTC)
    censored_deploy = DeployEvent(
        deploy_id="dep_hand_censored",
        commit_sha="8f3b21c" + "0" * 33,  # pragma: allowlist secret
        service="webhook-gateway",
        environment="prod",
        deployed_at=base,
        slo_breach_at=None,
        next_deploy_at=base.replace(minute=45),
    )
    result = deriver.derive_and_emit(censored_deploy)
    assert result.is_valid
    label = deriver.emitted[-1]
    assert label["eligibility"] == "censored"
    assert label["original_horizon_end"] == "2026-07-24T11:15:03Z"
    assert label["observation_window"]["end"] == "2026-07-24T10:45:03Z"
