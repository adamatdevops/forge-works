from __future__ import annotations

from pathlib import Path
from typing import Any

from forge_works.dr.label_schema_validator import load_catalog_from_yaml, validate_label_event

REPO_ROOT = Path(__file__).resolve().parents[3]
CATALOG_PATH = REPO_ROOT / "docs" / "decisions" / "dynamic-reliability" / "estimand_catalog.yaml"


def test_load_seeded_catalog() -> None:
    catalog = load_catalog_from_yaml(CATALOG_PATH)
    assert "deploy_slo_breach_60m_association_v0" in catalog.entries
    entry = catalog.lookup("deploy_slo_breach_60m_association_v0")
    assert entry is not None
    assert "slo_breach_occurred" in entry.outcome_vocabulary
    assert "slo_breach_absent" in entry.outcome_vocabulary


def test_outcome_not_in_vocabulary_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["outcome"] = "made_up_outcome"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "OutcomeNotInVocabulary" for err in result.errors)


def test_estimand_not_in_catalog_rejects(
    valid_eligible_event: dict[str, Any], catalog: Any
) -> None:
    valid_eligible_event["estimand_id"] = "unknown_estimand_v0"
    result = validate_label_event(valid_eligible_event, estimand_catalog=catalog)
    assert not result.is_valid
    assert any(err.code == "EstimandNotInCatalog" for err in result.errors)


def test_censored_no_outcome_no_catalog_check(
    valid_censored_event: dict[str, Any], catalog: Any
) -> None:
    result = validate_label_event(valid_censored_event, estimand_catalog=catalog)
    assert result.is_valid
