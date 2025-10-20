"""UIEdit component: editor for video metadata."""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class UIEdit:
    """Panel for editing video metadata (category, rating, notes)."""

    DEFAULT_CATEGORIES = [
        'public', 'private', 'ticket', 'password', 'special', 'clip', 'other'
    ]

    def __init__(self, parent, on_save_callback):
        """Initialize the editor panel.
        
        Args:
            parent: tk container for the editor
            on_save_callback: callable(video_id, updated_fields)
        """
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.video_id = None

        self.title_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.rating_var = tk.IntVar(value=0)

        self.frame = ttk.Frame(self.parent, padding=8)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        ttk.Label(self.frame, text='Edit Video Details', font=(None, 12, 'bold')).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 10)
        )

        # Title (read-only)
        ttk.Label(self.frame, text='Title:').grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(self.frame, textvariable=self.title_var, state='readonly', width=40).grid(
            row=1, column=1, sticky='we', padx=5
        )

        # Path (read-only)
        ttk.Label(self.frame, text='Path:').grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(self.frame, textvariable=self.path_var, state='readonly', width=40).grid(
            row=2, column=1, sticky='we', padx=5
        )

        # Category combobox
        ttk.Label(self.frame, text='Category:').grid(row=3, column=0, sticky='w', pady=5)
        self.categories = list(self.DEFAULT_CATEGORIES)
        self.category_combobox = ttk.Combobox(
            self.frame, textvariable=self.category_var, values=self.categories,
            state='readonly', width=37
        )
        self.category_combobox.grid(row=3, column=1, sticky='we', padx=5)

        # Rating (1-5 stars)
        ttk.Label(self.frame, text='Rating:').grid(row=4, column=0, sticky='w', pady=5)
        stars_frame = ttk.Frame(self.frame)
        stars_frame.grid(row=4, column=1, sticky='w', padx=5)
        self.star_buttons = []
        for i in range(1, 6):
            btn = ttk.Button(
                stars_frame, text='☆', width=3,
                command=lambda v=i: self._on_star_click(v)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.star_buttons.append(btn)

        # Notes
        ttk.Label(self.frame, text='Notes:').grid(row=5, column=0, sticky='nw', pady=5)
        self.notes_text = tk.Text(self.frame, height=8, width=40)
        self.notes_text.grid(row=5, column=1, sticky='we', padx=5)

        # Buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=6, column=1, sticky='e', pady=(10, 0))
        self.save_btn = ttk.Button(btn_frame, text='Save', command=self._on_save)
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        self.cancel_btn = ttk.Button(btn_frame, text='Cancel', command=self._on_cancel)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        self.frame.columnconfigure(1, weight=1)
        self._set_enabled(False)

    def load_video(self, video_id, video_row):
        """Load video data into the editor.
        
        Args:
            video_id: Database video ID
            video_row: Tuple from database or dict with video data
        """
        self.video_id = video_id

        # Handle both dict and tuple formats
        if isinstance(video_row, dict):
            data = video_row
        else:
            # Assume tuple: (id, filename, path, title, duration, category, rating, notes, ...)
            try:
                data = {
                    'title': video_row[3] if len(video_row) > 3 else '',
                    'path': video_row[2] if len(video_row) > 2 else '',
                    'category': video_row[5] if len(video_row) > 5 else 'public',
                    'rating': video_row[6] if len(video_row) > 6 else 0,
                    'notes': video_row[7] if len(video_row) > 7 else '',
                }
            except (IndexError, TypeError):
                logger.exception('Unexpected video_row format')
                return

        self.title_var.set(data.get('title', ''))
        self.path_var.set(data.get('path', ''))

        category = data.get('category', 'public')
        if category and category not in self.categories:
            self.update_categories(self.categories + [category])
        self.category_var.set(category)

        rating = int(data.get('rating', 0) or 0)
        self.rating_var.set(rating)
        self._refresh_stars()

        self.notes_text.delete('1.0', tk.END)
        self.notes_text.insert('1.0', data.get('notes', '') or '')

        self._set_enabled(True)

    def update_categories(self, categories_list):
        """Update available categories."""
        merged = []
        for c in (self.DEFAULT_CATEGORIES + list(categories_list)):
            if c not in merged:
                merged.append(c)
        self.categories = merged
        self.category_combobox['values'] = self.categories

    def _set_enabled(self, enabled: bool):
        """Enable or disable all editor controls."""
        state = 'normal' if enabled else 'disabled'
        for btn in self.star_buttons:
            btn.config(state=state)
        self.category_combobox.config(state='readonly' if enabled else 'disabled')
        self.notes_text.config(state=state)
        self.save_btn.config(state=state)
        self.cancel_btn.config(state=state)

    def _on_star_click(self, value: int):
        """Handle star rating click."""
        self.rating_var.set(value)
        self._refresh_stars()

    def _refresh_stars(self):
        """Update star display based on rating."""
        rating = self.rating_var.get()
        for i, btn in enumerate(self.star_buttons, start=1):
            btn.config(text='★' if i <= rating else '☆')

    def _on_save(self):
        """Save changes and call callback."""
        if not self.video_id:
            logger.warning('Save called without video_id')
            return

        updated = {
            'title': self.title_var.get(),
            'category': self.category_var.get(),
            'rating': self.rating_var.get(),
            'notes': self.notes_text.get('1.0', 'end').rstrip('\n'),
        }

        try:
            self.on_save_callback(self.video_id, updated)
            logger.info('Saved video %d', self.video_id)
        except (RuntimeError, ValueError, OSError):
            logger.exception('Error calling on_save_callback')


    def _on_cancel(self):
        """Cancel editing (clear selection)."""
        self.video_id = None
        self.title_var.set('')
        self.path_var.set('')
        self.category_var.set('')
        self.rating_var.set(0)
        self.notes_text.delete('1.0', tk.END)
        self._set_enabled(False)

    def cancel(self):
        """Public API to cancel (used by app)."""
        self._on_cancel()
