# VideoManager

Repository for video manager app - includes stable version control for modules and database.

## Version Control

This repository maintains stable versions of:
- **Application Modules**: Core components of the VideoManager application
- **Database**: Schema versions and migration tracking

See the [versions directory](./versions/README.md) for detailed information on version management.

## Directory Structure

```
VideoManager/
├── versions/          # Version control for modules and database
│   ├── modules/       # Module version tracking
│   └── database/      # Database version tracking
└── README.md
```

## Quick Start

### View Version Information

Use the provided Python script to display version information:

```bash
# View all versions
python3 version_info.py all

# View only module versions
python3 version_info.py modules

# View only database versions
python3 version_info.py database

# Get specific module version
python3 version_info.py get core
```

## Quick Links

- [Quick Start Guide](./QUICK_START.md) - Common tasks and examples
- [Version Management Guide](./versions/README.md)
- [Module Versions](./versions/modules/README.md)
- [Database Versions](./versions/database/README.md)
- [Changelog](./CHANGELOG.md)
