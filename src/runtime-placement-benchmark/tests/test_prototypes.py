from __future__ import annotations

from forge_works.dr.ab029_spike.dimensions import DIMENSIONS, MeasurementStatus
from forge_works.dr.ab029_spike.prototypes import (
    ALL_STUB_PROTOTYPES,
    BatchMaterializedStub,
    DedicatedInferenceStub,
    InsightGeneratorExtensionStub,
    PatternMatcherExtensionStub,
    PlacementPrototype,
    SiblingFlinkStub,
    measure_all,
)


def test_five_stubs_cover_options_a_through_e() -> None:
    codes = {p.option_code for p in ALL_STUB_PROTOTYPES}
    assert codes == {"A", "B", "C", "D", "E"}


def test_each_stub_satisfies_protocol() -> None:
    for p in ALL_STUB_PROTOTYPES:
        assert isinstance(p, PlacementPrototype)


def test_measure_all_returns_every_dimension() -> None:
    p = SiblingFlinkStub()
    ms = measure_all(p)
    assert set(ms.keys()) == {d.code for d in DIMENSIONS}


def test_stubs_report_not_implemented() -> None:
    for p in ALL_STUB_PROTOTYPES:
        for d in DIMENSIONS:
            m = p.measure(d.code)
            assert m.status is MeasurementStatus.NOT_IMPLEMENTED


def test_batch_contract_implications_include_staleness() -> None:
    p = BatchMaterializedStub()
    impls = p.contract_implications()
    assert any("staleness" in impl.lower() for impl in impls)


def test_pattern_matcher_notes_shared_failure_domain() -> None:
    assert any(
        "failure domain" in i.lower() for i in PatternMatcherExtensionStub().contract_implications()
    )


def test_insight_generator_notes_scaling_profile() -> None:
    impls = InsightGeneratorExtensionStub().contract_implications()
    assert any("scaling" in i.lower() or "bursty" in i.lower() for i in impls)


def test_dedicated_inference_notes_new_service() -> None:
    impls = DedicatedInferenceStub().contract_implications()
    assert any("service" in i.lower() for i in impls)
