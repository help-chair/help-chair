# Contributing guide — Help Chair (monorepo)

[Versión en español → CONTRIBUTING.md](CONTRIBUTING.md)

Seven teams work in one repository. This guide lets anyone work on a branch, push changes and merge them **without stepping on other teams' work**.

## 0. Monorepo golden rules

1. **Work only inside your team's folder.** `CODEOWNERS` requires the owner's approval for each folder.
2. **Cross-folder changes:** split them into separate PRs or get approval from both teams.
3. **Teams communicate through contracts** (`contracts/`), never by importing code or reading another service's DB.
4. **Small, frequent PRs.** With 7 teams on `develop`, a big old PR = conflicts.
5. **Each folder has its own path-filtered CI:** your CI only runs when you change your folder.

## 1. Branching model

| Branch | Purpose | Who writes | Protected |
|---|---|---|---|
| `main` | Stable, deployable. | Only via PR from `develop` or `hotfix/*` | ✅ |
| `develop` | Integration of all teams. Default branch. | Only via PR from working branches | ✅ |
| `feature/<area>/<n>-<slug>` | New functionality. Branches off `develop`. | The developer | ❌ |
| `fix/<area>/<n>-<slug>` | Bug fix on `develop`. | The fixer | ❌ |
| `hotfix/<area>/<n>-<slug>` | Urgent fix on `main`. | The fixer | ❌ |
| `docs/<slug>`, `chore/<slug>`, `refactor/<area>/<slug>` | Docs, maintenance, refactoring. | The author | ❌ |

- `<area>` = `events`, `access`, `requests`, `incidents`, `problems`, `knowledge`, `frontend`, `gateway`, `deploy` or `contracts`.
- `<n>` = issue number; `<slug>` = short lowercase hyphenated description.
- Example: `feature/events/42-informational-classification`.

**Rules:** **short-lived** branches (ideally < 1 week), deleted after merge, and **no** direct pushes to `main` or `develop`.

## 2. Daily workflow

```bash
# 1. Sync and create your branch
git switch develop
git pull origin develop
git switch -c feature/events/42-informational-classification

# 2. Work in your folder with small commits (see section 3)
git add services/events
git commit -m "feat(events): add informational event rule"

# 3. Update your branch with develop often (at least daily)
git fetch origin
git rebase origin/develop       # or: git merge origin/develop

# 4. Push your branch and open a Pull Request into develop
git push -u origin feature/events/42-informational-classification
```

> If others already share your branch, use `merge` instead of `rebase` and never force-push.
> Tip: use `git add <your-folder>` instead of `git add .` to avoid committing files from other areas by accident.

## 3. Commits — Conventional Commits with mandatory *scope*

Format: `type(scope): imperative description`

| Type | Use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting (no logic change) |
| `refactor` | Internal change, same behaviour |
| `perf` | Performance improvement |
| `test` | Tests |
| `build` / `ci` | Dependencies, Dockerfile, pipelines |
| `chore` | Maintenance |
| `revert` | Revert a commit |

**Allowed scopes** (one per folder): `events`, `access`, `requests`, `incidents`, `problems`, `knowledge`, `frontend`, `gateway`, `deploy`, `contracts`, `docs`, `ci`, `repo`.

- Breaking change: add `!` (`feat(contracts)!: …`) and explain with `BREAKING CHANGE:` in the body.
- Reference the issue: `Closes #42`.

## 4. Pull Requests

1. **Target:** `develop` (or `main` for `hotfix/*`).
2. **Title:** Conventional Commits with scope (a workflow validates it; used as the squash message).
3. Fill in the template (what, why, affected area, how to test, checklist).
4. **Size:** preferably < 400 lines. Split larger changes.
5. **Review:** at least **1 code-owner approval** for the folders touched. Authors don't approve their own PR.
6. Conversations resolved and CI checks green.
7. If you change a contract, **mention the consuming teams** (`@help-chair/team-…`) in the PR and wait for their OK.

## 5. Merge strategy

| From → To | Method | Reason |
|---|---|---|
| working branch → `develop` | **Squash and merge** | 1 commit per change; readable history with 7 teams |
| `develop` → `main` | **Merge commit** | Keeps integration history |
| `hotfix/*` → `main` | **Merge commit** | Traceability of the urgent fix |
| `main` → `develop` (after a hotfix) | **Merge commit** | Keep the fix from being lost |

*Rebase and merge* is not used in the GitHub UI.

## 6. Versioning and releases (per service)

- **SemVer per service**, not per repository. Tag on `main` as `<folder>/vX.Y.Z`, e.g. `events/v1.2.0` or `platform-gateway/v0.3.1`.
- Each tag triggers (in the team's CI) publishing the image `ghcr.io/help-chair/hc-<service>:X.Y.Z`.
- Create a GitHub Release per tag with change notes.
- `contracts/` is versioned with the service that publishes it; a breaking change requires `MAJOR`.
- To release: PR `develop` → `main`, then after merging create tags for the services that changed.

## 7. Per-folder CI

Each team creates its workflow in `.github/workflows/<service>-ci.yml` (its folder, its language), path-filtered. Example:

```yaml
name: events-ci
on:
  pull_request:
    paths: ['services/events/**', 'contracts/events/**', 'contracts/messages/**']
  push:
    branches: [develop]
    paths: ['services/events/**']
jobs:
  build-test:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: services/events } }
    steps:
      - uses: actions/checkout@v4
      # TODO: language setup, tests and image build
```

> Files under `.github/workflows/` belong to Platform per `CODEOWNERS`; Platform approves PRs for new workflows.

## 8. Hotfix

```bash
git switch main && git pull origin main
git switch -c hotfix/access/57-fix-login
# ...fix + commit...
# PR into main → merge → tag access/vX.Y.(Z+1)
# Then PR main → develop
```

## 9. Security

- **Never** commit secrets, tokens, passwords or `.env` files. Use `.env.example`.
- If you commit a secret by mistake, **revoke it immediately** and tell the maintainers (deleting the commit is not enough).

## 10. Definition of done

- [ ] Touches only my team's folder (or is justified and approved).
- [ ] Meets the *Minimum service contract* (if applicable).
- [ ] Tests included and passing.
- [ ] Documentation and OpenAPI updated.
- [ ] `contracts/` updated if APIs or messages change.
- [ ] No secrets or real data.
- [ ] PR reviewed and approved.

## 11. Configured protection rules

`main` and `develop`: PR required, 1 code-owner approval, stale approvals dismissed, conversations resolved, no force-push or deletion.
