# Modules Version Control

This directory contains version control information for all VideoManager application modules.

## Structure

- `stable-versions.json` - The registry of all stable module versions

## Module Version Format

Each module in the registry includes:
- **version**: Semantic version number (e.g., "1.0.0")
- **description**: Brief description of the module
- **status**: Current status (stable, beta, deprecated)
- **releaseDate**: Date of the release

## Usage

### Adding a New Module Version

1. Update the `stable-versions.json` file
2. Add the new module entry with version information
3. Update the `lastUpdated` field to the current date

### Updating an Existing Module

1. Modify the version field for the specific module
2. Update the `lastUpdated` field
3. Optionally update the `status` if the module status changed

## Available Modules

- **core**: Core VideoManager functionality
- **player**: Video playback capabilities
- **uploader**: Video upload functionality
- **transcoder**: Video transcoding services

## Version Status

- `stable`: Production-ready, recommended for use
- `beta`: Under testing, may have issues
- `deprecated`: No longer recommended, use alternative
