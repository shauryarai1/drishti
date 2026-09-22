## Next.js dev/build workflow (MANDATORY)

NEVER run `npm run build` while `npm run dev` is running in `frontend-next/`.
`next dev` and `next build` must never write the same `.next` directory at the
same time - doing so produces stale server chunks such as
`Error: Cannot find module './819.js'` from `.next/server/webpack-runtime.js`.

### Normal development verification (dev server stays up)
```powershell
npx tsc --noEmit                 # type check
# then exercise routes against the running dev server, e.g.
#   http://localhost:3000/ , /reading , /results , /life-summary , /panchang , /ask
```

### Production build verification (requires taking dev down briefly)
```powershell
# 1. stop next dev (kill only the frontend process on port 3000)
# 2. delete frontend-next/.next
# 3. npm run build          (from frontend-next/)
# 4. npx tsc --noEmit       (from frontend-next/)
# 5. delete frontend-next/.next
# 6. restart npm run dev
```
Steps 2, 5 and 6 are required: the build leaves production artefacts
(`BUILD_ID`, production manifests) that corrupt dev chunk resolution.

Never delete `node_modules`, `package-lock.json` or source files as part of this.
Do not upgrade Next.js to clear the "outdated version" notice.

# KAVACH — LOCKED BASELINE / CHANGE CONTROL

The existing KAVACH codebase is a STABLE, PRODUCTION BASELINE. The current
working product has been tested and approved. From this point onward, existing
functionality must be treated as FROZEN unless explicitly authorized.

## 1. Default rule: existing files are READ-ONLY

Treat ALL files that already exist in the repository at the start of a task as
READ-ONLY by default.

You MAY:
- inspect them
- search them
- trace imports/call paths
- run tests against them
- understand their APIs/interfaces
- use existing exported functions
- build new features around them

You MUST NOT (unless explicitly authorized):
- edit, refactor, rename, move or delete them
- reformat, "clean up", optimize, simplify or rewrite them
- change comments unnecessarily
- change behavior
- change dependencies merely for convenience

"Implement this feature" does NOT automatically mean permission to modify
unrelated existing files.

## 2. New features should be ADDITIVE

For future ideas/features, prefer creating NEW isolated files/modules/
components/endpoints rather than modifying stable code. Design new functionality
around existing interfaces.

    EXISTING STABLE SYSTEM
            ↓
    stable interface
            ↓
    NEW isolated module
            ↓
    new feature

Avoid invasive changes to working systems.

## 3. Minimum-change principle

If a new feature genuinely cannot be connected without editing an existing file:

STOP BEFORE EDITING IT. Report:

1. exact existing file that must change
2. why the change is unavoidable
3. exact lines/area that need modification
4. what behavior could be affected
5. smallest proposed change

Then wait for explicit approval. Do not silently make the integration change.

Exception: if the prompt explicitly names the existing file(s) you may modify,
you may modify only those authorized files and only as much as required.

## 4. Protected core systems

The following are especially frozen (do not alter unless the prompt explicitly
says to modify that system):

- Ask KAVACH routing
- Ask KAVACH context isolation
- personal-reading routing
- hidden Tarot/KAVACH reading mechanics
- Tarot draw logic
- astrology context generation
- Groq integration
- Gemini fallback
- provider order
- provider timeouts
- authentication
- Supabase history
- admin archive
- archive sanitization
- rate limiting
- production security controls
- Geoapify/location handling
- Kundli calculation engine
- Swiss Ephemeris calculations
- Lahiri ayanamsha
- BNN methodology
- Navtara methodology
- Mars methodology
- Dasha engine
- Daily Prediction
- Weekly Prediction
- Panchang
- Hora
- Life Summary
- retrograde handling
- timezone handling
- CORS
- production environment handling
- existing database migrations
- existing RLS/security policies

## 5. Astrology methodology is IMMUTABLE

Never "correct", replace, reinterpret, modernize, standardize or substitute the
project's astrology rules using your own astrology knowledge. The repository's
approved astrology methodology is authoritative for KAVACH.

