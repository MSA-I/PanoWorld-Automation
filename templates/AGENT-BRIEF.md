# AGENT BRIEF

## Identity
- Agent name:
- Role:
- PLAN_ID:
- Iteration:

## Model routing
- PROVIDER:
- MODEL:
- MODEL_ID_EXACT:
- EFFORT_NORMALIZED:
- EFFORT_PROVIDER_VALUE:
- THINKING:
- MODEL_REASON:
- FALLBACK_PROVIDER:
- FALLBACK_MODEL:
- ESCALATE_WHEN:
- TOKEN_BUDGET:
- MAX_RUNTIME:
- CROSS_PROVIDER_REVIEWER:

## Goal
משפט אחד מדיד.

## Context to read
- exact paths בלבד.

## Ownership
### May modify
- paths

### Read only
- paths

### Forbidden
- paths/actions

## Inputs
- artifact + schema version + hash.

## Required outputs
- exact artifact paths.

## Acceptance criteria
- [ ] criterion עם בדיקה.

## Tests and gates
- exact commands.
- expected result.

## Non-goals
- רשימה מפורשת.

## Blocker policy
אל תנחש ואל תשנה מחוץ לבעלות. כתוב BLOCKER לפי התבנית ושלח למתזמר. המשך עבודה עצמאית שאינה תלויה בחסם.

## Reporting format
```text
PLAN_ID:
STATUS:
PROVIDER:
MODEL_ID_EXACT:
EFFORT:
OWNERSHIP:
COMPLETED:
EVIDENCE:
FILES_CHANGED:
TESTS_RUN:
TEST_RESULT:
BLOCKERS:
RISKS:
NEXT_ACTION:
COMMIT:
```
