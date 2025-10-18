"""Launch script for VideoManager application.

This script sets up the environment and launches the video organizer app.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Change to script directory to ensure relative imports work
os.chdir(current_dir)

# Launch the app
if __name__ == '__main__':
    try:
        from videomanager import main
        main()
    except ImportError as e:
        print(f'Error: Missing required modules: {e}')
        print('\nRequired packages:')
        print('  - tkinter (usually built-in)')
        print('  - Pillow (pip install Pillow)')
        print('  - python-vlc (pip install python-vlc) [optional for player]')
        sys.exit(1)
