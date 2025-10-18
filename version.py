"""Version management module for VideoManager application."""

import logging
from pathlib import Path
from typing import Dict, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class VersionInfo:
    """Version information container."""

    def __init__(self, major: int, minor: int, patch: int, pre_release: str = "", build: str = ""):
        """Initialize version.
        
        Args:
            major: Major version number
            minor: Minor version number
            patch: Patch version number
            pre_release: Pre-release label (alpha, beta, rc, etc.)
            build: Build metadata
        """
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre_release = pre_release
        self.build = build

    def __str__(self) -> str:
        """Return version string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            version += f"-{self.pre_release}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, VersionInfo):
            return False
        return (self.major == other.major and
                self.minor == other.minor and
                self.patch == other.patch)

    def __lt__(self, other) -> bool:
        """Check if less than."""
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other) -> bool:
        """Check if less than or equal."""
        return self < other or self == other

    def __gt__(self, other) -> bool:
        """Check if greater than."""
        if not isinstance(other, VersionInfo):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other) -> bool:
        """Check if greater than or equal."""
        return self > other or self == other


class VersionManager:
    """Manage application and module versions."""

    # Current application version
    APP_VERSION = VersionInfo(1, 0, 0, "", "20251018")

    # Module versions
    MODULE_VERSIONS = {
        'videomanager': VersionInfo(1, 0, 0),
        'ui_preview': VersionInfo(1, 2, 0),  # Timeline features added
        'ui_player': VersionInfo(1, 1, 0),   # Interactive timeline added
        'ui_edit': VersionInfo(1, 0, 0),
        'video_db': VersionInfo(1, 1, 0),    # Auto-duration detection
        'thumbnail_generator': VersionInfo(1, 2, 0),  # Hardware accel fix
    }

    # Database version
    DB_VERSION = VersionInfo(1, 1, 0)

    # Features changelog
    CHANGELOG = {
        '1.0.0': {
            'date': '2025-10-18',
            'features': [
                'Initial release',
                'Grid/List/Timeline video views',
                'VLC-based video player with interactive timeline',
                'FFmpeg-based thumbnail generation',
                'SQLite database for video metadata',
                'Threading for responsive UI',
                'Dynamic responsive grid layout',
            ],
        }
    }

    @staticmethod
    def get_version_file_path() -> Path:
        """Get path to version file.
        
        Returns:
            Path to version.json
        """
        return Path(__file__).parent / 'version.json'

    @staticmethod
    def get_app_version() -> VersionInfo:
        """Get application version.
        
        Returns:
            VersionInfo of application
        """
        return VersionManager.APP_VERSION

    @staticmethod
    def get_module_version(module_name: str) -> Optional[VersionInfo]:
        """Get module version.
        
        Args:
            module_name: Name of module
            
        Returns:
            VersionInfo or None if not found
        """
        return VersionManager.MODULE_VERSIONS.get(module_name)

    @staticmethod
    def get_db_version() -> VersionInfo:
        """Get database version.
        
        Returns:
            VersionInfo of database
        """
        return VersionManager.DB_VERSION

    @staticmethod
    def save_version_info() -> bool:
        """Save version information to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            version_info = {
                'app_version': str(VersionManager.APP_VERSION),
                'db_version': str(VersionManager.DB_VERSION),
                'modules': {name: str(ver) for name, ver in VersionManager.MODULE_VERSIONS.items()},
                'saved_at': datetime.now().isoformat(),
                'changelog': VersionManager.CHANGELOG,
            }

            version_file = VersionManager.get_version_file_path()
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2)

            logger.info("Version information saved to %s", version_file)
            return True
        except (OSError, IOError) as e:
            logger.error("Failed to save version information: %s", e)
            return False

    @staticmethod
    def load_version_info() -> Optional[Dict]:
        """Load version information from file.
        
        Returns:
            Dict with version information or None if file not found
        """
        try:
            version_file = VersionManager.get_version_file_path()
            if not version_file.exists():
                return None

            with open(version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            logger.error("Failed to load version information: %s", e)
            return None

    @staticmethod
    def get_version_string() -> str:
        """Get formatted version string for display.
        
        Returns:
            Formatted version string
        """
        app_ver = VersionManager.APP_VERSION
        db_ver = VersionManager.DB_VERSION

        lines = [
            "=" * 60,
            "VideoManager - Version Information",
            "=" * 60,
            f"Application Version: {app_ver}",
            f"Database Version: {db_ver}",
            "",
            "Module Versions:",
        ]

        for module_name, version in sorted(VersionManager.MODULE_VERSIONS.items()):
            lines.append(f"  • {module_name}: {version}")

        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def log_version_info() -> None:
        """Log version information to logger."""
        logger.info("=" * 60)
        logger.info("VideoManager - Version Information")
        logger.info("=" * 60)
        logger.info("Application Version: %s", VersionManager.APP_VERSION)
        logger.info("Database Version: %s", VersionManager.DB_VERSION)
        logger.info("-" * 60)
        logger.info("Module Versions:")

        for module_name, version in sorted(VersionManager.MODULE_VERSIONS.items()):
            logger.info("  • %s: %s", module_name, version)

        logger.info("=" * 60)

    @staticmethod
    def check_compatibility() -> Dict[str, bool]:
        """Check version compatibility between components.
        
        Returns:
            Dict with compatibility status
        """
        compatibility = {
            'all_compatible': True,
            'warnings': [],
            'errors': [],
        }

        # Check if any module version is significantly outdated
        app_major = VersionManager.APP_VERSION.major

        for module_name, module_ver in VersionManager.MODULE_VERSIONS.items():
            if module_ver.major < app_major:
                warning = f"Module '{module_name}' version {module_ver} is outdated (app is {VersionManager.APP_VERSION})"
                compatibility['warnings'].append(warning)
                logger.warning(warning)

        # Check database compatibility
        if VersionManager.DB_VERSION.major < VersionManager.APP_VERSION.major:
            error = f"Database version {VersionManager.DB_VERSION} is incompatible with app {VersionManager.APP_VERSION}"
            compatibility['errors'].append(error)
            compatibility['all_compatible'] = False
            logger.error(error)

        if compatibility['all_compatible'] and not compatibility['warnings']:
            logger.info("All components are compatible ✓")

        return compatibility

    @staticmethod
    def get_feature_list() -> str:
        """Get formatted feature list.
        
        Returns:
            Formatted feature list string
        """
        lines = ["Features in this version:"]

        for version, info in sorted(VersionManager.CHANGELOG.items()):
            lines.append(f"\n  Version {version} ({info['date']}):")
            for feature in info['features']:
                lines.append(f"    • {feature}")

        return "\n".join(lines)
