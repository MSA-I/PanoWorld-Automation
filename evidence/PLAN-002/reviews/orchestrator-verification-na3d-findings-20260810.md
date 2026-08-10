# Orchestrator verification of the NA-3d review findings (PLAN-002)

Subject: branch `panoworld-dev/na-3b-gc3-fixes`, commit `6eaef17`.
Reviewed document: `evidence/PLAN-002/reviews/independent-anthropic-rework3-review-20260810.md`
(Anthropic reviewer, round 4, `VERDICT: ACCEPT` with 2 MINOR and 2 INFO findings).
Date: 2026-08-10. Author: orchestrator (Claude Opus 5, this session).

This document does three things, in this order: it checks the reviewer's four findings against the
code, it reports the Windows experiment the reviewer explicitly asked the orchestrator to run
(F4), and it records two defects that experiment uncovered which no reviewer in four rounds has
reported. Nothing here edits or re-opens the reviewer's document; that record stands as written.

Paths are repository-relative per section 12. The experiment scripts and their raw output live in
the session scratchpad, outside the repository, and are referred to as `<scratch>/...`; their
substance is reproduced inline below so this record is self-contained.

---

## 1. F1 - byte-limit gate is enforced on a pre-staging `stat()`, not on the copied bytes

Reviewer's claim: the DXF size gate at `src/pwa/floorplan/builder.py:742-753` stats the source
file, but the bytes are not read until `copy_source_inventory` at `:780`, so the limit does not
bind what is actually copied.

**CONFIRMED, with the impact narrower than an unbounded write.**

- `src/pwa/floorplan/builder.py:742` takes `source_floorplan.stat().st_size` and `:753` compares it
  to `MAX_DXF_BYTES`. Both happen *before* `:766` creates the staging directory.
- `src/pwa/floorplan/runs.py:181-194` (`copy_source_inventory`) then calls
  `copy_immutable(source_item, destination_item)` at `:185`.
- `src/pwa/files.py:27-42` (`copy_immutable`) streams the whole file in 1 MiB chunks with **no size
  cap of any kind**. There is no second `st_size` check anywhere on that path.

So a source file that measures under the limit at `:742` and is grown before `:780` is copied in
full, unbounded. What stops it from being *accepted* is GC-3's hash re-verification: the copied
digest is compared to the immutable declared hash at `runs.py:189`, and a grown file cannot match,
so the run fails with `PARSE_SOURCE_HASH_MISMATCH`. The residue is therefore disk consumption and
wall-clock inside the staging directory, not accepted oversized input. MINOR is the right severity.
The fix is one line: pass the cap into `copy_immutable` (or re-`stat` the opened handle) and abort
mid-stream past `MAX_DXF_BYTES`.

## 2. F2 - a post-rename verification failure publishes a failed run and drops its report

Reviewer's claim: `src/pwa/floorplan/runs.py:213-223` verifies the inventory a second time *after*
`os.replace`, and if that verification fails the diagnostic report is lost via
`src/pwa/floorplan/builder.py:431-454`.

**CONFIRMED, and the consequence is worse than a lost report.**

The exact sequence:

1. `runs.py:220` `verify_run_inventory(staging_run, manifest)` - passes.
2. `runs.py:221` `os.replace(staging_run, final_run)` - the run is now **published** at its final
   path; `staging_run` no longer exists.
3. `runs.py:222` `verify_run_inventory(final_run, manifest)` raises
   `ValueError("finalized inventory hash mismatch")`.
4. That `ValueError` is caught by the broad handler at `builder.py:1070-1077` and routed to
   `_staged_operational_result`.
5. `builder.py:450` guards the report write with `if staging_run.is_dir()`. It is not a directory
   any more, so the write is skipped; `:452-453` swallows anything else with `except ... pass`.

Net state on disk: a complete, normally-named run directory sitting in `runs_root` next to
successful runs, containing manifests, parse artifacts, overlay and a `parse-report.json` that
describes a *successful* parse, with nothing anywhere on disk recording that finalization failed.
The only signal is the in-memory `cli_exit=2` and the returned diagnostic, which vanish when the
process exits. Anything that later enumerates `runs_root` and trusts directory presence - which is
precisely what a "derived run" is supposed to mean - consumes a run whose bytes failed
verification.

Likelihood is low: reaching step 3 needs a byte-level race between the two verifications or a
transient I/O error, since `os.replace` on the same volume does not alter contents. Consequence is
high. The fix is small and belongs in `finalize_run`: on post-rename failure, either rename back to
staging before propagating, or write the operational report into `final_run` and mark it. Do not
leave the caller guessing which side of the rename it is on - `_staged_operational_result` cannot
tell today.

