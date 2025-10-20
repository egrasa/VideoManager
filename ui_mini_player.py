"""Mini floating player window for VideoManager.

Provides a compact floating window with playback controls that can be
positioned anywhere on screen and kept always-on-top.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class MiniPlayer:
    """Compact floating player window with essential controls."""

    def __init__(self, parent_root, on_command: Callable[[str], None]):
        """Initialize mini player.
        
        Args:
            parent_root: Parent Tk root window (for positioning reference)
            on_command: Callback function for player commands
                       Receives: 'play', 'pause', 'stop', 'volume:<0-100>'
        """
        self.parent_root = parent_root
        self.on_command = on_command
        self.is_playing = False
        self.current_volume = 100
        self.is_visible = False

        # Create floating window
        self.window = tk.Toplevel(parent_root)
        self.window.title('🎬 Mini Player')
        self.window.geometry('400x100')
        self.window.resizable(False, False)

        # Set window to always be on top
        self.window.attributes('-topmost', True)

        # Position window near top-right of parent
        self.window.update_idletasks()
        self._position_window()

        # Build UI
        self._build_ui()

        # Handle window close
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)

        # Initially hidden
        #self.window.withdraw()
        self.is_visible = False

        logger.info('Mini player created')

    def _position_window(self):
        """Position window near parent window's top-right corner."""
        try:
            # Get parent window position
            parent_x = self.parent_root.winfo_x()
            parent_y = self.parent_root.winfo_y()
            parent_width = self.parent_root.winfo_width()

            # Position mini player at top-right of parent, with offset
            x = parent_x + parent_width - 420  # 20px margin from right
            y = parent_y + 100  # Below the main window controls

            # Ensure window is within screen bounds
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            if x < 0:
                x = 10
            if y < 0:
                y = 10
            if x + 400 > screen_width:
                x = screen_width - 420
            if y + 140 > screen_height:
                y = screen_height - 160

            self.window.geometry(f'+{x}+{y}')
        except tk.TclError:
            # Window not yet fully initialized, skip positioning
            pass

    def _build_ui(self):
        """Build mini player UI."""
        # Main container
        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title/info label
        self.info_label = ttk.Label(
            main_frame,
            text='🎵 No video loaded',
            justify=tk.CENTER,
            font=('Arial', 9)
        )
        #self.info_label.pack(fill=tk.X, pady=(0, 10))

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=2)

        self.play_pause_btn = ttk.Button(
            button_frame,
            text='▶ Play',
            command=self._on_play_pause,
            width=10
        )
        self.play_pause_btn.pack(side=tk.LEFT, padx=3)

        # Skip backward button
        self.skip_back_btn = ttk.Button(
            button_frame,
            text='⏮ ',
            command=self._skip_backward,
            width=4
        )
        self.skip_back_btn.pack(side=tk.LEFT, padx=2)

        # Skip forward button
        self.skip_forward_btn = ttk.Button(
            button_frame,
            text=' ⏭',
            command=self._skip_forward,
            width=4
        )
        self.skip_forward_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(
            button_frame,
            text='⏹ Stop',
            command=self._on_stop,
            width=10
        )
        self.stop_btn.pack(side=tk.LEFT, padx=3)

        # Volume control
        volume_frame = ttk.Frame(main_frame)
        volume_frame.pack(fill=tk.X, pady=5)

        self.volume_label = ttk.Label(button_frame, text='100%', width=5)
        self.volume_label.pack(side=tk.LEFT, padx=2)

        ttk.Label(button_frame, text='🔊', width=2).pack(side=tk.LEFT, padx=2)

        self.volume_var = tk.IntVar(value=100)
        self.volume_slider = ttk.Scale(
            button_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            orient=tk.HORIZONTAL,
            command=self._on_volume_change)
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=2)

        self.time_label = ttk.Label(progress_frame, text='0:00 / 0:00', font=('Arial', 8))
        self.time_label.pack(side=tk.LEFT, padx=3)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            variable=self.progress_var,
            orient=tk.HORIZONTAL,
            command=self._on_progress_change
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # Control buttons at bottom
        control_frame = ttk.Frame(main_frame)
        #control_frame.pack(fill=tk.X, pady=2)

        self.pin_button = ttk.Button(control_frame, text='📍 Pin',
                                     command=self._toggle_topmost, width=6)
        #self.pin_button.pack(side=tk.LEFT, padx=2)

        self.refresh_button = ttk.Button(control_frame, text='Refresh',
                                         command=self._on_refresh, width=8)
        #self.refresh_button.pack(side=tk.LEFT, padx=2)

        self.close_button = ttk.Button(control_frame, text='×',
                                       command=self._on_close, width=3)
        #self.close_button.pack(side=tk.RIGHT, padx=2)

        # Keyboard shortcuts
        self.window.bind('<Left>', lambda e: self._skip_backward())
        self.window.bind('<Right>', lambda e: self._skip_forward())

    def _on_play(self):
        """Handle play button."""
        self.is_playing = True
        self.on_command('play')
        logger.debug('Mini player: play')

    def _on_pause(self):
        """Handle pause button."""
        self.is_playing = False
        self.on_command('pause')
        logger.debug('Mini player: pause')

    def _on_play_pause(self):
        """Toggle between play and pause."""
        if self.is_playing:
            self._on_pause()
            self.play_pause_btn.config(text='▶ Play')
        else:
            self._on_play()
            self.play_pause_btn.config(text='⏸ Pause')

    def _on_stop(self):
        """Handle stop button."""
        self.is_playing = False
        self.on_command('stop')
        self.play_pause_btn.config(text='▶ Play')
        logger.debug('Mini player: stop')

    def _skip_backward(self):
        """Skip backward 10 seconds."""
        self.on_command('skip_backward')
        logger.debug('Mini player: skip backward 10s')

    def _skip_forward(self):
        """Skip forward 10 seconds."""
        self.on_command('skip_forward')
        logger.debug('Mini player: skip forward 10s')

    def _on_volume_change(self, value: str):
        """Handle volume slider change."""
        volume = int(float(value))
        self.current_volume = volume
        self.volume_label.config(text=f'{volume}%')
        self.on_command(f'volume:{volume}')
        logger.debug('Mini player: volume %d', volume)

    def _on_progress_change(self, value: str):
        """Handle progress bar change (seek)."""
        progress = float(value)
        self.on_command(f'seek:{progress}')
        logger.debug('Mini player: seek %f', progress)

    def _on_refresh(self):
        """Refresh window position."""
        self._position_window()
        logger.debug('Mini player: repositioned')

    def _toggle_topmost(self):
        """Toggle always-on-top state."""
        current = self.window.attributes('-topmost')
        self.window.attributes('-topmost', not current)
        logger.debug('Mini player: topmost toggled to %s', not current)

    def _on_close(self):
        """Handle window close."""
        self.hide()
        logger.debug('Mini player: hidden')

    def show(self):
        """Show the mini player window."""
        self.window.deiconify()
        self._position_window()
        self.window.lift()  # Bring to front
        self.is_visible = True
        logger.info('Mini player: shown')

    def hide(self):
        """Hide the mini player window."""
        self.window.withdraw()
        self.is_visible = False
        logger.info('Mini player: hidden')

    def toggle_visibility(self):
        """Toggle mini player visibility."""
        if self.is_visible:
            self.hide()
        else:
            self.show()

    def update_info(self, title: str = '', current_time: float = 0, total_time: float = 0):
        """Update display info.
        
        Args:
            title: Current video title
            current_time: Current playback time in seconds
            total_time: Total duration in seconds
        """
        if title:
            display_title = f'🎵 {title[:40]}'
            if len(title) > 40:
                display_title += '...'
            self.info_label.config(text=display_title)

        if total_time > 0:
            current_formatted = self._format_time(current_time)
            total_formatted = self._format_time(total_time)
            self.time_label.config(text=f'{current_formatted} / {total_formatted}')

            # Update progress bar
            progress = (current_time / total_time) * 100 if total_time > 0 else 0
            self.progress_var.set(progress)

    def update_volume(self, volume: int):
        """Update volume display.
        
        Args:
            volume: Volume percentage (0-100)
        """
        self.current_volume = volume
        self.volume_var.set(volume)
        self.volume_label.config(text=f'{volume}%')

    def set_playing_state(self, is_playing: bool):
        """Update play/pause button state.
        
        Args:
            is_playing: Whether playback is active
        """
        self.is_playing = is_playing
        if is_playing:
            self.play_pause_btn.config(text='⏸ Pause')
        else:
            self.play_pause_btn.config(text='▶ Play')

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to MM:SS format."""
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{minutes}:{secs:02d}'

    def cleanup(self):
        """Cleanup resources."""
        try:
            self.window.destroy()
            logger.info('Mini player: cleaned up')
        except tk.TclError:
            pass
