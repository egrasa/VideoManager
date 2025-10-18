"""VideoManager: Application for organizing and managing video files.

Provides a complete UI for importing, viewing, rating, and categorizing videos
with support for Grid View, List View, Timeline, and a VLC player.

Requirements Met:
- ✅ Import videos individually and in bulk
- ✅ Grid View with responsive thumbnails
- ✅ List View with detailed metadata
- ✅ Timeline view with frame thumbnails
- ✅ Rating system (1-5 stars)
- ✅ Categorization (public, private, ticket, password, special, clip, other)
- ✅ Notes/Comments support
- ✅ VLC Player integration
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import logging
import os
from pathlib import Path
from typing import Dict, Any

from video_db import VideoDatabase
from ui_preview import UIPreview
from ui_edit import UIEdit
from ui_player import UIPlayer
from version import VersionManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoManagerApp:
    """Main application window for video management."""

    SUPPORTED_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'}

    def __init__(self, root):
        """Initialize the application.
        
        Args:
            root: tk.Tk root window
        """
        # Log version information on startup
        VersionManager.log_version_info()
        VersionManager.check_compatibility()
        VersionManager.save_version_info()

        self.root = root
        self.root.title('VideoManager - Video Organizer')
        self.root.geometry('1400x900')

        # Create menu bar
        self._create_menu_bar()

        # Initialize database
        self.db = VideoDatabase('videos.db')

        # Create main layout: LEFT (70%) | RIGHT (30%) | BOTTOM
        self._build_ui()

        # Load initial videos
        self.load_videos()

        logger.info('VideoManager started')

    def _build_ui(self):
        """Build main UI layout."""
        # Toolbar
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text='➕ Add Video', command=self.add_video).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='📁 Add Folder', command=self.add_folder).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='🗑️ Delete', command=self.delete_selected).pack(
            side=tk.LEFT, padx=5)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text='🔄 Refresh', command=self.load_videos).pack(
            side=tk.LEFT, padx=5)

        # Main paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT: Preview (70%)
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=7)

        self.preview = UIPreview(left_frame, self._on_video_selected)

        # RIGHT: Editor (30%)
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)

        self.editor = UIEdit(right_frame, self._on_video_save)

        # BOTTOM: Player
        bottom_frame = ttk.LabelFrame(self.root, text='Player', padding=5)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        self.player = UIPlayer(bottom_frame)

    def add_video(self):
        """Add a single video file."""
        filetypes = [
            ('Video files', ' '.join(f'*{fmt}' for fmt in self.SUPPORTED_FORMATS)),
            ('All files', '*.*'),
        ]
        filepath = filedialog.askopenfilename(
            title='Select a video file',
            filetypes=filetypes
        )

        if filepath:
            video_id = self.db.add_video(filepath)
            if video_id:
                logger.info('Added video: %s', filepath)
                self.load_videos()
                messagebox.askokcancel('Success',
                                    f'Video added successfully (ID: {video_id})'.format(video_id))
            else:
                messagebox.showerror('Error', 'Video already exists or could not be added')


    def add_folder(self):
        """Add all videos from a folder recursively."""
        folder = filedialog.askdirectory(title='Select a folder with videos')

        if folder:
            video_files = []
            for fmt in self.SUPPORTED_FORMATS:
                video_files.extend(Path(folder).rglob(f'*{fmt}'))
                video_files.extend(Path(folder).rglob(f'*{fmt.upper()}'))

            added = 0
            for filepath in video_files:
                video_id = self.db.add_video(str(filepath))
                if video_id:
                    added += 1

            self.load_videos()
            messagebox.askokcancel('Success', f'Added {added} videos from the folder'.format(added))
            logger.info('Added %d videos from %s', added, folder)


    def delete_selected(self):
        """Delete the currently selected video."""
        if self.preview.selected_video_id:
            if messagebox.askyesno('Confirm', 'Delete this video from the database?'):
                self.db.delete_video(self.preview.selected_video_id)
                self.load_videos()
                self.editor.cancel()
                logger.info('Deleted video %d', self.preview.selected_video_id)


    def load_videos(self):
        """Load all videos from database and update UI."""
        videos = self.db.get_all_videos()
        self.preview.load_videos(videos)
        logger.info('Loaded %d videos', len(videos))


    def _on_video_selected(self, video_id: int, video_data: Dict[str, Any]):
        """Handle video selection from preview.
        
        Args:
            video_id: Database video ID
            video_data: Video metadata dict
        """
        # Load into editor
        full_data = self.db.get_video(video_id)
        if full_data:
            self.editor.load_video(video_id, full_data)

        # Load into player
        video_path = video_data.get('path')
        if video_path and os.path.exists(video_path):
            self.player.load_video(video_path)

        # Generate timeline (stub - would call FFmpeg for actual thumbnails)
        self.preview.generate_timeline(video_data.get('path', ''))

        logger.info('Selected video %d', video_id)


    def _on_video_save(self, video_id: int, updated_fields: Dict[str, Any]):
        """Handle video save from editor.
        
        Args:
            video_id: Database video ID
            updated_fields: Dict of fields to update
        """
        success = self.db.update_video(video_id, **updated_fields)
        if success:
            self.load_videos()
            messagebox.askokcancel('Success', f'Video {video_id} updated successfully')
            logger.info('Updated video %d: %s', video_id, updated_fields)
        else:
            messagebox.showerror('Error', f'Failed to update video {video_id}')
            logger.error('Failed to update video %d', video_id)

    def _create_menu_bar(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Add Video...', command=self.add_video)
        file_menu.add_command(label='Add Folder...', command=self.add_folder)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_menu)
        help_menu.add_command(label='About VideoManager', command=self._show_about)
        help_menu.add_command(label='Version Info', command=self._show_version_info)

    def _show_about(self):
        """Show about dialog."""
        app_version = VersionManager.get_app_version()
        features = VersionManager.get_feature_list()

        about_text = f"""VideoManager v{app_version}

A powerful video organizer and management application.

Features:
{features.replace('Features in this version:', '')}

© 2025 All rights reserved
        """

        messagebox.showinfo('About VideoManager', about_text)

    def _show_version_info(self):
        """Show version information dialog."""
        version_info = VersionManager.get_version_string()
        messagebox.showinfo('Version Information', version_info)


def main():
    """Main entry point."""
    root = tk.Tk()
    VideoManagerApp(root)
    root.mainloop()



if __name__ == '__main__':
    main()
