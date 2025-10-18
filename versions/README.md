# Version Control Repository

This directory contains stable version information for the VideoManager application.

## Purpose

This version control system helps:
- Track stable versions of application modules
- Manage database schema versions and migrations
- Coordinate releases across different environments
- Maintain version history for auditing and rollback purposes

## Structure

```
versions/
├── modules/          # Module version tracking
│   ├── README.md
│   └── stable-versions.json
└── database/         # Database version tracking
    ├── README.md
    └── stable-versions.json
```

## Quick Start

### Check Current Stable Versions

**Modules:**
```bash
cat versions/modules/stable-versions.json
```

**Database:**
```bash
cat versions/database/stable-versions.json
```

### Update a Module Version

1. Edit `versions/modules/stable-versions.json`
2. Update the specific module's version number
3. Update the `lastUpdated` field
4. Commit the changes

### Add a Database Migration

1. Edit `versions/database/stable-versions.json`
2. Add a new entry to the `migrations` array
3. Update schema version if needed
4. Update the `lastUpdated` field
5. Commit the changes

## Version Scheme

This repository uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: Backwards-compatible functionality
- **PATCH** version: Backwards-compatible bug fixes

## Workflows

### Release Process

1. Test new module/database versions in development
2. Update the respective `stable-versions.json` file
3. Tag the commit with the version number
4. Deploy to production

### Rollback Process

1. Check version history in git
2. Identify the last stable version
3. Update `stable-versions.json` to point to previous version
4. Deploy the rollback

## Best Practices

1. **Always test** versions before marking them as stable
2. **Document changes** in each version
3. **Keep history** - don't delete old version information
4. **Use status flags** to indicate version stability
5. **Coordinate updates** across modules and database together

## Contributing

When updating versions:
1. Ensure all tests pass
2. Update relevant documentation
3. Follow semantic versioning rules
4. Update the `lastUpdated` timestamp
5. Create a clear commit message

## Support

For questions about version management, consult:
- Module README: `versions/modules/README.md`
- Database README: `versions/database/README.md`
