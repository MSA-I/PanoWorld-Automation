from __future__ import annotations

import json

import pytest

from pwa.floorplan.cli import main


@pytest.mark.parametrize("fixture", ["f-usage-missing-arg"], ids=lambda fixture: fixture)
def test_usage_missing_parse_run_id_exits_2(fixture: str):
    with pytest.raises(SystemExit) as exc:
        main(["--runs-root", "runs", "--source-run", "runs/source"])

    assert exc.value.code == 2


def test_main_converts_unexpected_exception_to_cli_2(monkeypatch):
    """Defense-in-depth guard (M-2/M-3, code review 2026-08-10): parse_run()
    is expected to catch every reachable failure itself, but if some
    genuinely unforeseen exception still escapes it, cli.main() must not let
    a raw traceback reach the user -- it must return the documented
    operational exit code 2 instead.
    """

    def boom(**kwargs):
        raise RuntimeError("unexpected failure inside parse_run")

    monkeypatch.setattr("pwa.floorplan.cli.parse_run", boom)

    exit_code = main(["--runs-root", "runs", "--source-run", "runs/source", "--parse-run-id", "RUN-x"])

    assert exit_code == 2


def test_main_surfaces_finalized_directory_left_behind_diagnostic(monkeypatch, capsys):
    diagnostic = {
        "report_version": 1,
        "parse_run_id": "RUN-x",
        "outcome": "operational_failure",
        "cli_exit": 2,
        "residual_state": "finalized_directory_left_behind",
    }

    class Result:
        cli_exit = 2

        def __init__(self):
            self.diagnostic = diagnostic

    monkeypatch.setattr("pwa.floorplan.cli.parse_run", lambda **kwargs: Result())

    exit_code = main(["--runs-root", "runs", "--source-run", "runs/source", "--parse-run-id", "RUN-x"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert json.loads(captured.err) == diagnostic