## 3. F3 - annotation bytes are read before the byte limit is applied (pre-existing)

Reviewer's claim: `src/pwa/floorplan/builder.py:684` does `Path(annotation).read_bytes()` and the
`MAX_ANNOTATION_BYTES` check only happens afterwards; and this pre-dates the rework.

**CONFIRMED.** `:684` reads the entire annotation file into memory; `:695` is where
`len(annotation_bytes) > MAX_ANNOTATION_BYTES` is finally tested. The limit therefore bounds what is
*processed*, never what is *read*, so annotation memory use is bounded only by the file size an
operator can place in the run. The reviewer's provenance claim also holds: this ordering is present
in `11ef553`, the pre-rework parent, so the rework neither introduced nor worsened it. INFO is
right; it is a pre-existing item for the AC-18 resource-limit discussion, not a rework defect.

## 4. F4 - the Windows aliasing experiment the reviewer asked for: NEGATIVE for both mechanisms

The reviewer could not test its own hypothesis and named the commands for the orchestrator: whether
a trailing dot, an NTFS 8.3 short-name alias, or an alternate data stream can make a path component
that *lexically* differs from an already-checked ancestor resolve to that ancestor anyway, thereby
slipping past the lexical containment walk in `src/pwa/floorplan/runs.py:12-74`.

Run on this Windows 10 host (NTFS, `py` 3.14.5), scripts `<scratch>/f4_experiment.py` and
`<scratch>/f4_poc_helpers.py`, raw output in `<scratch>/f4-results.txt` and
`<scratch>/f4-poc-results.txt`. A junction `junc` was created pointing outside the lab directory,
and every alias form was stat'ed through `pwa.files.is_link_or_reparse`.

| accessed as | `exists()` | reparse detected | `st_ino` / `st_dev` |
|---|---|---|---|
| `junc` (true name) | True | **True** | identical |
| `junc.` (trailing dot) | True | **True** | identical |
| `junc ` (trailing space) | True | **True** | identical |
| `junc..` (two trailing dots) | True | **True** | identical |
| `JUNC` (case-folded) | True | **True** | identical |

For 8.3: `dir /x` produced `AVERYL~1` for `averylongdirectoryname_xyz`; the long and short names
reported identical `st_ino` and `st_dev`, `os.path.samefile` returned True, and `Path(alias).resolve()`
normalized back to the long name.

**Conclusion: neither mechanism defeats the check.** Windows normalizes the alias before the stat,
so `lstat` reports the reparse attribute through every alias form, and `resolve()` collapses 8.3
aliases to the canonical name before the `relative_to` containment test. The residual risk the
reviewer flagged on GC3-1 for these two mechanisms is closed by measurement, not by argument.

One cosmetic side effect worth knowing: `Path("newdir.").mkdir()` succeeds and creates `newdir` on
disk, so a declared path with a trailing dot names a file whose on-disk name differs from the
manifest string. It is harmless for containment and for hashing (both sides resolve to the same
object), but it means a manifest can describe a name that no directory listing will show.

---

## 5. Two defects the experiment uncovered, reported by no reviewer in four rounds

Testing F4 required calling the real containment helpers rather than reasoning about them, and that
is what surfaced these. Both are in the same helper family as the CRITICAL gate GC3-1.

### O-NA3D-1 (MAJOR, latent): a drive-relative component defeats the write-side containment walk

`src/pwa/floorplan/runs.py:12-17` (`_contained_parts`) rejects a component equal to `""`, `"."` or
`".."`, and rejects absolute paths. It does **not** reject a component that carries a Windows drive
letter, because a drive-relative path such as `C:sub` is not absolute:

```
_contained_parts("C:pwa_escape")        -> ('C:', 'pwa_escape')        # accepted
PureWindowsPath("D:/runs") / "C:"       -> PureWindowsPath("C:")       # root discarded
PureWindowsPath("D:/runs") / "D:foo"    -> PureWindowsPath("D:/runs/foo")   # same drive, harmless
```

The escape needs a drive letter *different* from the root's, because `pathlib` only discards the
left-hand path when the drives differ. That is exactly the situation in production: `runs_root`
lives on the project drive, so a declared path naming any other drive letter drops it.

