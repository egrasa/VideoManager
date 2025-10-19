"""UIPlayer component: VLC-based video player."""

import logging
import tkinter as tk
from tkinter import ttk
import threading
import time
import vlc
from ui_mini_player import MiniPlayer

logger = logging.getLogger(__name__)


class UIPlayer:
    """Video player component using VLC (if available)."""

    def __init__(self, parent):
        """Initialize the player.
        
        Args:
            parent: tk container for the player
        """
        self.parent = parent
        self.player = None
        self.current_video_path = None
        self.vlc_media_player = None
        self.playback_thread = None
        self.playback_running = False
        self.total_duration = 0
        self.is_seeking = False

        # Create player frame
        self.frame = ttk.LabelFrame(self.parent, text='Video Player', padding=10)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)


        # Control buttons
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.play_btn = ttk.Button(control_frame, text='▶ Play', command=self.play)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = ttk.Button(control_frame, text='⏸ Pause', command=self.pause)
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text='⏹ Stop', command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Mini player button
        self.mini_player_btn = ttk.Button(control_frame, text='🪟 Mini', command=self._toggle_mini_player, width=8)
        self.mini_player_btn.pack(side=tk.LEFT, padx=5)

        # Placeholder for player
        self.info_label = ttk.Label(
            control_frame,
            text='  Video Player (VLC integration) - Select a video to play  ',
            justify=tk.CENTER
        )
        self.info_label.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=10, pady=5)

        # Volume control (compact, right side)
        self.mute_btn = ttk.Button(control_frame, text='🔊', command=self._toggle_mute, width=3)
        self.mute_btn.pack(side=tk.RIGHT, padx=5)

        # Volume slider (small, right side)
        self.volume_var = tk.IntVar(value=100)
        self.volume_slider = ttk.Scale(
            control_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            orient=tk.HORIZONTAL,
            command=self._on_volume_change,
            length=80
        )
        self.volume_slider.pack(side=tk.RIGHT, padx=5)

        # Volume percentage label (right side)
        self.volume_percent_label = ttk.Label(control_frame, text='100%', width=5)
        self.volume_percent_label.pack(side=tk.RIGHT, padx=3)

        # Progress bar frame with time labels
        progress_frame = ttk.Frame(self.frame)
        progress_frame.pack(fill=tk.X, pady=5, padx=5)

        # Current time label (left)
        self.current_time_label = ttk.Label(progress_frame, text='0:00', width=6)
        self.current_time_label.pack(side=tk.LEFT, padx=5)

        # Progress bar (center, expandable)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            variable=self.progress_var,
            orient=tk.HORIZONTAL,
            command=self._on_progress_change
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Total time label (right)
        self.total_time_label = ttk.Label(progress_frame, text='0:00', width=6)
        self.total_time_label.pack(side=tk.LEFT, padx=5)

        # Attempt to import vlc
        try:
            self.vlc_instance = vlc.Instance()
            self.player = self.vlc_instance.media_list_player_new()
            self.vlc_media_player = self.player.get_media_player()
            self.is_muted = False
            self.previous_volume = 100  # For mute toggle
            self.info_label.config(text='VLC Player Ready  - Select a video to play')
        except ImportError:
            logger.warning('python-vlc not installed; player will be disabled')
            self.vlc_instance = None
            self.player = None
            self.vlc_media_player = None
            self.is_muted = False
            self.previous_volume = 100

        # Initialize mini player
        self.mini_player = MiniPlayer(
            self.parent.winfo_toplevel(),
            self._on_mini_player_command
        )
        logger.info('Mini player initialized')

    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string (MM:SS)
        """
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def load_video(self, video_path: str):
        """Load a video file.
        
        Args:
            video_path: Full path to video file
        """
        self.current_video_path = video_path
        self.info_label.config(text=f'Loaded: {video_path}')
        self.progress_var.set(0)
        self.current_time_label.config(text='0:00')
        self.total_time_label.config(text='0:00')
        self.total_duration = 0

        if self.player:
            try:
                media = self.vlc_instance.media_new(video_path)
                media_list = self.vlc_instance.media_list_new()
                media_list.add_media(media)
                self.player.set_media_list(media_list)

                # Get video duration (requires parsing media)
                # VLC doesn't provide duration until media is parsed
                # This will be updated when playback starts
                logger.info('Loaded video: %s', video_path)
            except (RuntimeError, ValueError, OSError):
                logger.exception('Error loading video: %s', video_path)

    def _update_playback_position(self):
        """Update playback position in a separate thread."""
        while self.playback_running:
            if self.vlc_media_player and not self.is_seeking:
                try:
                    # Get current time and duration
                    current_ms = self.vlc_media_player.get_time()
                    duration_ms = self.vlc_media_player.get_length()

                    if duration_ms > 0:
                        self.total_duration = duration_ms / 1000.0  # Convert to seconds
                        current_sec = current_ms / 1000.0
                        progress = (current_ms / duration_ms) * 100

                        # Update UI (thread-safe)
                        self.parent.after(0, lambda c=current_sec, p=progress,
                                          d=self.total_duration:
                            self._update_ui_position(c, p, d))
                except (RuntimeError, AttributeError):
                    pass

            time.sleep(0.1)  # Update every 100ms

    def _update_ui_position(self, current_sec: float, progress: float, duration: float):
        """Update UI with current playback position.
        
        Args:
            current_sec: Current time in seconds
            progress: Progress percentage (0-100)
            duration: Total duration in seconds
        """
        self.current_time_label.config(text=self._format_time(current_sec))
        self.total_time_label.config(text=self._format_time(duration))

        # Only update progress bar if user isn't dragging
        if not self.is_seeking:
            self.progress_var.set(progress)

        # Update mini player if visible
        if self.mini_player and self.mini_player.is_visible:
            self.mini_player.update_info('', current_sec, duration)

    def _on_progress_change(self, value: str):
        """Handle progress bar changes (user dragging).
        
        Args:
            value: New progress value (0-100)
        """
        if self.vlc_media_player and self.total_duration > 0:
            progress = float(value)
            # Set seeking flag to prevent update thread from updating
            self.is_seeking = True

            # Calculate time to seek to
            seek_ms = int((progress / 100.0) * self.total_duration * 1000)

            try:
                self.vlc_media_player.set_time(seek_ms)
                current_sec = seek_ms / 1000.0
                self.current_time_label.config(text=self._format_time(current_sec))
            except (RuntimeError, ValueError):
                logger.exception('Error seeking video')
            finally:
                self.is_seeking = False

    def play(self):
        """Play video."""
        if self.player:
            try:
                self.player.play()
                self.info_label.config(text=f'Playing: {self.current_video_path}')

                # Start playback update thread if not already running
                if not self.playback_running:
                    self.playback_running = True
                    self.playback_thread = threading.Thread(
                        target=self._update_playback_position,
                        daemon=True
                    )
                    self.playback_thread.start()
            except (RuntimeError, ValueError, OSError):
                logger.exception('Error playing video')

    def pause(self):
        """Pause video."""
        if self.player:
            try:
                self.player.pause()
                self.info_label.config(text='Paused')
            except (RuntimeError, ValueError, OSError):
                logger.exception('Error pausing video')

    def stop(self):
        """Stop video."""
        if self.player:
            try:
                self.player.stop()
                self.playback_running = False
                self.info_label.config(text='Stopped')
                self.progress_var.set(0)
                self.current_time_label.config(text='0:00')
            except (RuntimeError, ValueError, OSError):
                logger.exception('Error stopping video')

    def seek(self, seconds: float):
        """Seek to a specific time.
        
        Args:
            seconds: Time in seconds to seek to
        """
        if self.vlc_media_player and self.total_duration > 0:
            try:
                seek_ms = int(seconds * 1000)
                self.vlc_media_player.set_time(seek_ms)
                self.current_time_label.config(text=self._format_time(seconds))
            except (RuntimeError, ValueError):
                logger.exception('Error seeking video')

    def _on_volume_change(self, value: str):
        """Handle volume slider changes.
        
        Args:
            value: Volume level (0-100)
        """
        volume = int(float(value))
        self.volume_percent_label.config(text=f'{volume}%')

        if self.vlc_media_player:
            try:
                self.vlc_media_player.audio_set_volume(volume)
                self.previous_volume = volume

                # Update mute button icon based on volume
                if volume == 0:
                    self.mute_btn.config(text='🔇')
                elif volume < 50:
                    self.mute_btn.config(text='🔉')
                else:
                    self.mute_btn.config(text='🔊')

                self.is_muted = volume == 0
            except (RuntimeError, ValueError):
                logger.exception('Error setting volume')

    def _toggle_mute(self):
        """Toggle mute on/off."""
        if self.vlc_media_player:
            try:
                if self.is_muted:
                    # Unmute: restore previous volume
                    self.volume_var.set(self.previous_volume)
                    self.vlc_media_player.audio_set_volume(self.previous_volume)
                    self.volume_percent_label.config(text=f'{self.previous_volume}%')
                    self.mute_btn.config(text='🔊')
                    self.is_muted = False
                else:
                    # Mute: set volume to 0 and save current volume
                    if self.volume_var.get() > 0:
                        self.previous_volume = self.volume_var.get()
                    self.volume_var.set(0)
                    self.vlc_media_player.audio_set_volume(0)
                    self.volume_percent_label.config(text='0%')
                    self.mute_btn.config(text='🔇')
                    self.is_muted = True
            except (RuntimeError, ValueError):
                logger.exception('Error toggling mute')

    def _toggle_mini_player(self):
        """Toggle mini player visibility."""
        self.mini_player.toggle_visibility()
        logger.info('Mini player toggled')

    def _on_mini_player_command(self, command: str):
        """Handle commands from mini player.
        
        Args:
            command: Command string ('play', 'pause', 'stop', 'volume:N', 'seek:N')
        """
        try:
            if command == 'play':
                self.play()
            elif command == 'pause':
                self.pause()
            elif command == 'stop':
                self.stop()
            elif command.startswith('volume:'):
                volume = int(command.split(':')[1])
                self.volume_var.set(volume)
                self._on_volume_change(str(volume))
            elif command.startswith('seek:'):
                progress = float(command.split(':')[1])
                self._on_progress_change(str(progress))
        except (ValueError, IndexError) as e:
            logger.error('Error processing mini player command: %s', e)

    def update_mini_player_info(self):
        """Update mini player with current playback info."""
        if self.mini_player and self.mini_player.is_visible:
            try:
                title = ''
                if self.current_video_path:
                    import os
                    title = os.path.basename(self.current_video_path)

                current_time = 0
                total_time = 0
                if self.vlc_media_player:
                    current_time = self.vlc_media_player.get_time() / 1000.0
                    total_time = self.vlc_media_player.get_length() / 1000.0

                self.mini_player.update_info(title, current_time, total_time)
            except (RuntimeError, AttributeError):
                pass

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'mini_player'):
            self.mini_player.cleanup()

