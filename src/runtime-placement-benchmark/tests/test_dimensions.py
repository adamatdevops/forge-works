from __future__ import annotations

import pytest
from forge_works.dr.ab029_spike.dimensions import (
    DEFAULT_WEIGHTS,
    DIMENSIONS,
    Measurement,
    MeasurementStatus,
    dimension_by_code,
)


def test_seven_dimensions_present() -> None:
    codes = {d.code for d in DIMENSIONS}
    assert codes == {"D1", "D2", "D3", "D4", "D5", "D6", "D7"}


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