Proven end to end, with the containment root on one drive letter and the injected component naming
another, both mapped inside the scratchpad so the escape landed somewhere harmless
(`<scratch>/f4_poc_drive.py` and `.ps1`, output `<scratch>/f4-poc-drive-results.txt`). Verbatim,
with the drive-relative value `C:pwa_escape/owned.txt` and root `X:/f4lab3`:

```
1 _contained_parts                 -> ('C:', 'pwa_escape', 'owned.txt')
2 Path(root) / 'C:'                -> 'C:'                      <- root discarded
3 validate_contained_destination   -> ACCEPTED, leaf = C:pwa_escape\owned.txt
  leaf under root?                 -> False
4 resolve_contained_output         -> ACCEPTED, write target = C:pwa_escape\owned.txt
5 write_bytes_contained            -> WROTE, bytes b'ESCAPED-THE-RUN-DIRECTORY'
   root contents after             -> []
   escaped file exists outside root-> True
6 resolve_contained_relpath        -> ValueError: path escapes containment root   <- read side is safe
7 create_contained_directory       -> CREATED a directory outside the root
```

So four of the five write-side helpers - `validate_contained_destination`,
`create_contained_directory`, `resolve_contained_output`, `write_bytes_contained` - accept the value
and write outside the root. The read-side helper `resolve_contained_relpath` refuses it, and the
reason is instructive: it is the only one of the family that ends with an independent
`resolved.relative_to(root_resolved)` check (`runs.py:168-177`). The write side has the lexical walk
and nothing else.

**Is it live today?** No - and only because of call ordering, not because of the helper. The single
write-side call reached by attacker-controlled data is `runs.py:184`
(`resolve_contained_output(staging_run, item["path"])`), and `runs.py:183` passes the same string
through the read-side helper first, which rejects it; `builder.py:647` pre-validates every declared
inventory path the same way before staging even exists. Every other write-side call site uses a
literal or the grammar-validated `parse_run_id`.

That makes this a latent instance of the exact defect class that produced the GC-1 CRITICAL in the
previous round - a path helper that trusts a component `pathlib` will interpret as a new anchor -
surviving in the write-side family, held off by an ordering invariant that no test asserts and no
comment names. It is one refactor away from being live. It should be fixed in this plan, not
deferred: reject any component containing `:` in `_contained_parts`, and give
`validate_contained_destination` the same closing `resolve()`/`relative_to` check its read-side
sibling already has. Two edits, both inside `runs.py`, plus a failure-matrix test per mechanism.

### O-NA3D-2 (MINOR): an alternate-data-stream component hides bytes inside a finalized artifact

`name:stream` is a single `pathlib` component (the colon is not at offset 1, so it is not parsed as
a drive), so `_contained_parts` accepts it and both the read and write helpers treat it as an
ordinary leaf inside the root. Windows then resolves it as a stream on the host file. Verbatim from
`<scratch>/f4-poc-results.txt`, against an existing 16-byte `artifact.dxf`:

```
F1 _contained_parts('artifact.dxf:evil') -> ('artifact.dxf:evil',)
F2 resolve_contained_output              -> ACCEPTED
F3 write_bytes_contained                 -> WROTE stream
   host main-stream bytes unchanged      -> b'ORIGINAL-PAYLOAD'
   host size still 16 (was 16)
   os.listdir(root)                      -> ['artifact.dxf']      <- stream invisible
   stream readable                       -> b'HIDDEN-BYTES'
F4 sha256(host) unchanged by the stream   -> True
```

There is **no containment escape** here - the bytes stay inside the run directory - so this is not a
GC3-1 issue. What it breaks is the auditability the run directory is supposed to provide: bytes can
be attached to an already-written artifact without changing that artifact's size, its `sha256`, or
any directory listing, which means `verify_run_inventory`, an inventory walk, and a human reviewer
all see an unchanged run. Same one-line fix as above (reject `:` in a component) closes it, which is
why the two are reported together.

---

## 6. What I am not claiming

- I have not re-run the full test suite for this document; nothing here changed code.
- O-NA3D-1's non-reachability is established by reading every call site of the five write-side
  helpers in `src/` (the grep is exhaustive: `builder.py:519,520,766,767,768,781,782,787` and
  `runs.py:184,197-198,217`). It is not established by a test, and that is part of the finding.
- Severities are mine. F2 in particular I rate above the reviewer's MINOR on consequence while
  agreeing with it on likelihood; the reviewer had no diff access, which is an orchestrator error
  recorded in the review's own header.
