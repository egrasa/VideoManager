#!/usr/bin/env python3
"""
Example script to read and display version information from the VideoManager version control system.
"""

import json
import sys
from pathlib import Path

def load_module_versions():
    """Load module version information."""
    version_file = Path(__file__).parent / "versions" / "modules" / "stable-versions.json"
    with open(version_file, 'r') as f:
        return json.load(f)

def load_database_versions():
    """Load database version information."""
    version_file = Path(__file__).parent / "versions" / "database" / "stable-versions.json"
    with open(version_file, 'r') as f:
        return json.load(f)

def display_module_versions():
    """Display all module versions."""
    data = load_module_versions()
    print(f"Module Versions (Last Updated: {data['lastUpdated']})")
    print("=" * 60)
    
    for module_name, module_info in data['modules'].items():
        print(f"\n{module_name.upper()}")
        print(f"  Version: {module_info['version']}")
        print(f"  Status: {module_info['status']}")
        print(f"  Description: {module_info['description']}")
        print(f"  Release Date: {module_info['releaseDate']}")

def display_database_versions():
    """Display database version information."""
    data = load_database_versions()
    print(f"\nDatabase Schema (Last Updated: {data['lastUpdated']})")
    print("=" * 60)
    
    schema = data['schema']
    print(f"\nSchema Version: {schema['version']}")
    print(f"Status: {schema['status']}")
    print(f"Description: {schema['description']}")
    print(f"Release Date: {schema['releaseDate']}")
    
    print(f"\nMigrations ({len(data['migrations'])} total):")
    for migration in data['migrations']:
        print(f"  [{migration['id']}] v{migration['version']} - {migration['description']}")
        print(f"      Status: {migration['status']}, Applied: {migration['appliedDate']}")

def get_module_version(module_name):
    """Get version of a specific module."""
    data = load_module_versions()
    if module_name in data['modules']:
        return data['modules'][module_name]['version']
    return None

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "modules":
            display_module_versions()
        elif command == "database":
            display_database_versions()
        elif command == "all":
            display_module_versions()
            print("\n")
            display_database_versions()
        elif command == "get" and len(sys.argv) > 2:
            module_name = sys.argv[2]
            version = get_module_version(module_name)
            if version:
                print(f"{module_name}: {version}")
            else:
                print(f"Module '{module_name}' not found")
                sys.exit(1)
        else:
            print("Unknown command")
            print("Usage: python3 version_info.py [modules|database|all|get <module_name>]")
            sys.exit(1)
    else:
        # Default: show all
        display_module_versions()
        print("\n")
        display_database_versions()

if __name__ == "__main__":
    main()
