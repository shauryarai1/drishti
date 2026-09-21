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