- The Opus 5 pass queued after the rate-limit window is still outstanding at the time of writing
  and receives the diff pre-materialised. If it disagrees with anything here, both records stand.

---

## 7. Addendum, appended after the Opus 5 pass returned (2026-08-10, later the same evening)

The queued Opus 5 pass ran with the diff pre-materialised and no Bash tool, and returned
`VERDICT: NEEDS_REWORK` - archived as
`evidence/PLAN-002/reviews/independent-anthropic-rework3-review-opus-20260810.md`. It had no access
to the document you are reading; it was written after that reviewer's brief and is not referenced in
its prompt. It nevertheless reported both of the defects in section 5 from code alone:

- its **F-3** is **O-NA3D-1** (drive-relative component defeats the write-side walk), with the same
  root cause, the same four affected helpers, the same reachability analysis, and the same two-line
  fix;
- its **F-7** is **O-NA3D-2** (ADS component), with the same conclusion that it is contained but
  smuggles bytes past every listing and hash;
- its **F-1** is the same defect this document raised as a severity upgrade over the earlier pass's
  F2, and it also rates it MAJOR.

Two independent routes reached the same three conclusions. The stronger reading is not that the
findings are confirmed twice but that four rounds of review had missed them, and only the round with
both a proof-of-concept and full diff access caught them.

### Verifications the Opus reviewer asked the orchestrator to run

It had no shell and listed twelve `CANNOT_VERIFY` items, each with the command it would have run.
Results, all executed on the working tree at `6eaef17`:

| Its item | Command | Result |
|---|---|---|
| 1 - suite | `python -m pytest -q` | **338 passed, exit 0** in 60 s, one pre-existing Pillow `getdata` deprecation warning. Matches the implementer's claim. |
| 2 - golden hash | included in the suite run | `tests/golden/test_floorplan_golden.py` pins `sha256:e5041ddc...b7e77e` and passed. |
| 3 - tree equals commit | `git diff --stat 6eaef17 -- src tests` | **empty.** The working tree it read is byte-identical to the reviewed commit for `src/` and `tests/`. |
| 4 - dependencies and contracts untouched | `git diff --stat 11ef553 6eaef17 -- pyproject.toml uv.lock schemas contracts docs` | **empty.** |
| 5 - F-1 | its own probe, run outside the repository | **F-1 CONFIRMED.** Output below. |
| 6 - F-3 | `write_bytes_contained` with a drive-relative component | Already run before its pass; see section 5. Its predicted outcome matched the measured one exactly. |
| 7 - F-7 | `write_bytes_contained` with `name:stream` | Already run; see section 5. Predicted outcome matched. |

The F-1 probe reused the repository test's own fixtures from an out-of-tree file
(`<scratch>/test_f1_probe.py`) so nothing in the repository was modified, and added the two
assertions the reviewer named. Verbatim:

```
cli_exit                      = 2
diagnostic.outcome            = operational_failure
final_run.exists()            = True
staging_run.exists()          = False
finalized run file count      = 15
    parse/annotation.json, parse/assumptions.json, parse/floorplan_parse.json,
    parse/overlay.svg, parse/parse-report.json, project/input_quality_report.json,
    project/inputs/originals/floorplan.png, project/inputs/originals/style_reference.png,
    project/project_manifest.json, project/source-manifest.json,
    project/source-quality-report.json
on-disk parse-report.outcome  = 'complete'
on-disk parse-report.cli_exit = 0
```

So on a post-rename inventory hash drift the caller is told CLI 2 while a complete, normally-named
run sits in `runs_root` whose own report claims `complete` / `0`, and staging - the thing an
operational failure is supposed to retain for diagnosis - is gone. This is the strongest evidence
produced in this round, and it is the reviewer's stated basis for `NEEDS_REWORK`.

Items 8 through 12 remain unverified and are recorded as such: F-2's exploitable interleaving needs
a race harness this round does not have, F-9 needs a second `ezdxf` version, and AC-13/AC-14's
remaining clauses need artifacts a read-only pass cannot generate.

### Where the two Anthropic passes disagree, and which one governs

The earlier pass said ACCEPT; this one says NEEDS_REWORK. The disagreement is not a matter of
judgment applied to the same evidence - the earlier pass never saw the diff, did not read
`src/pwa/files.py`, the failure-matrix test or the two unit test files, and had no shell, all of
which is recorded in its own archived header. The later pass had the full change set, read the
files the earlier one skipped, and its central finding is now reproduced by an executed probe. On
the evidence, **NEEDS_REWORK governs this round.** Neither document has been edited.
