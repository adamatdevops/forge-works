from __future__ import annotations

import pytest
from forge_works.dr.ab029_spike.dimensions import DIMENSIONS, MeasurementStatus
from forge_works.dr.ab029_spike.prototypes import (
    ALL_STUB_PROTOTYPES,
    RFC_GATES,
    BatchMaterializedStub,
    DedicatedInferenceStub,
    GateStatus,
    InsightGeneratorExtensionStub,
    PatternMatcherExtensionStub,
    PlacementPrototype,
    SiblingFlinkPrototype,
    SiblingFlinkStub,
    StandalonePythonKafkaConsumerStub,
    evaluate_gates,
    measure_all,
)


def test_six_stubs_cover_options_a_through_f() -> None:
    """v0.2: registry expanded to 6 options per RFC §3.6 (added Option F)."""
    codes = {p.option_code for p in ALL_STUB_PROTOTYPES}
    assert codes == {"A", "B", "C", "D", "E", "F"}


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


def test_batch_contract_implications_include_staleness_or_freshness() -> None:
    """v0.2: memo v0.1 said staleness field required; v0.2 clarified PC §3.3 already covers it."""
    p = BatchMaterializedStub()
    impls = p.contract_implications()
    assert any("freshness" in impl.lower() or "staleness" in impl.lower() for impl in impls)


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


def test_standalone_python_kafka_notes_manual_semantics() -> None:
    """v0.2 NEW: Option F consumer-group management, backpressure, state, exactly-once are manual."""
    impls = StandalonePythonKafkaConsumerStub().contract_implications()
    blob = " ".join(impls).lower()
    assert "manual" in blob or "redis" in blob


# --- SiblingFlinkPrototype (real-scaffold Option A prototype — v0.2 freeze applies) ---


def test_sibling_flink_prototype_satisfies_protocol() -> None:
    assert isinstance(SiblingFlinkPrototype(), PlacementPrototype)


def test_sibling_flink_prototype_option_code_is_a() -> None:
    assert SiblingFlinkPrototype().option_code == "A"


def test_sibling_flink_prototype_contract_implications_mention_topic_and_placeholder() -> None:
    impls = SiblingFlinkPrototype().contract_implications()
    blob = " ".join(impls).lower()
    assert "topic" in blob
    assert "placeholder" in blob
    assert "estimand" in blob


def test_sibling_flink_prototype_contract_implications_mention_v0_2_deferrals() -> None:
    """v0.2 NEW: Codex Loop #4 deferred findings must be surfaced in contract implications."""
    impls = SiblingFlinkPrototype().contract_implications()
    blob = " ".join(impls).lower()
    assert "deferred" in blob or "codex loop" in blob


def test_sibling_flink_prototype_d1_is_not_measured() -> None:
    """v0.2: v0.1 returned OK-with-caveats; v0.2 returns NOT_MEASURED per RFC §6.2.1."""
    m = SiblingFlinkPrototype().measure("D1")
    assert m.status is MeasurementStatus.NOT_MEASURED
    assert m.value is None
    assert "unmeasured" in m.qualitative.lower() or "not_measured" in m.qualitative.lower()


def test_sibling_flink_prototype_d3_is_not_measured() -> None:
    """v0.2: v0.1 returned OK with invented ~30s+15s numbers; v0.2 returns NOT_MEASURED."""
    m = SiblingFlinkPrototype().measure("D3")
    assert m.status is MeasurementStatus.NOT_MEASURED
    assert m.value is None


def test_sibling_flink_prototype_d4_is_frozen() -> None:
    """v0.2: v0.1 asserted static D4=5.0; v0.2 freezes per RFC §8 R1."""
    m = SiblingFlinkPrototype().measure("D4")
    assert m.status is MeasurementStatus.FROZEN
    assert m.value is None
    assert "rescinded" in m.note.lower() or "frozen" in m.note.lower()


def test_sibling_flink_prototype_d7_is_frozen() -> None:
    """v0.2: v0.1 asserted static D7=5.0; v0.2 freezes per RFC §8 R1."""
    m = SiblingFlinkPrototype().measure("D7")
    assert m.status is MeasurementStatus.FROZEN
    assert m.value is None
    assert "rescinded" in m.note.lower() or "frozen" in m.note.lower()


def test_sibling_flink_prototype_d8_is_not_applicable_with_dual_reason() -> None:
    """v0.2 NEW: D8 has both methodology gap AND §8 R1 freeze."""
    m = SiblingFlinkPrototype().measure("D8")
    assert m.status is MeasurementStatus.NOT_APPLICABLE
    blob = m.note.lower()
    assert "methodology" in blob or "§8 r1" in blob or "sub-check" in blob


def test_sibling_flink_prototype_d2_d5_d6_not_applicable() -> None:
    proto = SiblingFlinkPrototype()
    for code in ("D2", "D5", "D6"):
        m = proto.measure(code)
        assert m.status is MeasurementStatus.NOT_APPLICABLE, code
        assert m.note, code


def test_sibling_flink_prototype_unknown_dimension_raises() -> None:
    with pytest.raises(ValueError, match="unknown dimension code"):
        SiblingFlinkPrototype().measure("D99")


def test_sibling_flink_prototype_measure_all_shape() -> None:
    """v0.2: dimension count 7→8 (added D8); D1/D3 now NOT_MEASURED; D4/D7 now FROZEN."""
    ms = measure_all(SiblingFlinkPrototype())
    assert set(ms.keys()) == {d.code for d in DIMENSIONS}
    frozen_codes = {c for c, m in ms.items() if m.status is MeasurementStatus.FROZEN}
    not_measured_codes = {c for c, m in ms.items() if m.status is MeasurementStatus.NOT_MEASURED}
    na_codes = {c for c, m in ms.items() if m.status is MeasurementStatus.NOT_APPLICABLE}
    assert frozen_codes == {"D4", "D7"}
    assert not_measured_codes == {"D1", "D3"}
    assert na_codes == {"D2", "D5", "D6", "D8"}


# --- evaluate_gates (v0.2 NEW per Codex Loop #4 H17) ---


def test_evaluate_gates_returns_all_ten_rfc_gates() -> None:
    """v0.2 NEW: RFC §6.3 defines G1-G10; gate-evaluation surface must cover them."""
    results = evaluate_gates(SiblingFlinkPrototype())
    assert set(results.keys()) == set(RFC_GATES)
    assert len(RFC_GATES) == 10


def test_evaluate_gates_scaffold_state_all_not_evaluated() -> None:
    """v0.2 NEW: for scaffold-state Option A + stub B-F, every gate is NOT_EVALUATED."""
    for proto in (SiblingFlinkPrototype(), *ALL_STUB_PROTOTYPES):
        results = evaluate_gates(proto)
        for gate, res in results.items():
            assert res.status is GateStatus.NOT_EVALUATED, f"{proto.option_code}:{gate}"
            assert res.evidence, f"{proto.option_code}:{gate} evidence missing"
