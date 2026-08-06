# Invalid evidence run

This run is retained to preserve history, but it is **not acceptance evidence**.
The pytest subprocess exited 0; however, `tools/run_checks.py` decoded captured output
as strict UTF-8 and its reader thread raised `UnicodeDecodeError`. Commit `PLAN-001`
changes capture to `errors="replace"`. Use the later `RUN-20260806-051819-816232` run.
