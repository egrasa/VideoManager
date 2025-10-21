"""UI Preview component: Grid, List and Timeline views for VideoManager."""

import tkinter as tk
from tkinter import ttk
import logging
from typing import List, Dict, Any, Callable
from pathlib import Path
import threading
from PIL import Image, ImageTk
from thumbnail_generator import ThumbnailGenerator
from thumbnail_loader import ThumbnailLoader

logger = logging.getLogger(__name__)

# Check if FFmpeg is available
FFMPEG_AVAILABLE = ThumbnailGenerator.check_ffmpeg_available()
if not FFMPEG_AVAILABLE:
    logger.warning("FFmpeg not found in PATH. Thumbnails will show placeholders."
                   " Install FFmpeg to see actual thumbnails.")


class UIPreview:
    """Displays videos in Grid, List, and Timeline views."""

    # Optimized breakpoints to show 5 columns on standard window size
    # Width thresholds and corresponding column counts
    GRID_COLS = {400: 2, 600: 3, 800: 5, 1200: 6, 1600: 7}

    # Category color mapping (RGB hex colors for visual distinction)
    CATEGORY_COLORS = {
        'public': "#D9F1DB",      # Light Green
        'private': "#FFA1A1",      # Light Red
        'ticket': "#FCE3BB",       # Light Orange
        'password': "#E0DA7A",     # Light Pink
        'special': "#E5B3EC",      # Light Purple
        'clip': "#AAF1EE",         # Light Cyan
        'other': "#C2BDBD",        # Light Gray
    }

    def __init__(self, parent: ttk.Frame, on_selection_callback: Callable[[int, Dict], None]):
        self.parent = parent
        self.on_selection_callback = on_selection_callback
        self.video_data = []
        self.selected_video_id = None
        self.last_grid_width = 0  # For tracking grid resize

        # Threading for timeline generation
        self.timeline_generation_thread = None
        self.timeline_stop_event = threading.Event()

        # Cache for generated timeline frames (persists during app lifetime)
        # Structure: {video_id: {'frames': [frame_paths], 'duration': duration_sec}}
        self.timeline_cache = {}

        # Initialize asynchronous thumbnail loader (3 worker threads)
        self.thumbnail_loader = ThumbnailLoader(max_workers=3)

        # Store references to thumbnail labels for updating
        self.thumbnail_labels: Dict[str, tk.Label] = {}  # {video_path: tk.Label}

        # Create notebook with tabs
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Grid View
        self.grid_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.grid_frame, text='  Grid View  ////  ')
        self._build_grid_view()

        # List View
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text='  List View  ////  ')
        self._build_list_view()

        # Timeline View
        self.timeline_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timeline_frame, text='  Timeline  ////  ')
        self._build_timeline_view()

    def _build_grid_view(self):
        """Build the grid view with responsive layout."""
        # Add legend frame at the top
        self._build_legend_frame(self.grid_frame)

        self.grid_canvas = tk.Canvas(self.grid_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.grid_frame, orient=tk.VERTICAL,
                                  command=self.grid_canvas.yview)

        self.grid_canvas.configure(yscrollcommand=scrollbar.set)
        self.grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.grid_scrollable = ttk.Frame(self.grid_canvas)
        self.grid_canvas.create_window((0, 0), window=self.grid_scrollable, anchor=tk.NW)

        # Bind mousewheel to canvas and make canvas focusable
        self.grid_canvas.bind('<MouseWheel>', self._on_mousewheel_grid)
        self.grid_canvas.bind('<Button-4>', self._on_mousewheel_grid)
        self.grid_canvas.bind('<Button-5>', self._on_mousewheel_grid)
        
        # Make canvas focusable and bind mousewheel on focus
        self.grid_canvas.bind('<Enter>', lambda e: self.grid_canvas.focus_set())
        self.grid_frame.bind('<Enter>', lambda e: self.grid_canvas.focus_set())

        # Bind resize event for dynamic grid recalculation
        self.grid_frame.bind('<Configure>', self._on_grid_frame_resize)

    def _build_legend_frame(self, parent_frame: ttk.Frame):
        """Build category legend frame.
        
        Args:
            parent_frame: Parent frame to add legend to (grid_frame or list_frame)
        """
        legend_frame = tk.Frame(parent_frame, bg='#F0F0F0', relief=tk.RIDGE, borderwidth=1)
        legend_frame.pack(fill=tk.X, padx=5, pady=5)

        # Title
        title_label = tk.Label(
            legend_frame,
            text='📋 Category Legend:',
            bg='#F0F0F0',
            fg='#333333',
            font=('Arial', 10, 'bold')
        )
        title_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Create color boxes for each category
        for category, color in self.CATEGORY_COLORS.items():
            # Color box
            color_box = tk.Frame(legend_frame, bg=color, relief=tk.SUNKEN, borderwidth=2,
                                width=20, height=20)
            color_box.pack(side=tk.LEFT, padx=3, pady=5)
            color_box.pack_propagate(False)

            # Category label
            cat_label = tk.Label(
                legend_frame,
                text=category.capitalize(),
                bg='#F0F0F0',
                fg='#333333',
                font=('Arial', 9)
            )
            cat_label.pack(side=tk.LEFT, padx=2, pady=5)

    def _on_grid_frame_resize(self, event):
        """Handle grid frame resize events to recalculate columns."""
        current_width = event.width

        # Only recalculate if width changed significantly (> 50px)
        if abs(current_width - self.last_grid_width) > 50:
            self.last_grid_width = current_width
            # Recalculate and redraw grid
            self._update_grid_view()

            # Update scrollregion for canvas
            self.grid_scrollable.update_idletasks()
            self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox('all'))

    def _build_list_view(self):
        """Build the list view with custom scrollable layout."""
        # Add legend frame at the top
        self._build_legend_frame(self.list_frame)
        
        # Create canvas with scrollbar for list view
        self.list_canvas = tk.Canvas(self.list_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL,
                                  command=self.list_canvas.yview)
        
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.list_scrollable = ttk.Frame(self.list_canvas)
        self.list_canvas.create_window((0, 0), window=self.list_scrollable, anchor=tk.NW)

        # Bind mousewheel to canvas and make canvas focusable
        self.list_canvas.bind('<MouseWheel>', self._on_mousewheel_list)
        self.list_canvas.bind('<Button-4>', self._on_mousewheel_list)
        self.list_canvas.bind('<Button-5>', self._on_mousewheel_list)
        
        # Make canvas focusable and bind mousewheel on focus
        self.list_canvas.bind('<Enter>', lambda e: self.list_canvas.focus_set())
        self.list_frame.bind('<Enter>', lambda e: self.list_canvas.focus_set())

        # Update scrollregion
        self.list_scrollable.bind('<Configure>', 
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox('all')))

    def _build_timeline_view(self):
        """Build the timeline view for frame thumbnails."""
        self.timeline_frame_container = ttk.Frame(self.timeline_frame)
        self.timeline_frame_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Progress label
        self.timeline_progress = ttk.Label(
            self.timeline_frame_container,
            text='Select a video to see timeline',
            foreground='gray'
        )
        self.timeline_progress.pack(pady=10)

        # Timeline canvas with scrollbar (vertical scroll with wrapping)
        canvas_frame = ttk.Frame(self.timeline_frame_container)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.timeline_canvas = tk.Canvas(
            canvas_frame,
            bg='#f0f0f0',
            highlightthickness=1,
            highlightbackground='#cccccc'
        )
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                                  command=self.timeline_canvas.yview)

        self.timeline_canvas.configure(yscrollcommand=scrollbar.set)
        self.timeline_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Frame for timeline images (with wrapping layout)
        self.timeline_scroll_frame = tk.Frame(self.timeline_canvas, bg='#f0f0f0')
        self.timeline_canvas.create_window((0, 0), window=self.timeline_scroll_frame, anchor='nw')

        # Bind configure event to update scroll region
        self.timeline_scroll_frame.bind('<Configure>', self._on_timeline_frame_configure)

        # Dictionary to store PhotoImage references
        self.timeline_photos = {}

    def _on_timeline_frame_configure(self, _event):
        """Update canvas scroll region when timeline frame changes size."""
        self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox('all'))

    def load_videos(self, video_data: List[Dict[str, Any]]):
        """Load videos into all views."""
        self.video_data = video_data
        # Defer grid update to ensure geometry is calculated
        self.parent.after(100, self._update_grid_view)
        self._update_list_view()

    def _update_grid_view(self):
        """Update grid view with current videos."""
        # Clear existing widgets
        for widget in self.grid_scrollable.winfo_children():
            widget.destroy()

        if not self.video_data:
            label = ttk.Label(self.grid_scrollable, text='No videos loaded')
            label.pack(pady=20)
            return

        # Force geometry update to get correct sizes
        self.parent.update_idletasks()

        # Also update grid canvas geometry
        self.grid_frame.update_idletasks()
        self.grid_canvas.update_idletasks()

        # Calculate columns dynamically based on available width
        # Try to get actual canvas width
        available_width = self.grid_canvas.winfo_width()

        if available_width < 50:  # Canvas not yet rendered properly
            # Fallback to grid frame width
            available_width = self.grid_frame.winfo_width()

        if available_width < 50:  # Still too small, use parent
            available_width = self.parent.winfo_width()

        if available_width < 50:  # Last resort
            available_width = 800

        # Account for scrollbar width (~17px) and margins
        usable_width = available_width - 30

        # Each column needs: image (145) + padding (10) = 155px minimum
        # Larger thumbnails while maintaining 4 per row on standard window
        thumbnail_width = 145
        column_spacing = 10  # padx=5 on both sides = 10 total
        column_width = thumbnail_width + column_spacing

        # Calculate how many complete columns fit
        cols = max(1, usable_width // column_width)

        # Determine maximum columns allowed based on window width (breakpoints)
        width = self.grid_frame.winfo_width()
        if width < 1:
            width = available_width

        max_cols = 4  # Default maximum
        for threshold, col_count in sorted(self.GRID_COLS.items()):
            if width >= threshold:
                max_cols = col_count

        # Don't exceed maximum, but allow up to what fits
        cols = min(cols, max_cols)

        # Configure grid column weights for equal distribution
        for col in range(cols):
            self.grid_scrollable.columnconfigure(col, weight=1)

        # Create grid layout
        for idx, video in enumerate(self.video_data):
            row = idx // cols
            col = idx % cols

            # Get category and corresponding color
            category = video.get('category', 'other')
            bg_color = self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS['other'])

            # Use tk.Frame to support background color
            frame = tk.Frame(self.grid_scrollable, relief=tk.RAISED, borderwidth=2, bg=bg_color)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky='ew')

            # Generate and display thumbnail (145x82 - larger for better visibility)
            thumb_label = tk.Label(frame, background=bg_color, width=145, height=82)
            thumb_label.pack(padx=5, pady=5)

            # Generate thumbnail in background
            video_path = video.get('path', '')
            if video_path and Path(video_path).exists():
                if FFMPEG_AVAILABLE:
                    # Queue thumbnail for asynchronous loading
                    self.thumbnail_loader.queue_thumbnail(
                        video_path,
                        lambda path, photo,
                        lbl=thumb_label: self._on_thumbnail_loaded(path, photo, lbl)
                    )
                    # Show placeholder while loading
                    placeholder = self.thumbnail_loader.get_placeholder_image()
                    thumb_label.config(image=placeholder, text='Loading...')
                    thumb_label.image = placeholder
                    self.thumbnail_labels[video_path] = thumb_label
                else:
                    # FFmpeg not available - show placeholder
                    filename = Path(video_path).name
                    thumb_label.config(text=filename, bg=bg_color,
                                       foreground='white', font=('Arial', 8))
            else:
                thumb_label.config(text='[Invalid path]', foreground='white')

            # Title
            title_text = video.get('title', 'Unknown')[:25]
            title_label = ttk.Label(frame, text=title_text, background=bg_color,
                                    justify=tk.CENTER, wraplength=150)
            title_label.pack(pady=5)

            # Bind click
            frame.bind('<Button-1>', lambda e, vid=video['id']: self._on_grid_selection(vid))
            thumb_label.bind('<Button-1>', lambda e, vid=video['id']: self._on_grid_selection(vid))
            title_label.bind('<Button-1>', lambda e, vid=video['id']: self._on_grid_selection(vid))

        self.grid_scrollable.update_idletasks()
        self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox('all'))

    def _update_list_view(self):
        """Update list view with current videos."""
        # Clear existing items
        for widget in self.list_scrollable.winfo_children():
            widget.destroy()

        if not self.video_data:
            label = ttk.Label(self.list_scrollable, text='No videos loaded')
            label.pack(pady=20)
            return

        # Add videos as custom rows
        for video in self.video_data:
            category = video.get('category', 'other')
            bg_color = self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS['other'])

            # Create row frame with category color background
            row_frame = tk.Frame(self.list_scrollable, bg=bg_color, relief=tk.RAISED, borderwidth=1)
            row_frame.pack(fill=tk.X, padx=3, pady=2)

            # Format extension
            ext = video['path'].split('.')[-1].upper() if '.' in video['path'] else '?'
            
            # Format rating
            rating_stars = '★' * video.get('rating', 0) + '☆' * (5 - video.get('rating', 0))
            
            # Format notes preview
            notes_preview = video.get('notes', '')[:40]

            # Create text for row
            title = video.get('title', 'Unknown')
            duration = video.get('duration', '')
            
            # Format text with columns
            row_text = f"{ext:5} | {title:40} | {duration:10} | {category:10} | {rating_stars:5} | {notes_preview}"

            # Create label with formatted text
            label = tk.Label(
                row_frame,
                text=row_text,
                bg=bg_color,
                background=bg_color,
                fg='#333333',
                font=('Courier', 9),
                anchor=tk.W,
                justify=tk.LEFT,
                padx=10,
                pady=5
            )
            label.pack(fill=tk.X)

            # Bind click event to label for selection
            label.bind('<Button-1>', lambda e, vid=video['id']: self._on_list_row_click(vid))
            row_frame.bind('<Button-1>', lambda e, vid=video['id']: self._on_list_row_click(vid))

    def _generate_timeline_threaded(self, video: Dict[str, Any]):
        """Generate timeline frames in a separate thread."""
        video_id = video.get('id')

        # Check if timeline is already cached
        if video_id in self.timeline_cache:
            cached_data = self.timeline_cache[video_id]
            logger.info("Loading cached timeline for video %d", video_id)
            # Display cached frames immediately without regeneration
            self._display_cached_timeline(video, cached_data['frames'], cached_data['duration'])
            return

        # Stop any previous thread
        self.timeline_stop_event.set()
        if self.timeline_generation_thread and self.timeline_generation_thread.is_alive():
            self.timeline_generation_thread.join(timeout=1.0)

        # Clear previous frames and timeline data
        for widget in self.timeline_scroll_frame.winfo_children():
            widget.destroy()
        self.timeline_photos.clear()

        # Reset stop event and start new thread
        self.timeline_stop_event.clear()
        self.timeline_generation_thread = threading.Thread(
            target=self._timeline_generation_worker,
            args=(video,),
            daemon=True
        )
        self.timeline_generation_thread.start()

    def _timeline_generation_worker(self, video: Dict[str, Any]):
        """Worker thread that generates timeline frames."""
        try:
            self._load_timeline(video)
        except (OSError, ValueError, KeyError) as e:
            logger.error("Error in timeline generation thread: %s", e)

    def _load_timeline(self, video: Dict[str, Any]):
        """Load and display timeline frames for a video. Called from worker thread."""
        if not FFMPEG_AVAILABLE:
            self.parent.after(0, self._update_timeline_ui, video, [], 0)
            return

        video_path = video.get('path', '')
        if not video_path or not Path(video_path).exists():
            self.parent.after(0, self._update_timeline_ui, video, [], 0)
            return

        # Show loading message via UI thread
        self.parent.after(0, lambda: self.timeline_progress.config(
            text='Generating timeline frames...',
            foreground='#2c3e50'
        ))

        try:
            # Generate timeline frames progressively
            frame_paths = []
            calculated_duration = 0  # Store duration for later use
            failed_frames = []  # Track failed frames for logging

            # Get video duration first
            duration = ThumbnailGenerator.get_video_duration(video_path)
            if duration and duration > 0:
                calculated_duration = duration
                # Calculate number of frames: 60 frames per hour of duration
                # For a 30 min video: 30 frames, 20 min: 20 frames, 1 hour: 60 frames
                duration_minutes = duration / 60
                num_frames = max(1, round(duration_minutes))  # At least 1 frame
                num_frames = min(num_frames, 120)  # Cap at 120 frames max

                for i in range(num_frames):
                    # Check if thread should stop
                    if self.timeline_stop_event.is_set():
                        logger.info("Timeline generation cancelled by user")
                        return

                    # Calculate timestamp
                    prog = 0.05 + (i / (num_frames - 1)) * 0.9 if num_frames > 1 else 0.5
                    timestamp = duration * prog

                    # Generate frame (may fail due to timeout)
                    frame_path = ThumbnailGenerator.generate_single_timeline_frame(
                        video_path,
                        frame_index=i,
                        timestamp=timestamp
                    )
                    if frame_path:
                        frame_paths.append(frame_path)
                        # Update UI immediately with the new frame (progressive display)
                        self.parent.after(0, self._add_timeline_frame, video, frame_path, i,
                                          calculated_duration, num_frames)
                    else:
                        failed_frames.append(i)
                        logger.warning("Failed to generate frame %d from %s", i,
                                       Path(video_path).name)

                    # Update progress via UI thread
                    progress = int(((i + 1) / num_frames) * 100)
                    self.parent.after(0, lambda p=i+1, max_f=num_frames, pr=progress,
                                      fail=len(failed_frames):
                        self.timeline_progress.config(
                            text=f'Generating timeline frames ({p}/{max_f})... {pr}%'
                            f'{" (failures: " + str(fail) + ")" if fail > 0 else ""}',
                            foreground='#2c3e50'
                        )
                    )
            else:
                # Fallback if duration detection fails - use default 8 frames
                frame_paths = ThumbnailGenerator.generate_timeline_frames(
                    video_path,
                    num_frames=8
                )
                # Update UI with all generated frames
                self.parent.after(0, self._update_timeline_ui, video,
                                  frame_paths, calculated_duration)
                return

            # Cache the generated frames for this video
            video_id = video.get('id')
            if video_id and frame_paths:
                self.timeline_cache[video_id] = {
                    'frames': frame_paths,
                    'duration': calculated_duration
                }
                logger.info("Cached %d timeline frames for video %d", len(frame_paths), video_id)

            # Update UI with final message
            if frame_paths:
                if calculated_duration > 0:
                    duration_str = f"{int(calculated_duration // 60)}:{int(
                        calculated_duration % 60):02d}"
                else:
                    duration_str = "0:00"
                self.parent.after(0, lambda frames=len(frame_paths), dur_str=duration_str:
                    self.timeline_progress.config(
                        text=f"Timeline ({frames} frames) - Duration: {dur_str}",
                        foreground='#27ae60'
                    )
                )
            else:
                self.parent.after(0, lambda:
                    self.timeline_progress.config(
                        text='Could not generate timeline frames',
                        foreground='#e67e22'
                    )
                )

        except (OSError, ValueError, KeyError) as e:
            logger.error("Error loading timeline: %s", e)
            self.parent.after(0, lambda err=str(e): self.timeline_progress.config(
                text=f'Error: {err[:50]}',
                foreground='#ff6b6b'
            ))

    def _display_cached_timeline(self, _video: Dict[str, Any], frame_paths: List[str],
                                 duration_sec: float):
        """Display cached timeline frames without regeneration. Called from UI thread."""
        # Clear previous frames
        for widget in self.timeline_scroll_frame.winfo_children():
            widget.destroy()
        self.timeline_photos.clear()

        if not frame_paths:
            self.timeline_progress.config(
                text='No cached frames available',
                foreground='#e67e22'
            )
            return

        # Display all cached frames with timestamps
        cols_per_row = 7
        for i, frame_path in enumerate(frame_paths):
            try:
                if not Path(frame_path).exists():
                    logger.warning("Cached frame file not found: %s", frame_path)
                    continue

                img = Image.open(frame_path)
                photo = ImageTk.PhotoImage(img)

                # Calculate timestamp
                if duration_sec > 0:
                    progress = 0.05 + (i / (len(frame_paths) - 1)) * 0.9 if len(
                        frame_paths) > 1 else 0.5
                    timestamp_sec = duration_sec * progress
                    minutes = int(timestamp_sec // 60)
                    seconds = int(timestamp_sec % 60)
                    timestamp_str = f"{minutes}:{seconds:02d}"
                else:
                    timestamp_str = "0:00"

                # Create container for frame and timestamp
                frame_container = tk.Frame(
                    self.timeline_scroll_frame,
                    bg='#f0f0f0'
                )
                row = i // cols_per_row
                col = i % cols_per_row
                frame_container.grid(row=row, column=col, padx=2, pady=5)

                # Create frame button
                frame_btn = tk.Label(
                    frame_container,
                    image=photo,
                    bg='#f0f0f0',
                    cursor='hand2',
                    relief=tk.RAISED,
                    borderwidth=1
                )
                frame_btn.pack()

                # Add timestamp label
                time_label = tk.Label(
                    frame_container,
                    text=timestamp_str,
                    bg='#f0f0f0',
                    fg='#2c3e50',
                    font=('Arial', 8, 'bold')
                )
                time_label.pack()

                # Keep reference
                self.timeline_photos[f"frame_{i}"] = photo

            except (OSError, ValueError) as e:
                logger.warning("Error loading cached frame: %s", e)

        # Update canvas scroll region
        self.timeline_scroll_frame.update_idletasks()
        self.timeline_canvas.configure(
            scrollregion=self.timeline_canvas.bbox('all')
        )

        # Display completion message
        if duration_sec > 0:
            duration_str = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}"
        else:
            duration_str = "0:00"
        self.timeline_progress.config(
            text=f"Timeline ({len(frame_paths)} frames - cached) - Duration: {duration_str}",
            foreground='#27ae60'
        )

    def _add_timeline_frame(self, _video: Dict[str, Any], frame_path: str, frame_index: int,
                           duration_sec: float, total_frames: int):
        """Add a single timeline frame to the UI progressively. Called from UI thread."""
        try:
            if not Path(frame_path).exists():
                return

            img = Image.open(frame_path)
            photo = ImageTk.PhotoImage(img)

            # Calculate timestamp
            if duration_sec > 0:
                progress = 0.05 + (frame_index / (total_frames - 1)
                                   ) * 0.9 if total_frames > 1 else 0.5
                timestamp_sec = duration_sec * progress
                minutes = int(timestamp_sec // 60)
                seconds = int(timestamp_sec % 60)
                timestamp_str = f"{minutes}:{seconds:02d}"
            else:
                timestamp_str = "0:00"

            # Create container for frame and timestamp
            frame_container = tk.Frame(
                self.timeline_scroll_frame,
                bg='#f0f0f0'
            )
            # Grid layout to allow wrapping
            cols_per_row = 7
            row = frame_index // cols_per_row
            col = frame_index % cols_per_row
            frame_container.grid(row=row, column=col, padx=2, pady=5)

            # Create frame button
            frame_btn = tk.Label(
                frame_container,
                image=photo,
                bg='#f0f0f0',
                cursor='hand2',
                relief=tk.RAISED,
                borderwidth=1
            )
            frame_btn.pack()

            # Add timestamp label below frame
            time_label = tk.Label(
                frame_container,
                text=timestamp_str,
                bg='#f0f0f0',
                fg='#2c3e50',
                font=('Arial', 8, 'bold')
            )
            time_label.pack()

            # Keep reference to prevent garbage collection
            self.timeline_photos[f"frame_{frame_index}"] = photo

            # Update canvas scroll region
            self.timeline_scroll_frame.update_idletasks()
            self.timeline_canvas.configure(
                scrollregion=self.timeline_canvas.bbox('all')
            )

        except (OSError, ValueError) as e:
            logger.warning("Error adding timeline frame: %s", e)

    def _update_timeline_ui(self, video: Dict[str, Any], frame_paths: List[str],
                            duration_sec: float):
        """Update timeline UI with generated frames. Called from UI thread."""
        # Clear previous frames
        for widget in self.timeline_scroll_frame.winfo_children():
            widget.destroy()
        self.timeline_photos.clear()

        if not FFMPEG_AVAILABLE:
            self.timeline_progress.config(
                text='FFmpeg not available for timeline generation',
                foreground='#ff6b6b'
            )
            return

        video_path = video.get('path', '')
        if not video_path:
            self.timeline_progress.config(
                text='Video file not found',
                foreground='#ff6b6b'
            )
            return

        if frame_paths:
            # Use calculated duration if available
            if duration_sec > 0:
                duration_float = duration_sec
            else:
                duration = video.get('duration', 0)
                try:
                    duration_float = float(duration) if isinstance(duration, str) else duration
                except (ValueError, TypeError):
                    duration_float = 0

            # Load and display frames with timestamps (wrapped layout with grid)
            cols_per_row = 7  # Number of frames per row
            for i, frame_path in enumerate(frame_paths):
                try:
                    img = Image.open(frame_path)
                    photo = ImageTk.PhotoImage(img)

                    # Calculate timestamp for this frame
                    if duration_float > 0:
                        progress = 0.05 + (i / (len(frame_paths) - 1)) * 0.9 if len(
                            frame_paths) > 1 else 0.5
                        timestamp_sec = duration_float * progress
                        minutes = int(timestamp_sec // 60)
                        seconds = int(timestamp_sec % 60)
                        timestamp_str = f"{minutes}:{seconds:02d}"
                    else:
                        timestamp_str = "0:00"

                    # Create container for frame and timestamp
                    frame_container = tk.Frame(
                        self.timeline_scroll_frame,
                        bg='#f0f0f0'
                    )
                    # Use grid layout to allow wrapping
                    row = i // cols_per_row
                    col = i % cols_per_row
                    frame_container.grid(row=row, column=col, padx=2, pady=5)

                    # Create frame button
                    frame_btn = tk.Label(
                        frame_container,
                        image=photo,
                        bg='#f0f0f0',
                        cursor='hand2',
                        relief=tk.RAISED,
                        borderwidth=1
                    )
                    frame_btn.pack()

                    # Add timestamp label below frame
                    time_label = tk.Label(
                        frame_container,
                        text=timestamp_str,
                        bg='#f0f0f0',
                        fg='#2c3e50',
                        font=('Arial', 8, 'bold')
                    )
                    time_label.pack()

                    # Keep reference to prevent garbage collection
                    self.timeline_photos[f"frame_{i}"] = photo

                except (OSError, ValueError) as e:
                    logger.warning("Error loading timeline frame: %s", e)

            # Update canvas scroll region
            self.timeline_scroll_frame.update_idletasks()
            self.timeline_canvas.configure(
                scrollregion=self.timeline_canvas.bbox('all')
            )

            # Display final message with duration
            if duration_float > 0:
                duration_str = f"{int(duration_float // 60)}:{int(duration_float % 60):02d}"
            else:
                duration_str = "0:00"
            self.timeline_progress.config(
                text=f"Timeline ({len(frame_paths)} frames) - Duration: {duration_str}",
                foreground='#27ae60'
            )
        else:
            self.timeline_progress.config(
                text='Could not generate timeline frames',
                foreground='#e67e22'
            )

    def _on_grid_selection(self, video_id: int):
        """Handle grid view click."""
        self.selected_video_id = video_id
        video = next((v for v in self.video_data if v['id'] == video_id), None)
        if video:
            # Load timeline for this video (threaded)
            self._generate_timeline_threaded(video)
            # Call the selection callback
            self.on_selection_callback(video_id, video)

    def _on_list_row_click(self, video_id: int):
        """Handle click on list row."""
        self.selected_video_id = video_id
        video = next((v for v in self.video_data if v['id'] == video_id), None)
        if video:
            # Load timeline for this video (threaded)
            self._generate_timeline_threaded(video)
            # Call the selection callback
            self.on_selection_callback(video_id, video)

    def _on_mousewheel_grid(self, event):
        """Handle mousewheel scroll in grid view."""
        # Check if grid canvas is visible and has focus
        try:
            if not self.grid_canvas.winfo_exists():
                return
            
            # Determine scroll direction
            # Windows: event.delta (positive = up, negative = down)
            # Linux/Unix: event.num (4 = up, 5 = down)
            if event.num == 5 or event.delta < 0:
                self.grid_canvas.yview_scroll(3, 'units')
            elif event.num == 4 or event.delta > 0:
                self.grid_canvas.yview_scroll(-3, 'units')
            
            # Return 'break' to prevent event propagation
            return 'break'
        except tk.TclError:
            pass

    def _on_mousewheel_list(self, event):
        """Handle mousewheel scroll in list view."""
        # Check if list canvas is visible and has focus
        try:
            if not self.list_canvas.winfo_exists():
                return
            
            # Determine scroll direction
            # Windows: event.delta (positive = up, negative = down)
            # Linux/Unix: event.num (4 = up, 5 = down)
            if event.num == 5 or event.delta < 0:
                self.list_canvas.yview_scroll(3, 'units')
            elif event.num == 4 or event.delta > 0:
                self.list_canvas.yview_scroll(-3, 'units')
            
            # Return 'break' to prevent event propagation
            return 'break'
        except tk.TclError:
            pass

    def _on_thumbnail_loaded(self, video_path: str, photo, label: tk.Label):
        """Callback when thumbnail is loaded asynchronously.
        
        Args:
            video_path: Path to the video file
            photo: PhotoImage object or None if failed
            label: tk.Label widget to update
        """
        try:
            # Check if widget still exists before updating
            if not label.winfo_exists():
                logger.debug('Label widget no longer exists, skipping update')
                return

            if photo:
                # Schedule update on main thread
                self.parent.after(0, lambda: self._update_thumbnail_on_main_thread(label, photo))
                logger.debug('Thumbnail loaded for: %s', Path(video_path).name)
            else:
                # Thumbnail generation failed
                self.parent.after(0, lambda: label.config(text='[No thumbnail]', foreground='white')
                                          if label.winfo_exists() else None)
                logger.warning('Failed to load thumbnail for: %s', video_path)
        except (RuntimeError, ValueError) as e:
            logger.error('Error in thumbnail callback: %s', e)

    def _update_thumbnail_on_main_thread(self, label: tk.Label, photo):
        """Update label with thumbnail image on the main thread.
        
        Args:
            label: tk.Label widget to update
            photo: PhotoImage to display
        """
        try:
            # Check if widget still exists
            if not label.winfo_exists():
                logger.debug('Label widget no longer exists, skipping thumbnail update')
                return

            label.config(image=photo, text='')
            label.image = photo  # Keep reference to prevent garbage collection
        except tk.TclError as e:
            logger.debug('Label widget no longer exists: %s', e)

    def update_categories(self, categories: List[str]):
        """Update available categories (called by app)."""
        # Categories are fixed in requirements

    def generate_timeline(self, video_path: str):
        """Generate timeline thumbnails for video (stub - FFmpeg integration needed)."""
        self.timeline_progress.config(text=f'Timeline for: {video_path}')

    def cleanup(self):
        """Cleanup resources before closing."""
        logger.info('Cleaning up UIPreview resources')
        # Shutdown thumbnail loader
        if hasattr(self, 'thumbnail_loader'):
            self.thumbnail_loader.shutdown()
        # Stop timeline generation
        if hasattr(self, 'timeline_stop_event'):
            self.timeline_stop_event.set()
