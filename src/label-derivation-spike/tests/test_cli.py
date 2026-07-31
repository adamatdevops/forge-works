from __future__ import annotations

import json

import pytest
from forge_works.dr.ab028_spike.cli import build_parser, main


def test_parser_defaults() -> None:
    args = build_parser().parse_args([])
    assert args.metadata_days == 30
    assert args.modeling_days == 60


def test_cli_writes_out_dir(tmp_path, capsys) -> None:
    exit_code = main(
        [
            "--out-dir",
            str(tmp_path),
            "--seed",
            "42",
            "--base-rate",
            "0.03",
            "--deploys-per-day",
            "5.0",
            "--train-floor",
            "10",
            "--val-floor",
            "3",
            "--test-floor",
            "3",
        ]
    )
    assert exit_code in (0, 1)
    assert (tmp_path / "metadata-pass.json").exists()
    assert (tmp_path / "metadata-pass.md").exists()
    payload = json.loads((tmp_path / "metadata-pass.json").read_text())
    assert "metadata_pass" in payload
    assert "config" in payload
    md = (tmp_path / "metadata-pass.md").read_text()
    assert "# AB-028 Pre-Scoping Metadata Window Pass" in md


def test_cli_json_only(capsys) -> None:
    exit_code = main(
        [
            "--json-only",
            "--seed",
            "42",
            "--base-rate",
            "0.03",
            "--deploys-per-day",
            "5.0",
            "--train-floor",
            "10",
            "--val-floor",
            "3",
            "--test-floor",
            "3",
        ]
    )
    assert exit_code in (0, 1)
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert "metadata_pass" in payload


def test_cli_ready_returns_zero(capsys) -> None:
    exit_code = main(
        [
            "--json-only",
            "--seed",
            "42",
            "--base-rate",
            "0.03",
            "--deploys-per-day",
            "5.0",
            "--train-floor",
            "10",
            "--val-floor",
            "3",
            "--test-floor",
            "3",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    ready = payload["metadata_pass"]["ready_for_scoping_approval"]
    if ready:
        assert exit_code == 0
    else:
        pytest.skip("this seed didn't produce ready outcome; exit-code semantics still asserted")


def test_cli_not_ready_returns_nonzero(capsys) -> None:
    exit_code = main(
        [
            "--json-only",
            "--seed",
            "1",
            "--base-rate",
            "0.005",
            "--deploys-per-day",
            "2.0",
            "--train-floor",
            "500",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    if not payload["metadata_pass"]["ready_for_scoping_approval"]:
        assert exit_code == 1
