"""SQLite database module for VideoManager.

Manages video metadata storage, retrieval, and updates.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from thumbnail_generator import ThumbnailGenerator


class VideoDatabase:
    """ Video metadata database handler."""
    SUPPORTED_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.webm'}

    def __init__(self, db_path: str = 'videos.db'):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def init_db(self):
        """Initialize database with required tables."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                title TEXT,
                duration TEXT,
                category TEXT DEFAULT 'public',
                rating INTEGER DEFAULT 0,
                notes TEXT,
                thumbnail BLOB,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def add_video(self, filepath: str, category: str = 'public',
                  tags: str = '', duration: Optional[str] = None,
                  title: Optional[str] = None) -> Optional[int]:
        """Insert a video into the database.
        
        Args:
            filepath: Full path to video file
            category: Video category (public, private, ticket, password, clip, special)
            tags: Space-separated tags
            duration: Video duration (auto-detected if None)
            title: Display title (filename if None)
        
        Returns:
            video_id if successful, None otherwise
        """
        if not os.path.exists(filepath):
            return None

        filename = os.path.basename(filepath)
        if title is None:
            title = os.path.splitext(filename)[0]

        # Auto-detect duration if not provided
        if duration is None or duration == '':
            try:
                duration_sec = ThumbnailGenerator.get_video_duration(filepath)
                if duration_sec and duration_sec > 0:
                    minutes = int(duration_sec // 60)
                    seconds = int(duration_sec % 60)
                    duration = f"{minutes}:{seconds:02d}"
                else:
                    duration = ''
            except (OSError, ValueError, TypeError):
                duration = ''

        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO videos (filename, path, title, duration, category, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filename, filepath, title, duration or '', category, tags))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def check_duplicate_video(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Check if a video with the same name and extension already exists.
        
        Args:
            filepath: Full path to video file
        
        Returns:
            Dictionary with existing video info if found, None otherwise
        """
        if not os.path.exists(filepath):
            return None
        
        filename = os.path.basename(filepath)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM videos WHERE filename = ?
        ''', (filename,))
        
        result = cursor.fetchone()
        if result:
            return self._row_to_dict(result, cursor)
        
        return None

    def get_all_videos(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all videos (optionally filtered by category)."""
        cursor = self.conn.cursor()
        if category:
            cursor.execute('SELECT * FROM videos WHERE category = ?', (category,))
        else:
            cursor.execute('SELECT * FROM videos ORDER BY added_date DESC')

        rows = cursor.fetchall()
        return [self._row_to_dict(row, cursor) for row in rows]

    def get_video(self, video_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single video by ID."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        return self._row_to_dict(row, cursor) if row else None

    def update_video(self, video_id: int, **kwargs) -> bool:
        """Update video metadata.
        
        Allowed fields: title, category, rating, notes, duration
        """
        allowed_fields = {'title', 'category', 'rating', 'notes', 'duration'}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [video_id]

        cursor = self.conn.cursor()
        cursor.execute(f'UPDATE videos SET {set_clause} WHERE id = ?', values)
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_video(self, video_id: int) -> bool:
        """Delete a video from the database."""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def search_videos(self, query: str = '', category: Optional[str] = None,
                     min_rating: int = 0, search_mode: str = 'all') -> List[Dict[str, Any]]:
        """Search videos by various criteria.
        
        Args:
            query: Search text (default: empty = search all)
            category: Filter by category (None = all categories)
            min_rating: Minimum rating filter (0 = all)
            search_mode: 'title_filename', 'filename', 'title', 'notes', 'all'
        
        Returns:
            List of matching video dictionaries
        """
        cursor = self.conn.cursor()
        
        # Build query based on search mode
        where_conditions = []
        params = []
        
        if query:
            query_param = f'%{query}%'
            
            if search_mode == 'title_filename':
                where_conditions.append('(title LIKE ? OR filename LIKE ?)')
                params.extend([query_param, query_param])
            elif search_mode == 'filename':
                where_conditions.append('filename LIKE ?')
                params.append(query_param)
            elif search_mode == 'title':
                where_conditions.append('title LIKE ?')
                params.append(query_param)
            elif search_mode == 'notes':
                where_conditions.append('notes LIKE ?')
                params.append(query_param)
            elif search_mode == 'all':
                where_conditions.append('(title LIKE ? OR filename LIKE ? OR notes LIKE ? OR category LIKE ?)')
                params.extend([query_param, query_param, query_param, query_param])
        
        # Add category filter
        if category:
            where_conditions.append('category = ?')
            params.append(category)
        
        # Add rating filter
        if min_rating > 0:
            where_conditions.append('rating >= ?')
            params.append(min_rating)
        
        # Build final query
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        sql = f'SELECT * FROM videos WHERE {where_clause} ORDER BY title ASC'
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        
        return [self._row_to_dict(row, cursor) for row in results]

    def _row_to_dict(self, row: tuple, cursor) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        cols = [description[0] for description in cursor.description]
        return dict(zip(cols, row))

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
