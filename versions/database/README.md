# Database Version Control

This directory contains version control information for the VideoManager database schema and migrations.

## Structure

- `stable-versions.json` - The registry of stable database versions and migrations

## Database Version Format

The registry includes:
- **schema.version**: Current stable schema version
- **schema.description**: Description of the schema
- **schema.status**: Current status (stable, beta)
- **schema.releaseDate**: Date of the release
- **migrations**: Array of applied migrations

## Migration Format

Each migration includes:
- **id**: Unique migration identifier
- **version**: Associated version number
- **description**: What the migration does
- **appliedDate**: When it was applied
- **status**: Current status (applied, pending, rolled back)

## Usage

### Adding a New Migration

1. Update the `stable-versions.json` file
2. Add a new migration entry to the `migrations` array
3. Increment the migration `id`
4. Update the schema `version` if needed
5. Update the `lastUpdated` field

### Tracking Database Changes

Use this registry to:
- Track which schema version is stable
- Record all applied migrations
- Maintain a history of database changes
- Coordinate database updates across environments

## Best Practices

- Always increment the schema version when applying breaking changes
- Document all migrations with clear descriptions
- Mark migrations as "applied" only after successful execution
- Keep migration history for audit purposes
