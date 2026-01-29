"""Image optimization service for Claude vision API.

This service handles image preprocessing to meet Claude's vision API requirements:
- Max dimension: 1568px
- Supported formats: PNG, JPEG, WEBP, GIF
- Recommended size: < 500KB per image
- DPI: 150 for good quality vs. cost balance
"""

import io
import logging
from typing import BinaryIO

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """Optimize images for Claude's vision API.

    Handles:
    - Resizing to fit within max dimensions
    - Format conversion
    - Compression
    - Metadata stripping (for security)
    """

    def __init__(
        self,
        max_dimension: int = 1568,
        target_file_size_kb: int = 500,
        quality: int = 85,
    ):
        """Initialize image optimizer.

        Args:
            max_dimension: Maximum width or height in pixels
            target_file_size_kb: Target file size in kilobytes
            quality: JPEG/WebP quality (1-100, higher is better)
        """
        self.max_dimension = max_dimension
        self.target_file_size_kb = target_file_size_kb
        self.quality = quality

        # Import PIL
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            logger.error("Pillow not installed. Run: pip install Pillow")
            raise ImportError("Pillow required for image optimization")

    async def optimize_image(
        self,
        image_data: bytes | BinaryIO,
        output_format: str = "PNG",
        strip_metadata: bool = True,
    ) -> tuple[bytes, dict]:
        """Optimize an image for vision analysis.

        Args:
            image_data: Input image (bytes or file-like object)
            output_format: Output format (PNG, JPEG, WEBP)
            strip_metadata: Remove EXIF and other metadata

        Returns:
            Tuple of (optimized_image_bytes, metadata_dict)
            metadata includes: original_size, optimized_size, dimensions, format

        Raises:
            ImportError: If PIL not available
            Exception: If image processing fails
        """
        from PIL import Image

        # Convert file-like to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        original_size = len(image_bytes)

        # Open image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logger.error(f"Failed to open image: {str(e)}")
            raise

        original_width, original_height = image.size
        original_format = image.format or "UNKNOWN"

        # Convert to RGB if necessary (for JPEG output)
        if output_format.upper() == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            # Create white background
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
            image = rgb_image

        # Resize if needed
        if max(original_width, original_height) > self.max_dimension:
            image = self._resize_image(image, self.max_dimension)
            logger.info(
                f"Resized image from {original_width}x{original_height} to {image.size[0]}x{image.size[1]}"
            )

        # Strip metadata if requested
        if strip_metadata:
            # Create new image without EXIF
            data = list(image.getdata())
            image_without_exif = Image.new(image.mode, image.size)
            image_without_exif.putdata(data)
            image = image_without_exif

        # Save with optimization
        output_buffer = io.BytesIO()

        save_kwargs = {"format": output_format.upper()}

        if output_format.upper() == "PNG":
            save_kwargs["optimize"] = True
        elif output_format.upper() in ("JPEG", "WEBP"):
            save_kwargs["quality"] = self.quality
            save_kwargs["optimize"] = True

        image.save(output_buffer, **save_kwargs)

        optimized_bytes = output_buffer.getvalue()
        optimized_size = len(optimized_bytes)

        # If still too large, try more aggressive compression
        if optimized_size > (self.target_file_size_kb * 1024):
            optimized_bytes = await self._aggressive_compress(
                image, output_format, self.target_file_size_kb * 1024
            )
            optimized_size = len(optimized_bytes)

        metadata = {
            "original_size_bytes": original_size,
            "optimized_size_bytes": optimized_size,
            "compression_ratio": original_size / optimized_size if optimized_size > 0 else 0,
            "original_dimensions": (original_width, original_height),
            "optimized_dimensions": image.size,
            "original_format": original_format,
            "output_format": output_format.upper(),
            "metadata_stripped": strip_metadata,
        }

        logger.info(
            f"Optimized image: {original_size / 1024:.1f}KB → {optimized_size / 1024:.1f}KB "
            f"({metadata['compression_ratio']:.2f}x compression)"
        )

        return optimized_bytes, metadata

    def _resize_image(self, image, max_dimension: int):
        """Resize image to fit within max_dimension while maintaining aspect ratio.

        Args:
            image: PIL Image object
            max_dimension: Maximum width or height

        Returns:
            Resized PIL Image
        """
        from PIL import Image

        width, height = image.size

        # Calculate new dimensions
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))

        # Use LANCZOS for high-quality downsampling
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    async def _aggressive_compress(
        self, image, output_format: str, target_size_bytes: int
    ) -> bytes:
        """Aggressively compress image to reach target size.

        Args:
            image: PIL Image object
            output_format: Target format
            target_size_bytes: Target file size

        Returns:
            Compressed image bytes
        """
        output_buffer = io.BytesIO()

        # Try progressively lower quality
        for quality in [75, 65, 55, 45, 35]:
            output_buffer.seek(0)
            output_buffer.truncate()

            if output_format.upper() == "PNG":
                # For PNG, reduce colors
                image = image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
                image.save(output_buffer, format="PNG", optimize=True)
            elif output_format.upper() in ("JPEG", "WEBP"):
                image.save(output_buffer, format=output_format.upper(), quality=quality, optimize=True)

            if len(output_buffer.getvalue()) <= target_size_bytes:
                logger.info(f"Achieved target size with quality={quality}")
                break

        return output_buffer.getvalue()

    async def create_thumbnail(
        self,
        image_data: bytes | BinaryIO,
        size: tuple[int, int] = (300, 300),
        output_format: str = "JPEG",
    ) -> bytes:
        """Create a thumbnail of an image.

        Args:
            image_data: Input image
            size: Thumbnail size (width, height)
            output_format: Output format

        Returns:
            Thumbnail image bytes
        """
        from PIL import Image

        # Convert file-like to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        # Open and resize
        image = Image.open(io.BytesIO(image_bytes))

        # Convert RGBA to RGB for JPEG
        if output_format.upper() == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            rgb_image.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
            image = rgb_image

        image.thumbnail(size, Image.Resampling.LANCZOS)

        # Save
        output_buffer = io.BytesIO()
        image.save(output_buffer, format=output_format.upper(), quality=85, optimize=True)

        return output_buffer.getvalue()


def get_image_optimizer(**kwargs) -> ImageOptimizer:
    """Factory function to get an image optimizer.

    Args:
        **kwargs: Passed to ImageOptimizer constructor

    Returns:
        Configured ImageOptimizer instance
    """
    return ImageOptimizer(**kwargs)