Do not replace custom rules with generic Vedic astrology, Parashari rules,
Western astrology, internet-sourced astrology or model assumptions. If something
appears unusual, assume it is intentional unless explicitly asked to investigate.

## 6. Do not fix unrelated issues

While implementing a future feature you may notice old code, duplicate code,
lint issues, architecture you dislike, failing unrelated tests, possible
optimizations, naming inconsistencies, deprecated dependencies, TODOs or
potential refactors. DO NOT fix them automatically. Report them separately.

A task about Feature X must not become a refactor of Features A–W.

## 7. No drive-by refactoring

Never make changes solely because "this is cleaner", "this is more idiomatic",
"this architecture is better", "this reduces duplication", "this library would
be easier" or "this should be modernized". Production stability has priority
over code elegance.

## 8. Dependencies

Do not add, remove or upgrade dependencies unless required by the requested
feature. Before introducing a new dependency, prefer existing project
capabilities or a small dependency-free implementation. Do not perform framework
upgrades as part of unrelated work.

## 9. Database safety

Never modify existing production migrations. Never rewrite migration history.
For new database functionality, create a NEW migration.

Never weaken RLS, authentication, authorization, admin restrictions or
server-only secret handling. Never expose service-role/API secrets to frontend
code. Never delete production data unless explicitly instructed to do so.

## 10. Secrets

Never print, commit, expose or move secrets into client-side code. This includes
GROQ_API_KEY, GEMINI/API provider secrets, GEOAPIFY_API_KEY,
SUPABASE_SERVICE_ROLE_KEY and any future server secret.

Do not include actual secret values in logs, tests, commits, screenshots,
frontend bundles or reports.

## 11. Test isolation

Tests must never consume production AI quota or write to production services.
Mock external providers in automated tests. Tests must not call live Groq, call
live Gemini, write production Supabase rows, consume Geoapify quota
unnecessarily or mutate production data.

## 12. Git safety

Never use destructive Git commands such as `git reset --hard`, `git clean`,
`git checkout .` or `git restore .`. Do not discard unrelated user work. Do not
push unless explicitly asked to push. Commit locally when requested.

## 13. Before every task

1. Read this AGENTS.md.
2. Inspect git status.
3. Identify which files existed before the task.
4. Treat those files as frozen.
5. Determine whether the requested feature can be implemented additively.
6. Identify any existing files that would need modification.
7. If modification was not explicitly authorized, STOP and ask before touching them.

## 14. After every task

Before committing, run `git status --short`, `git diff --stat` and `git diff`.
Verify: only intended files changed; no frozen file changed without
authorization; no unrelated formatting changes; no secrets added; no production
methodology changed; no unrelated dependency changed; no production service used
by tests.

Run the smallest relevant test suite plus required type checks.

## 15. Completion report

At the end of every implementation report include:

NEW FILES: (list every newly created file)

EXISTING FILES MODIFIED: (list every pre-existing file modified and the explicit
authorization that allowed each modification)

PROTECTED SYSTEMS TOUCHED: (list them, or say NONE)

METHODOLOGY CHANGED: YES/NO (should normally be NO)

PROVIDER ARCHITECTURE CHANGED: YES/NO

DATABASE/SECURITY CHANGED: YES/NO

DEPENDENCIES CHANGED: YES/NO

TESTS: (exact commands, exact results)

GIT: (commit hash, pushed: YES/NO)

## 16. Conflict rule

If a future request conflicts with this freeze policy, do NOT guess whether the
override was intended. Only an explicit instruction such as "You may modify X",
"Change the existing X implementation", "Update these existing files: ..." or
"Refactor X" counts as authorization. When uncertain, preserve the existing
implementation.

## Golden rule

WORKING KAVACH FEATURES MUST KEEP WORKING. New ideas should be ADDITIVE and
ISOLATED by default. Do not destabilize finished functionality to implement a
new feature.
