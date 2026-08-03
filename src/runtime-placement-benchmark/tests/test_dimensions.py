from __future__ import annotations

import pytest
from forge_works.dr.ab029_spike.dimensions import (
    DEFAULT_WEIGHTS,
    DIMENSIONS,
    Measurement,
    MeasurementStatus,
    dimension_by_code,
)


def test_eight_dimensions_present() -> None:
    """v0.2: RFC v0.2 added D8 evidence integrity + operability."""
    codes = {d.code for d in DIMENSIONS}
    assert codes == {"D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"}


def test_d8_evidence_integrity_dimension_defined() -> None:
    """v0.2 NEW: D8 must exist with weight 4 per RFC v0.2 §6.2."""
    d8 = dimension_by_code("D8")
    assert d8.name == "Evidence integrity + operability"
    assert d8.default_weight == 4
    assert d8.higher_is_better is True


def test_default_weights_cover_every_dimension() -> None:
    assert DEFAULT_WEIGHTS.keys() == {d.code for d in DIMENSIONS}
    for w in DEFAULT_WEIGHTS.values():
        assert 1 <= w <= 5


def test_dimension_by_code_finds_known() -> None:
    d = dimension_by_code("D3")
    assert d.name == "Model rollout mechanics"


def test_dimension_by_code_raises_on_unknown() -> None:
    with pytest.raises(ValueError, match="unknown dimension code"):
        dimension_by_code("D99")


def test_measurement_ok_requires_value_or_qualitative() -> None:
    with pytest.raises(ValueError, match="value or qualitative"):
        Measurement(dimension_code="D1", status=MeasurementStatus.OK)


def test_measurement_ok_accepts_value() -> None:
    m = Measurement(dimension_code="D1", status=MeasurementStatus.OK, value=42.0)
    assert m.is_real


def test_measurement_not_implemented_is_not_real() -> None:
    m = Measurement(dimension_code="D1", status=MeasurementStatus.NOT_IMPLEMENTED)
    assert not m.is_real


def test_measurement_unknown_dimension_raises() -> None:
    with pytest.raises(ValueError, match="unknown dimension"):
        Measurement(dimension_code="D99", status=MeasurementStatus.NOT_IMPLEMENTED)


# --- v0.2 additions per Codex Loop #4 ---


def test_measurement_frozen_status_forbids_value() -> None:
    """v0.2: FROZEN must NOT carry a value — the point is to prevent score laundering."""
    with pytest.raises(ValueError, match="MUST NOT carry a value"):
        Measurement(dimension_code="D4", status=MeasurementStatus.FROZEN, value=5.0)


def test_measurement_not_measured_status_forbids_value() -> None:
    """v0.2: NOT_MEASURED must NOT carry a value (RFC §6.2.1 unmeasured → score 0, not passed)."""
    with pytest.raises(ValueError, match="MUST NOT carry a value"):
        Measurement(dimension_code="D1", status=MeasurementStatus.NOT_MEASURED, value=42.0)


def test_measurement_frozen_status_accepts_qualitative_and_note() -> None:
    """v0.2: FROZEN can carry qualitative + note but no value."""
    m = Measurement(
        dimension_code="D4",
        status=MeasurementStatus.FROZEN,
        qualitative="frozen per RFC §8 R1",
        note="scoring frozen until B-F parity",
    )
    assert m.value is None
    assert not m.is_real


def test_measurement_not_measured_status_accepts_qualitative_and_note() -> None:
    """v0.2: NOT_MEASURED can carry qualitative + note but no value."""
    m = Measurement(
        dimension_code="D1",
        status=MeasurementStatus.NOT_MEASURED,
        qualitative="requires real Kafka cluster",
        note="capability documented; measurement pending real infra",
    )
    assert m.value is None
    assert not m.is_real
