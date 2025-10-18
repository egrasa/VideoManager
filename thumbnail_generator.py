"""Thumbnail generator: Extract frames from videos using FFmpeg."""

import subprocess
import logging
from pathlib import Path
import tempfile
from typing import Optional, List
import shutil
import time

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Generate video thumbnails using FFmpeg."""

    THUMBNAIL_SIZE = "160x90"  # Width x Height
    THUMBNAIL_QUALITY = 3  # 1-10, lower = better quality
    CACHE_DIR = None
    FFMPEG_PATH = None
    FFPROBE_PATH = None

    # Common FFmpeg installation locations
    FFMPEG_LOCATIONS = [
        # Chocolatey default
        Path("C:\\ProgramData\\chocolatey\\bin\\ffmpeg.exe"),
        Path("C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\bin\\ffmpeg.exe"),
        # Manual installations
        Path("C:\\ffmpeg\\bin\\ffmpeg.exe"),
        Path("C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"),
        Path("C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"),
        # Scoop
        Path.home() / "scoop\\apps\\ffmpeg\\current\\bin\\ffmpeg.exe",
        # Winget installations (various locations)
        Path.home() / "AppData\\Local\\Programs\\ffmpeg\\bin\\ffmpeg.exe",
        Path("C:\\Users\\egras\\AppData\\Local\\Programs\\ffmpeg\\bin\\ffmpeg.exe"),
        Path("C:\\Users\\egras\\AppData\\Local\\Microsoft\\WinGet\\Links\\ffmpeg.exe"),
    ]

    FFPROBE_LOCATIONS = [
        # Chocolatey default
        Path("C:\\ProgramData\\chocolatey\\bin\\ffprobe.exe"),
        Path("C:\\ProgramData\\chocolatey\\lib\\ffmpeg\\tools\\bin\\ffprobe.exe"),
        # Manual installations
        Path("C:\\ffmpeg\\bin\\ffprobe.exe"),
        Path("C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe"),
        Path("C:\\Program Files (x86)\\ffmpeg\\bin\\ffprobe.exe"),
        # Scoop
        Path.home() / "scoop\\apps\\ffmpeg\\current\\bin\\ffprobe.exe",
        # Winget installations (various locations)
        Path.home() / "AppData\\Local\\Programs\\ffmpeg\\bin\\ffprobe.exe",
        Path("C:\\Users\\egras\\AppData\\Local\\Programs\\ffmpeg\\bin\\ffprobe.exe"),
        Path("C:\\Users\\egras\\AppData\\Local\\Microsoft\\WinGet\\Links\\ffprobe.exe"),
    ]

    @staticmethod
    def _find_ffmpeg_executable(program_name: str, locations: list) -> Optional[str]:
        """Find FFmpeg executable in common locations."""
        # First try using shutil.which (checks PATH)
        found = shutil.which(program_name)
        if found:
            logger.debug("Found %s in PATH: %s", program_name, found)
            return found

        # Then try known locations
        for location in locations:
            if location.exists():
                logger.debug("Found %s at: %s", program_name, location)
                return str(location)

        # Last resort: search recursively in AppData (for winget)
        try:
            appdata_path = Path.home() / "AppData" / "Local"
            if appdata_path.exists():
                for item in appdata_path.rglob(f"{program_name}.exe"):
                    if "ffmpeg" in str(item).lower() or "GyanD" in str(item):
                        logger.debug("Found %s at: %s (recursive search)", program_name, item)
                        return str(item)
        except (OSError, PermissionError):
            pass

        logger.warning("Could not find %s in any known location", program_name)
        return None

    @staticmethod
    def _initialize_ffmpeg_paths():
        """Initialize FFmpeg paths if not already done."""
        if ThumbnailGenerator.FFMPEG_PATH is None:
            ThumbnailGenerator.FFMPEG_PATH = ThumbnailGenerator._find_ffmpeg_executable(
                "ffmpeg", ThumbnailGenerator.FFMPEG_LOCATIONS
            )

        if ThumbnailGenerator.FFPROBE_PATH is None:
            ThumbnailGenerator.FFPROBE_PATH = ThumbnailGenerator._find_ffmpeg_executable(
                "ffprobe", ThumbnailGenerator.FFPROBE_LOCATIONS
            )

    @staticmethod
    def _get_cache_dir() -> Path:
        """Get or create thumbnail cache directory."""
        if ThumbnailGenerator.CACHE_DIR is None:
            cache_dir = Path(tempfile.gettempdir()) / "videomanager_thumbs"
            cache_dir.mkdir(exist_ok=True)
            ThumbnailGenerator.CACHE_DIR = cache_dir
        return ThumbnailGenerator.CACHE_DIR

    @staticmethod
    def get_video_duration(video_path: str) -> Optional[float]:
        """
        Get video duration in seconds.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds or None if unable to determine
        """
        return ThumbnailGenerator._get_video_duration(video_path)

    @staticmethod
    def _get_video_duration(video_path: str) -> Optional[float]:
        """Get video duration in seconds using FFprobe."""
        ThumbnailGenerator._initialize_ffmpeg_paths()

        if not ThumbnailGenerator.FFPROBE_PATH:
            logger.warning("FFprobe not found in PATH or known locations")
            return None

        try:
            cmd = [
                ThumbnailGenerator.FFPROBE_PATH,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1:noprint_wrappers=1',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
        except (ValueError, OSError) as e:
            logger.warning("Could not get duration for %s: %s", video_path, e)
        return None

    @staticmethod
    def _is_slow_storage(video_path: str) -> bool:
        """Detect if video is on slow/external storage.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if on slow storage, False otherwise
        """
        path_lower = video_path.lower()
        
        # Check for common slow storage indicators
        slow_indicators = [
            'elements',  # External drives like Elements
            'backup',
            'external',
            'portable',
            'usb',
            'removable',
            'network',
            'smb://',
            'nfs://',
            '\\\\',  # UNC paths
            'seagate',
            'wd-',
            'western digital',
            'my passport',
            'elements',
            '14tb',
            '10tb',
            '8tb',
            '6tb',
            '4tb',
            '2tb',
        ]
        
        return any(indicator in path_lower for indicator in slow_indicators)

    @staticmethod
    def _get_frame_timeout(video_path: str) -> int:
        """Get appropriate timeout for frame extraction based on storage type.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Timeout in seconds
        """
        if ThumbnailGenerator._is_slow_storage(video_path):
            logger.debug("Detected slow storage for %s, using extended timeout", video_path)
            return 60  # 60 seconds for external/slow storage
        else:
            return 30  # 30 seconds for local storage

    @staticmethod
    def _extract_frame_with_retry(
        video_path: str,
        timestamp: float,
        frame_index: int,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """Extract a single frame with retry logic and exponential backoff.
        
        Args:
            video_path: Path to video file
            timestamp: Frame timestamp in seconds
            frame_index: Frame number for logging
            output_dir: Output directory for frame
            
        Returns:
            Path to generated frame or None if failed
        """
        max_retries = 2
        backoff_base = 1  # seconds
        
        for attempt in range(max_retries + 1):
            try:
                timeout = ThumbnailGenerator._get_frame_timeout(video_path)
                
                if output_dir is None:
                    output_dir = str(ThumbnailGenerator._get_cache_dir())
                
                frame_path = str(Path(output_dir) / f"frame_{frame_index}_{int(timestamp)}.png")
                
                cmd = [
                    ThumbnailGenerator.FFMPEG_PATH,
                    '-hwaccel', 'none',
                    '-i', video_path,
                    '-ss', str(timestamp),
                    '-vframes', '1',
                    '-vf', 'scale=120:67',
                    '-q:v', '5',
                    '-y',
                    frame_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False
                )
                
                if result.returncode == 0 and Path(frame_path).exists():
                    logger.debug("Generated timeline frame %d: %s", frame_index, frame_path)
                    return frame_path
                else:
                    if attempt < max_retries:
                        logger.warning(
                            "Failed to extract frame %d (attempt %d/%d), retrying...",
                            frame_index, attempt + 1, max_retries + 1
                        )
                    else:
                        logger.warning("Failed to extract frame %d after %d attempts", 
                                     frame_index, max_retries + 1)
                    return None
                    
            except subprocess.TimeoutExpired:
                if attempt < max_retries:
                    wait_time = backoff_base * (2 ** attempt)
                    logger.warning(
                        "Timeout extracting frame %d (attempt %d/%d), waiting %ds before retry",
                        frame_index, attempt + 1, max_retries + 1, wait_time
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "Timeout extracting frame %d from %s (all %d attempts failed)",
                        frame_index, video_path, max_retries + 1
                    )
                    return None
            except (OSError, ValueError) as e:
                logger.error("Error extracting frame %d: %s", frame_index, e)
                return None
        
        return None


    @staticmethod
    def generate_thumbnail(
        video_path: str,
        output_path: Optional[str] = None,
        timestamp: Optional[float] = None
    ) -> Optional[str]:
        """
        Generate a thumbnail from a video file.

        Args:
            video_path: Path to video file
            output_path: Where to save thumbnail (optional, uses cache if None)
            timestamp: Timestamp in seconds (optional, uses 10% of duration if None)

        Returns:
            Path to generated thumbnail, or None if failed
        """
        ThumbnailGenerator._initialize_ffmpeg_paths()

        if not ThumbnailGenerator.FFMPEG_PATH:
            logger.error("FFmpeg not found in PATH or known locations")
            return None

        if not Path(video_path).exists():
            logger.error("Video file not found: %s", video_path)
            return None

        # Generate output path if not provided
        if output_path is None:
            cache_dir = ThumbnailGenerator._get_cache_dir()
            safe_name = Path(video_path).stem
            output_path = str(cache_dir / f"{safe_name}_thumb.jpg")

        # Skip if already generated
        if Path(output_path).exists():
            return output_path

        # Get timestamp if not provided
        if timestamp is None:
            duration = ThumbnailGenerator._get_video_duration(video_path)
            if duration and duration > 0:
                timestamp = duration * 0.1  # 10% into the video
            else:
                timestamp = 5  # Default: 5 seconds

        # Generate thumbnail using FFmpeg
        try:
            cmd = [
                ThumbnailGenerator.FFMPEG_PATH,
                '-hwaccel', 'none',  # Disable hardware acceleration to avoid D3D11VA errors
                '-i', video_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-vf', f"scale={ThumbnailGenerator.THUMBNAIL_SIZE}",
                '-q:v', str(ThumbnailGenerator.THUMBNAIL_QUALITY),
                '-y',  # Overwrite output
                output_path
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,  # Increased timeout from 15 to 30 seconds
                check=False
            )

            if result.returncode == 0 and Path(output_path).exists():
                logger.info("Generated thumbnail: %s", output_path)
                return output_path
            else:
                logger.error("FFmpeg failed: %s", result.stderr)
                return None

        except subprocess.TimeoutExpired:
            logger.error("Thumbnail generation timeout for %s", video_path)
            return None
        except (OSError, ValueError) as e:
            logger.error("Error generating thumbnail: %s", e)
            return None

    @staticmethod
    def cleanup_cache():
        """Remove cached thumbnails."""
        try:
            cache_dir = ThumbnailGenerator._get_cache_dir()
            for thumb_file in cache_dir.glob("*.jpg"):
                thumb_file.unlink()
            logger.info("Cleaned up thumbnail cache")
        except OSError as e:
            logger.warning("Error cleaning up cache: %s", e)

    @staticmethod
    def generate_single_timeline_frame(
        video_path: str,
        frame_index: int,
        timestamp: float,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a single frame from a video for timeline visualization.
        
        Args:
            video_path: Path to video file
            frame_index: Index of the frame (0-based)
            timestamp: Timestamp in seconds to extract frame from
            output_dir: Directory to save frame (optional, uses cache if None)
            
        Returns:
            Path to generated frame image or None if failed
        """
        ThumbnailGenerator._initialize_ffmpeg_paths()

        if not ThumbnailGenerator.FFMPEG_PATH:
            return None

        if not Path(video_path).exists():
            return None

        # Generate output directory if not provided
        if output_dir is None:
            cache_dir = ThumbnailGenerator._get_cache_dir()
            safe_name = Path(video_path).stem
            output_dir = str(cache_dir / f"{safe_name}_timeline")
            Path(output_dir).mkdir(exist_ok=True)

        # Generate frame filename
        frame_filename = f"frame_{frame_index:02d}.jpg"
        frame_path = str(Path(output_dir) / frame_filename)

        # Skip if already exists
        if Path(frame_path).exists():
            logger.debug("Using cached timeline frame: %s", frame_path)
            return frame_path

        # Extract frame with retry logic
        return ThumbnailGenerator._extract_frame_with_retry(
            video_path, timestamp, frame_index, output_dir
        )

    @staticmethod
    def generate_timeline_frames(
        video_path: str,
        num_frames: int = 8,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Generate multiple frames from a video for timeline visualization.

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract (default 8)
            output_dir: Directory to save frames (optional, uses cache if None)

        Returns:
            List of paths to generated frame images
        """
        ThumbnailGenerator._initialize_ffmpeg_paths()

        if not ThumbnailGenerator.FFMPEG_PATH or not ThumbnailGenerator.FFPROBE_PATH:
            logger.warning("FFmpeg not available for timeline generation")
            return []

        if not Path(video_path).exists():
            logger.error("Video file not found: %s", video_path)
            return []

        # Get video duration
        duration = ThumbnailGenerator._get_video_duration(video_path)
        if not duration or duration <= 0:
            logger.warning("Could not determine video duration: %s", video_path)
            return []

        # Reduce frames for slow storage to minimize timeout issues
        if ThumbnailGenerator._is_slow_storage(video_path):
            original_frames = num_frames
            num_frames = max(3, num_frames // 2)  # Reduce by half, min 3
            logger.info(
                "Detected slow storage for %s, reducing frames from %d to %d",
                Path(video_path).name, original_frames, num_frames
            )

        # Generate output directory if not provided
        if output_dir is None:
            cache_dir = ThumbnailGenerator._get_cache_dir()
            safe_name = Path(video_path).stem
            output_dir = str(cache_dir / f"{safe_name}_timeline")
            Path(output_dir).mkdir(exist_ok=True)

        frame_paths = []

        # Calculate timestamps for frames evenly distributed across video
        for i in range(num_frames):
            # Distribute frames across the video duration (skip first and last 5%)
            progress = 0.05 + (i / (num_frames - 1)) * 0.9 if num_frames > 1 else 0.5
            timestamp = duration * progress

            # Use retry-based frame extraction
            frame_path = ThumbnailGenerator._extract_frame_with_retry(
                video_path, timestamp, i, output_dir
            )
            
            if frame_path:
                frame_paths.append(frame_path)

        logger.info("Generated %d timeline frames for %s", len(frame_paths), Path(video_path).name)
        return frame_paths

    @staticmethod
    def check_ffmpeg_available() -> bool:
        """Check if FFmpeg and FFprobe are available in system PATH or known locations."""
        ThumbnailGenerator._initialize_ffmpeg_paths()

        if not ThumbnailGenerator.FFMPEG_PATH or not ThumbnailGenerator.FFPROBE_PATH:
            return False

        try:
            result_ffmpeg = subprocess.run(
                [ThumbnailGenerator.FFMPEG_PATH, '-version'],
                capture_output=True,
                timeout=2,
                check=False
            )
            result_ffprobe = subprocess.run(
                [ThumbnailGenerator.FFPROBE_PATH, '-version'],
                capture_output=True,
                timeout=2,
                check=False
            )
            available = result_ffmpeg.returncode == 0 and result_ffprobe.returncode == 0

            if available:
                logger.info("FFmpeg found at: %s", ThumbnailGenerator.FFMPEG_PATH)
                logger.info("FFprobe found at: %s", ThumbnailGenerator.FFPROBE_PATH)

            return available
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
