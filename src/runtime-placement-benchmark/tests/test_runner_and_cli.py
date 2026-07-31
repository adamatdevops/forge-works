from __future__ import annotations

import json

import pytest
from forge_works.dr.ab029_spike.cli import build_parser, load_inputs, main
from forge_works.dr.ab029_spike.dimensions import DIMENSIONS
from forge_works.dr.ab029_spike.runner import (
    BenchmarkRunner,
    OptionInput,
    scoping_approval_placeholder_inputs,
)


def test_placeholder_inputs_cover_all_options() -> None:
    inputs = scoping_approval_placeholder_inputs()
    codes = {i.option_code for i in inputs}
    assert codes == {"A", "B", "C", "D", "E"}
    for i in inputs:
        for d in DIMENSIONS:
            assert i.scores[d.code] == 3


def test_runner_produces_matrix_and_decision() -> None:
    r = BenchmarkRunner()
    m, d = r.run(scoping_approval_placeholder_inputs())
    assert len(m.options) == 5
    assert d.primary is not None


def test_runner_rejects_missing_input() -> None:
    r = BenchmarkRunner()
    partial = [i for i in scoping_approval_placeholder_inputs() if i.option_code != "D"]
    with pytest.raises(ValueError, match="missing OptionInput"):
        r.run(partial)


def test_cli_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.scores is None
    assert args.out_dir is None
    assert not args.json_only


def test_cli_writes_out_dir(tmp_path) -> None:
    exit_code = main(["--out-dir", str(tmp_path)])
    assert (tmp_path / "matrix.json").exists()
    assert (tmp_path / "matrix.md").exists()
    payload = json.loads((tmp_path / "matrix.json").read_text())
    assert len(payload["options"]) == 5
    assert exit_code in (0, 1)


def test_cli_json_only(capsys) -> None:
    main(["--json-only"])
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert len(payload["options"]) == 5


def test_load_inputs_accepts_scores_json(tmp_path) -> None:
    path = tmp_path / "scores.json"
    scores = {d.code: 4 for d in DIMENSIONS}
    payload = {
        "A": {"scores": scores},
        "B": {"scores": scores, "contract_breaking_flags": ["some flag"]},
        "C": {"scores": scores},
        "D": {"scores": scores},
        "E": {"scores": scores},
    }
    path.write_text(json.dumps(payload))
    inputs = load_inputs(path)
    by_code = {i.option_code: i for i in inputs}
    assert by_code["B"].contract_breaking_flags == ["some flag"]
    assert by_code["A"].scores["D3"] == 4


def test_load_inputs_flat_scores_shape(tmp_path) -> None:
    path = tmp_path / "scores.json"
    scores = {d.code: 4 for d in DIMENSIONS}
    payload = dict.fromkeys(("A", "B", "C", "D", "E"), scores)
    path.write_text(json.dumps(payload))
    inputs = load_inputs(path)
    assert {i.option_code for i in inputs} == {"A", "B", "C", "D", "E"}


def test_cli_ready_exit_semantics_when_all_disqualified(tmp_path) -> None:
    path = tmp_path / "scores.json"
    all_ones = {d.code: 1 for d in DIMENSIONS}
    payload = dict.fromkeys(("A", "B", "C", "D", "E"), all_ones)
    path.write_text(json.dumps(payload))
    exit_code = main(["--json-only", "--scores", str(path)])
    assert exit_code == 1


def test_option_input_defaults() -> None:
    scores = {d.code: 3 for d in DIMENSIONS}
    oi = OptionInput(option_code="X", scores=scores)
    assert oi.contract_breaking_flags == []
    assert oi.rationale_per_dimension == {}
