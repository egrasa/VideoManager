# Quick Reference Guide

## Common Tasks

### View Current Stable Versions

**All module versions:**
```bash
cat versions/modules/stable-versions.json
```

**All database versions:**
```bash
cat versions/database/stable-versions.json
```

### Update a Module Version

1. Open `versions/modules/stable-versions.json`
2. Find the module you want to update (e.g., "core", "player", "uploader", "transcoder")
3. Change the `version` field
4. Update the `lastUpdated` field to today's date
5. Save and commit

Example:
```json
"core": {
  "version": "1.1.0",  // Changed from 1.0.0
  "description": "Core VideoManager module",
  "status": "stable",
  "releaseDate": "2025-10-18"
}
```

### Add a New Module

1. Open `versions/modules/stable-versions.json`
2. Add a new entry under `modules`:
```json
"newmodule": {
  "version": "1.0.0",
  "description": "Description of new module",
  "status": "stable",
  "releaseDate": "2025-10-18"
}
```
3. Update the `lastUpdated` field
4. Save and commit

### Record a Database Migration

1. Open `versions/database/stable-versions.json`
2. Add a new entry to the `migrations` array:
```json
{
  "id": "002",
  "version": "1.1.0",
  "description": "Add new tables for feature X",
  "appliedDate": "2025-10-18",
  "status": "applied"
}
```
3. Update the schema `version` if needed
4. Update the `lastUpdated` field
5. Save and commit

### Check Version History

```bash
git log --oneline versions/
```

### Rollback to Previous Version

```bash
git log versions/modules/stable-versions.json  # Find commit hash
git show <commit-hash>:versions/modules/stable-versions.json
```

## File Locations

- **Module versions:** `versions/modules/stable-versions.json`
- **Database versions:** `versions/database/stable-versions.json`
- **Module docs:** `versions/modules/README.md`
- **Database docs:** `versions/database/README.md`
- **Full guide:** `versions/README.md`

## Status Values

- `stable`: Production-ready
- `beta`: Testing phase
- `deprecated`: No longer recommended

## Version Format

Use Semantic Versioning: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

Example: `1.2.3`
- Major version: 1
- Minor version: 2
- Patch version: 3
