"""Search module for VideoManager.

Provides search and filter functionality to find videos by title, filename,
category, rating, notes, and other metadata.
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable, List, Dict, Any

logger = logging.getLogger(__name__)


class UISearch:
    """Search interface for finding and filtering videos."""

    def __init__(self, parent, on_search_results: Callable[[List[Dict[str, Any]]], None]):
        """Initialize search UI.
        
        Args:
            parent: Parent tkinter widget
            on_search_results: Callback function when search results are found
                              Receives list of video dictionaries
        """
        self.parent = parent
        self.on_search_results = on_search_results
        self.search_history: List[str] = []
        self.max_history = 10
        self._search_timer = None
        self._on_search_params = None

        self._build_ui()

    def _build_ui(self):
        """Build search interface."""
        # Search frame
        search_frame = ttk.LabelFrame(self.parent, text='🔍 Search Videos', padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search input with history dropdown
        input_frame = ttk.Frame(search_frame)
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text='Search:').pack(side=tk.LEFT, padx=5)

        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_input)

        self.search_entry = ttk.Combobox(
            input_frame,
            textvariable=self.search_var,
            width=20,
            values=self.search_history,
            state='normal'
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<Return>', self._on_search_pressed)

        ttk.Button(
            input_frame,
            text='🔍 Search',
            command=self._perform_search
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            input_frame,
            text='✕ Clear',
            command=self._clear_search
        ).pack(side=tk.LEFT, padx=5)

        # Filter options frame
        #filter_frame = ttk.LabelFrame(search_frame, text='Filter By', padding=5)
        #filter_frame.pack(fill=tk.X, pady=10)

        # Category filter
        #cat_frame = ttk.Frame(filter_frame)
        #cat_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(input_frame, text='Category:').pack(side=tk.LEFT, padx=5)

        self.category_var = tk.StringVar(value='All')
        self.category_combo = ttk.Combobox(
            input_frame,
            textvariable=self.category_var,
            values=['All', 'public', 'private', 'ticket', 'password', 'special', 'clip', 'other'],
            state='readonly',
            width=12
        )
        self.category_combo.pack(side=tk.LEFT, padx=5)
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self._perform_search())

        # Rating filter
        rating_frame = ttk.Frame(input_frame)
        rating_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(input_frame, text='Min Rating:').pack(side=tk.LEFT, padx=5)

        self.rating_var = tk.IntVar(value=0)
        self.rating_var.trace('w', lambda *_: self._perform_search())
        self.rating_spin = ttk.Spinbox(
            input_frame,
            from_=0,
            to=5,
            textvariable=self.rating_var,
            width=5
        )
        self.rating_spin.pack(side=tk.LEFT, padx=5)

        # Search mode
        #mode_frame = ttk.Frame(filter_frame)
        #mode_frame.pack(side=tk.LEFT, padx=10)

        ttk.Label(input_frame, text=' ').pack(side=tk.LEFT, padx=5)

        self.search_mode_var = tk.StringVar(value='all')
        search_modes = [
            ('Filename', 'filename'),
            ('Notes', 'notes'),
            ('All Fields', 'all')
        ]

        for text, value in search_modes:
            ttk.Radiobutton(
                input_frame,
                text=text,
                variable=self.search_mode_var,
                value=value,
                command=self._perform_search
            ).pack(side=tk.LEFT, padx=5)

        # Search results info
        self.info_label = ttk.Label(
            input_frame,
            text='Enter search term or use filters',
            foreground='gray'
        )
        self.info_label.pack(fill=tk.X, side='right', padx=5, pady=5)

    def _on_search_input(self, *_):
        """Live search as user types."""
        # Only trigger on significant changes to avoid too many searches
        search_text = self.search_var.get()
        if len(search_text) >= 2 or len(search_text) == 0:
            # Debounce with a timer
            if self._search_timer:
                self.parent.after_cancel(self._search_timer)
            self._search_timer = self.parent.after(300, self._perform_search)

    def _on_search_pressed(self, *_):
        """Handle Enter key press."""
        self._perform_search()

    def _perform_search(self):
        """Execute search with current filters."""
        search_text = self.search_var.get().strip()
        category = self.category_var.get()
        min_rating = self.rating_var.get()
        search_mode = self.search_mode_var.get()

        # Build search parameters
        search_params = {
            'query': search_text,
            'category': None if category == 'All' else category,
            'min_rating': min_rating if min_rating > 0 else 0,
            'search_mode': search_mode
        }

        # Add to search history
        if search_text and search_text not in self.search_history:
            self.search_history.insert(0, search_text)
            self.search_history = self.search_history[:self.max_history]
            self.search_entry['values'] = self.search_history
            logger.info('Added to search history: %s', search_text)

        # Trigger callback with search parameters
        # The parent app will handle the actual search
        if self._on_search_params:
            self._on_search_params(search_params)

        logger.info('Search executed: query="%s", category=%s, min_rating=%d, mode=%s',
                   search_text, category, min_rating, search_mode)

    def _clear_search(self):
        """Clear search and show all videos."""
        self.search_var.set('')
        self.category_var.set('All')
        self.rating_var.set(0)
        self.search_mode_var.set('all')
        self._perform_search()
        self.info_label.config(text='Search cleared - showing all videos')
        logger.info('Search cleared')

    def set_search_callback(self, callback):
        """Set the callback for search results.
        
        Args:
            callback: Function that receives search parameters dict
        """
        self._on_search_params = callback

    def update_info(self, total_videos: int, results_count: int):
        """Update search results info label.
        
        Args:
            total_videos: Total videos in database
            results_count: Number of results found
        """
        if results_count == total_videos:
            text = f'Showing all {total_videos} videos'
        else:
            text = f'Found {results_count} of {total_videos} videos'
        self.info_label.config(text=text, foreground='black')
