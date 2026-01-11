# Release Process

ForgeWorks uses [Changesets](https://github.com/changesets/changesets) for automated versioning and releases.

## How It Works

### Automatic Flow

1. **During Development**: Contributors add changesets with their PRs
2. **On Merge**: Changesets accumulate in `.changeset/`
3. **Release PR**: Changesets bot opens "Version Packages" PR
4. **On Merge of Release PR**: Packages are versioned and tagged
5. **GitHub Releases**: Created automatically with changelogs

### Version Bumps

| Changeset Type | Version Bump | When to Use |
|----------------|--------------|-------------|
| `patch` | 0.0.X | Bug fixes, minor improvements |
| `minor` | 0.X.0 | New features (backwards compatible) |
| `major` | X.0.0 | Breaking changes |

## Creating a Release

### 1. Ensure Changesets Exist

Check pending changesets:

```bash
pnpm changeset status
```

### 2. Review the Release PR

When changesets are merged to main, the GitHub Action creates a "Version Packages" PR:

- Review the changelog entries
- Verify version bumps are correct
- Check for breaking changes

### 3. Merge the Release PR

Merging triggers:
1. Version updates in `package.json` files
2. `CHANGELOG.md` updates
3. Git tags (e.g., `@forge-works/frontend@0.4.0`)
4. GitHub Releases with release notes

## Manual Release (Emergency)

For emergency releases without the automation:

```bash
# 1. Create changeset if needed
pnpm changeset

# 2. Version packages
pnpm changeset:version

# 3. Commit version changes
git add .
git commit -m "chore: version packages"

# 4. Build and publish
pnpm changeset:publish

# 5. Push tags
git push --follow-tags
```

## Versioning Strategy

### Independent Versioning

Each package is versioned independently:

- `@forge-works/frontend` - Frontend dashboard
- `@forge-works/backend` - FastAPI backend
- Future packages version separately

### Tag Format

Tags follow the pattern:

```
@forge-works/<package>@<version>
```

Examples:
- `@forge-works/frontend@0.4.0`
- `@forge-works/backend@0.2.0`

## Changelogs

Changelogs are automatically generated from changesets:

- `src/frontend/CHANGELOG.md`
- `src/backend/CHANGELOG.md`

Each entry includes:
- Version number and date
- Change description from changeset
- PR link (via `@changesets/changelog-github`)

## Pre-releases (Future)

For pre-releases:

```bash
# Enter pre-release mode
pnpm changeset pre enter alpha

# Create changesets as normal
pnpm changeset

# Version creates alpha versions
pnpm changeset:version

# Exit pre-release mode when ready
pnpm changeset pre exit
```

## Troubleshooting

### No Changesets Found

```bash
# Add a changeset manually
pnpm changeset
```

### Wrong Version Bump

Before merging the release PR:
1. Edit the changeset file in `.changeset/`
2. Change `patch` to `minor` or `major`
3. Push the update

### Revert a Release

```bash
# Revert the version commit
git revert <commit-sha>

# Delete the tag
git tag -d @forge-works/frontend@0.4.0
git push origin :refs/tags/@forge-works/frontend@0.4.0
```

## Configuration

See `.changeset/config.json` for settings:

- `baseBranch`: main
- `changelog`: GitHub-linked changelogs
- `privatePackages`: Version even if private
- `access`: restricted (not published to npm)
