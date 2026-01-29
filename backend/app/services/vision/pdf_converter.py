"""PDF to image conversion service for vision analysis.

This service provides methods to convert PDF pages to images and extract
embedded images from PDFs for Claude's vision capabilities.
"""

import io
import logging
from typing import BinaryIO

logger = logging.getLogger(__name__)


class PDFConverter:
    """Convert PDFs to images for vision analysis.

    Supports two PDF processing libraries:
    - pdf2image (default): Better for rendering complex PDFs
    - PyMuPDF (fitz): Faster, good for extracting embedded images

    Usage:
        converter = PDFConverter()
        images = await converter.convert_pdf_to_images(pdf_content)
        embedded_images = await converter.extract_images_from_pdf(pdf_content)
    """

    def __init__(self, dpi: int = 150, image_format: str = "PNG"):
        """Initialize PDF converter.

        Args:
            dpi: Dots per inch for PDF rendering (default: 150)
            image_format: Output image format (PNG, JPEG, WEBP)
        """
        self.dpi = dpi
        self.image_format = image_format.upper()

        # Try to import pdf2image, fall back to PyMuPDF
        self.use_pdf2image = True
        try:
            from pdf2image import convert_from_bytes  # noqa: F401
        except ImportError:
            logger.warning(
                "pdf2image not available, falling back to PyMuPDF. "
                "Install with: pip install pdf2image"
            )
            self.use_pdf2image = False
            try:
                import fitz  # noqa: F401
            except ImportError:
                logger.error(
                    "Neither pdf2image nor PyMuPDF available. "
                    "Install one with: pip install pdf2image OR pip install PyMuPDF"
                )
                raise ImportError("No PDF processing library available")

    async def convert_pdf_to_images(
        self, pdf_content: bytes | BinaryIO, dpi: int | None = None
    ) -> list[bytes]:
        """Convert PDF pages to images.

        Args:
            pdf_content: PDF file content (bytes or file-like object)
            dpi: Override default DPI (optional)

        Returns:
            List of image bytes (one per page), in PNG/JPEG format

        Raises:
            ImportError: If no PDF library is available
            Exception: If PDF conversion fails
        """
        dpi = dpi or self.dpi

        # Convert file-like object to bytes if needed
        if hasattr(pdf_content, "read"):
            pdf_bytes = pdf_content.read()
            if hasattr(pdf_content, "seek"):
                pdf_content.seek(0)  # Reset file pointer
        else:
            pdf_bytes = pdf_content

        try:
            if self.use_pdf2image:
                return await self._convert_with_pdf2image(pdf_bytes, dpi)
            else:
                return await self._convert_with_pymupdf(pdf_bytes, dpi)
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise

    async def _convert_with_pdf2image(self, pdf_bytes: bytes, dpi: int) -> list[bytes]:
        """Convert PDF using pdf2image library.

        Args:
            pdf_bytes: PDF content as bytes
            dpi: Dots per inch for rendering

        Returns:
            List of image bytes
        """
        from pdf2image import convert_from_bytes
        from PIL import Image

        # Convert PDF to PIL images
        pil_images = convert_from_bytes(pdf_bytes, dpi=dpi, fmt=self.image_format.lower())

        # Convert PIL images to bytes
        image_bytes_list = []
        for pil_image in pil_images:
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format=self.image_format)
            image_bytes_list.append(img_byte_arr.getvalue())

        logger.info(f"Converted PDF to {len(image_bytes_list)} images using pdf2image")
        return image_bytes_list

    async def _convert_with_pymupdf(self, pdf_bytes: bytes, dpi: int) -> list[bytes]:
        """Convert PDF using PyMuPDF library.

        Args:
            pdf_bytes: PDF content as bytes
            dpi: Dots per inch for rendering

        Returns:
            List of image bytes
        """
        import fitz  # PyMuPDF

        # Open PDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Calculate zoom factor from DPI (72 DPI is default)
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        image_bytes_list = []
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # Render page to pixmap
            pix = page.get_pixmap(matrix=matrix)

            # Convert to bytes
            if self.image_format == "PNG":
                img_bytes = pix.tobytes("png")
            elif self.image_format == "JPEG":
                img_bytes = pix.tobytes("jpeg")
            else:
                # Default to PNG
                img_bytes = pix.tobytes("png")

            image_bytes_list.append(img_bytes)

        pdf_document.close()

        logger.info(f"Converted PDF to {len(image_bytes_list)} images using PyMuPDF")
        return image_bytes_list

    async def extract_images_from_pdf(self, pdf_content: bytes | BinaryIO) -> list[tuple[int, bytes]]:
        """Extract embedded images from PDF.

        This is useful for extracting charts, diagrams, and other images
        that are embedded in the PDF without re-rendering the entire page.

        Args:
            pdf_content: PDF file content (bytes or file-like object)

        Returns:
            List of tuples: (page_number, image_bytes)

        Raises:
            ImportError: If PyMuPDF is not available
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.error(
                "PyMuPDF required for image extraction. Install with: pip install PyMuPDF"
            )
            raise ImportError("PyMuPDF not available for image extraction")

        # Convert file-like object to bytes if needed
        if hasattr(pdf_content, "read"):
            pdf_bytes = pdf_content.read()
            if hasattr(pdf_content, "seek"):
                pdf_content.seek(0)
        else:
            pdf_bytes = pdf_content

        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        extracted_images = []

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # Get list of images on page
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                xref = img[0]  # Image reference number

                # Extract image
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]

                extracted_images.append((page_num + 1, image_bytes))  # 1-indexed pages

        pdf_document.close()

        logger.info(f"Extracted {len(extracted_images)} embedded images from PDF")
        return extracted_images

    async def get_page_count(self, pdf_content: bytes | BinaryIO) -> int:
        """Get the number of pages in a PDF.

        Args:
            pdf_content: PDF file content (bytes or file-like object)

        Returns:
            Number of pages in the PDF
        """
        try:
            import fitz
        except ImportError:
            # Fallback to pdf2image
            from pdf2image import pdfinfo_from_bytes

            if hasattr(pdf_content, "read"):
                pdf_bytes = pdf_content.read()
                if hasattr(pdf_content, "seek"):
                    pdf_content.seek(0)
            else:
                pdf_bytes = pdf_content

            info = pdfinfo_from_bytes(pdf_bytes)
            return info.get("Pages", 0)

        # Use PyMuPDF
        if hasattr(pdf_content, "read"):
            pdf_bytes = pdf_content.read()
            if hasattr(pdf_content, "seek"):
                pdf_content.seek(0)
        else:
            pdf_bytes = pdf_content

        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(pdf_document)
        pdf_document.close()

        return page_count
