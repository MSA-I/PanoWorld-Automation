# WP0 Anthropic Opus spatial-design brief

- PLAN: PLAN-002RF
- Work package: WP0 only
- Requested provider/model: Anthropic first-party Claude Code / `opus` / exact runtime model must be reported
- Requested effort: MAX (`--effort max`)
- Permission mode: plan/read-only
- Fallback: none
- Product execution boundary: local Windows CPU-only; no GPU/H200/cloud/remote product execution, no dependency installation, no network corpus acquisition, no spend, no G7/G8, no PLAN-003, no Product A/B activation.

You are the critical CV/spatial architect for PLAN-002RF WP0. Work read-only. First use Claude Code's `/skills` mechanism to find and apply relevant geometry/computer-vision/evaluation/threat-modeling skills; report exactly which skills were found/applied or that none were available. Do not edit files, install dependencies, acquire data, invoke network retrieval, run the raster fixture, or start implementation.

Read these repository artifacts:
- external approved packet: `D:/משה פרוייקטים/פיתוח אתרים/PanoWorld-Automation/.hermes/plans/2026-08-11_220700-plan-002rf-final-remediation-approval-packet.md` (approved SHA-256 `95c4cfd8711d4c2335d9905285b977118ba89cff440aa90c1a9cb5aab74422f7`)
- `docs/02-היתכנות-על-המחשב-הנוכחי-ולוחות-זמנים.md`
- `docs/06-מדיניות-ניתוב-מודלים-ומאמץ.md`
- `samples/README.md`
- `evidence/PLAN-002/visual-gate/na4-na5-record-20260811.md`
- `pyproject.toml` and `uv.lock`

Produce a rigorous design memo for the hardest-clean-raster CPU-only feasibility gate using only already-locked Pillow/NumPy and the existing rights-cleared public-domain sample. The sample lacks authoritative scale anchors and prior manual geometry is explicitly not accuracy truth, so distinguish what can be validly measured now from what must fail closed. Define deterministic stages, algorithm/config parameters, exact metrics, memory/runtime instrumentation, replay/determinism proof, adversarial/refusal checks, thresholds, and a STOP/GO/PARTIAL decision rule. Recommend exact resolutions for U-1 through U-15 only where WP0 evidence can support them; mark every unsupported item BLOCKED and name the missing evidence/owner. Do not weaken the approved AT thresholds, invent labels, treat previous annotations as independent truth, or substitute manual operation.

Your output must include: requested and actual provider/model evidence available to you; session ID if available; skills; assumptions; protocol; threshold table; U-1..U-15 recommendation table; security/resource risks; and explicit boundary audit. State clearly whether this single existing sample can prove Product B feasibility (expected answer should follow evidence, not optimism).