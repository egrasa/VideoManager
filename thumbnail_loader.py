"""Asynchronous thumbnail loading for VideoManager.

Handles loading and caching of thumbnail images in a separate thread
to prevent UI blocking when loading large numbers of videos.
"""

import tkinter as tk
import logging
import threading
import queue
from pathlib import Path
from typing import Dict, Optional, Callable
from PIL import Image, ImageTk
from thumbnail_generator import ThumbnailGenerator

logger = logging.getLogger(__name__)


class ThumbnailLoader:
    """Manages asynchronous thumbnail loading and caching."""

    # Size constants
    THUMB_WIDTH = 145
    THUMB_HEIGHT = 82
    PLACEHOLDER_COLOR = '#404040'

    def __init__(self, max_workers: int = 3):
        """Initialize thumbnail loader.
        
        Args:
            max_workers: Number of worker threads for parallel loading
        """
        self.max_workers = max_workers
        self.worker_threads: Dict[int, threading.Thread] = {}
        self.request_queue: queue.Queue = queue.Queue()
        self.thumbnail_cache: Dict[str, ImageTk.PhotoImage] = {}
        self.loading_set: set = set()  # Track videos currently loading
        self.is_running = True
        self.stop_event = threading.Event()

        # Start worker threads
        self._start_workers()

    def _start_workers(self):
        """Start worker threads for thumbnail loading."""
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f'ThumbnailWorker-{i}'
            )
            thread.start()
            self.worker_threads[i] = thread
            logger.info('Started thumbnail worker thread %d', i)

    def _worker_loop(self):
        """Main loop for worker threads - processes thumbnail requests."""
        while self.is_running:
            try:
                # Get request from queue with timeout to allow periodic checks
                request = self.request_queue.get(timeout=1.0)
                
                if request is None:  # Sentinel value to stop worker
                    break

                video_path, callback = request
                
                try:
                    # Skip if already loading
                    if video_path in self.loading_set:
                        self.request_queue.task_done()
                        continue
                    
                    self.loading_set.add(video_path)
                    
                    # Generate thumbnail
                    thumb_path = ThumbnailGenerator.generate_thumbnail(video_path)
                    
                    if thumb_path and Path(thumb_path).exists():
                        # Load image
                        img = Image.open(thumb_path)
                        # Resize to ensure consistent size
                        img = img.resize((self.THUMB_WIDTH, self.THUMB_HEIGHT), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Cache the PhotoImage
                        self.thumbnail_cache[video_path] = photo
                        
                        logger.debug('Loaded thumbnail for: %s', Path(video_path).name)
                    else:
                        logger.warning('Failed to generate thumbnail for: %s', video_path)
                        photo = None
                    
                except (OSError, ValueError, IOError) as e:
                    logger.error('Error loading thumbnail for %s: %s', video_path, e)
                    photo = None
                
                finally:
                    self.loading_set.discard(video_path)
                    # Call the callback with the result
                    try:
                        callback(video_path, photo)
                    except (RuntimeError, tk.TclError) as e:
                        logger.error('Error in thumbnail callback: %s', e)
                    
                    self.request_queue.task_done()
                    
            except queue.Empty:
                continue
            except (RuntimeError, ValueError) as e:
                logger.error('Worker thread error: %s', e)

    def queue_thumbnail(self, video_path: str, callback: Callable[[str, Optional[ImageTk.PhotoImage]], None]):
        """Queue a thumbnail for loading.
        
        Args:
            video_path: Path to video file
            callback: Function to call when thumbnail is ready. Receives (video_path, photo)
        """
        # Check cache first
        if video_path in self.thumbnail_cache:
            callback(video_path, self.thumbnail_cache[video_path])
            return
        
        # Skip if already loading
        if video_path in self.loading_set:
            return
        
        # Queue for loading
        self.request_queue.put((video_path, callback))

    def get_placeholder_image(self) -> tk.PhotoImage:
        """Get a placeholder image when thumbnail is loading or unavailable.
        
        Returns:
            PhotoImage placeholder
        """
        # Create a simple placeholder using PIL
        img = Image.new('RGB', (self.THUMB_WIDTH, self.THUMB_HEIGHT), 
                       color=self.PLACEHOLDER_COLOR)
        return ImageTk.PhotoImage(img)

    def clear_cache(self):
        """Clear the thumbnail cache to free memory."""
        self.thumbnail_cache.clear()
        logger.info('Thumbnail cache cleared')

    def shutdown(self):
        """Shutdown the thumbnail loader and cleanup."""
        logger.info('Shutting down thumbnail loader')
        self.is_running = False
        self.stop_event.set()
        
        # Send sentinel values to stop workers
        for _ in range(self.max_workers):
            self.request_queue.put(None)
        
        # Wait for workers to finish
        for thread in self.worker_threads.values():
            thread.join(timeout=2.0)
        
        # Clear cache
        self.clear_cache()
        
        logger.info('Thumbnail loader shut down')

    def get_queue_size(self) -> int:
        """Get current size of request queue."""
        return self.request_queue.qsize()

    def get_loading_count(self) -> int:
        """Get number of thumbnails currently loading."""
        return len(self.loading_set)
