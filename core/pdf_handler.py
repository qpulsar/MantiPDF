import fitz  # PyMuPDF
import os
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QRectF

from core.pdf_annotations import PDFAnnotations

class PDFHandler:
    """Handles PDF document loading, manipulation, and rendering."""

    def __init__(self):
        self.doc: fitz.Document | None = None
        self.filepath: str | None = None
        self.modified: bool = False # Track if changes have been made
        self.annotations = None # Will be initialized when a document is opened

    def open_document(self, filepath: str) -> bool:
        """Opens a PDF document.

        Args:
            filepath: The path to the PDF file.

        Returns:
            True if the document was opened successfully, False otherwise.
        """
        if self.doc:
            self.close_document() # Close previous document if any

        try:
            self.doc = fitz.open(filepath)
            self.filepath = filepath
            self.modified = False
            
            # Initialize annotations handler
            self.annotations = PDFAnnotations(self)
            
            # Load annotations if they exist
            annotations_filepath = self._get_annotations_filepath()
            if annotations_filepath:
                self.annotations.load_annotations(annotations_filepath)
                
            return True
        except Exception as e:
            print(f"Error opening PDF {filepath}: {e}")
            self.doc = None
            self.filepath = None
            self.annotations = None
            return False

    def close_document(self):
        """Closes the currently open PDF document."""
        if self.doc:
            try:
                # Save annotations if modified
                if self.modified and self.annotations:
                    annotations_filepath = self._get_annotations_filepath()
                    if annotations_filepath:
                        self.annotations.save_annotations(annotations_filepath)
                
                self.doc.close()
            except Exception as e:
                print(f"Error closing PDF {self.filepath}: {e}")
            finally:
                self.doc = None
                self.filepath = None
                self.annotations = None
                self.modified = False

    @property
    def page_count(self) -> int:
        """Returns the number of pages in the document."""
        return self.doc.page_count if self.doc else 0

    def get_page(self, page_num: int) -> fitz.Page | None:
        """Returns the specified page object."""
        if self.doc and 0 <= page_num < self.page_count:
            try:
                return self.doc.load_page(page_num)
            except Exception as e:
                print(f"Error loading page {page_num}: {e}")
                return None
        return None

    def get_page_pixmap(self, page_num: int, scale: float = 1.0, rotation: int = 0) -> QPixmap | None:
        """Renders a page to a QPixmap.

        Args:
            page_num: The page number (0-indexed).
            scale: The scaling factor for rendering.
            rotation: The rotation angle (0, 90, 180, 270).

        Returns:
            A QPixmap of the rendered page, or None on error.
        """
        page = self.get_page(page_num)
        if page:
            try:
                zoom_matrix = fitz.Matrix(scale, scale)
                rotation_matrix = fitz.Matrix(1, 1).prerotate(page.rotation)
                combined_matrix = zoom_matrix * rotation_matrix

                pix = page.get_pixmap(matrix=combined_matrix, alpha=False)

                # Convert fitz.Pixmap to QImage to QPixmap
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                qpixmap = QPixmap.fromImage(img)
                return qpixmap
            except Exception as e:
                print(f"Error getting pixmap for page {page_num}: {e}")
                return None
        return None


    def save_document(self, filepath: str | None = None):
        """Saves the document. If filepath is None, saves to the original path."""
        if not self.doc:
            print("No document open to save.")
            return False

        if not self.modified and filepath is None:
            print("No modifications to save.")
            return True # Nothing to do

        save_path = filepath if filepath else self.filepath
        if not save_path:
            print("Cannot save document without a filepath.")
            # Maybe trigger Save As? For now, return False
            return False

        try:
            # TODO: Implement incremental save if possible and desired
            # For now, use standard save which might rebuild the file
            save_opts = {} # Add options like garbage collection, etc. if needed
            self.doc.save(save_path, **save_opts)
            
            # Save annotations to a separate file
            if self.annotations:
                old_annotations_filepath = self._get_annotations_filepath()
                
                # If saving to a new path, update the internal filepath first
                if filepath:
                    old_filepath = self.filepath
                    self.filepath = filepath
                    
                # Save annotations to the new location
                new_annotations_filepath = self._get_annotations_filepath()
                self.annotations.save_annotations(new_annotations_filepath)
                
            self.modified = False
            if filepath:
                self.filepath = filepath
            return True
        except Exception as e:
            print(f"Error saving PDF to {save_path}: {e}")
            return False

    def rotate_page(self, page_num: int, angle: int):
        """Rotates a specific page by the given angle (90, 180, 270).
        
        Args:
            page_num: The page number to rotate (0-indexed).
            angle: The rotation angle in degrees (must be 90, 180, or 270).
                   90 = clockwise 90 degrees (saat yönünde 90 derece)
                   180 = 180 degrees (180 derece döndürme)
                   270 = counter-clockwise 90 degrees (saat yönünün tersine 90 derece)
        
        Returns:
            True if rotation was successful, False otherwise.
        """
        if not self.doc or not (0 <= page_num < self.page_count):
            return False
        if angle not in [90, 180, 270]:
             print(f"Invalid rotation angle: {angle}. Must be 90, 180, or 270.")
             return False

        try:
            page = self.doc[page_num]
            # Calculate the new rotation angle based on the current rotation
            current_rotation = page.rotation
            new_rotation = (current_rotation + angle) % 360
            page.set_rotation(new_rotation)
            self.modified = True
            return True
        except Exception as e:
            print(f"Error rotating page {page_num}: {e}")
            return False

    def move_page(self, from_index: int, to_index: int):
        """Moves a page from one position to another."""
        if not self.doc or not (0 <= from_index < self.page_count) or not (0 <= to_index < self.page_count):
            return False
        
        try:
            # PyMuPDF's move_page is smart about adjusting indices
            self.doc.move_page(from_index, to_index)
            self.modified = True
            return True
        except Exception as e:
            print(f"Error moving page: {e}")
            return False

    def add_blank_page(self, width: float = 595, height: float = 842, index: int = -1):
        """Adds a blank page."""
        if not self.doc: return False
        try:
            # Default A4 size in points
            self.doc.new_page(pno=index, width=width, height=height)
            self.modified = True
            return True
        except Exception as e:
            print(f"Error adding blank page: {e}")
            return False

    def delete_page(self, page_num: int):
        """Deletes a specific page."""
        if not self.doc or not (0 <= page_num < self.page_count): return False
        try:
            self.doc.delete_page(page_num)
            self.modified = True
            return True
        except Exception as e:
            print(f"Error deleting page {page_num}: {e}")
            return False

    def merge_document(self, other_pdf_path: str):
        """Merges another PDF document into the current one."""
        if not self.doc:
            print("No document open to merge into.")
            return False
        if not os.path.exists(other_pdf_path):
            print(f"File not found: {other_pdf_path}")
            return False
        try:
            other_doc = fitz.open(other_pdf_path)
            self.doc.insert_pdf(other_doc)
            other_doc.close()
            self.modified = True
            print(f"Merged document {other_pdf_path} into {self.filepath}")
            return True
        except Exception as e:
            print(f"Error merging document {other_pdf_path}: {e}")
            return False
            
    def split_pdf(self, output_dir: str, split_all: bool, page_ranges: list[tuple[int, int]] | None) -> tuple[bool, str]:
        """Splits the current PDF based on the provided options.

        Args:
            output_dir: The directory to save the split PDF files.
            split_all: If True, split every page into a separate file.
            page_ranges: A list of (start_page, end_page) tuples (0-indexed) 
                         to split by range. Used if split_all is False.

        Returns:
            A tuple (success: bool, message: str).
        """
        if not self.doc or not self.filepath:
            return False, "No document open to split."
        if not os.path.isdir(output_dir):
            return False, f"Output directory does not exist: {output_dir}"

        base_filename = os.path.splitext(os.path.basename(self.filepath))[0]
        split_count = 0

        try:
            if split_all:
                # Split every page
                for i in range(self.page_count):
                    new_doc = fitz.open() # Create a new empty PDF
                    new_doc.insert_pdf(self.doc, from_page=i, to_page=i)
                    output_filename = os.path.join(output_dir, f"{base_filename}_page_{i + 1}.pdf")
                    new_doc.save(output_filename)
                    new_doc.close()
                    split_count += 1
                message = f"{split_count} sayfa başarıyla ayrı PDF dosyalarına bölündü."

            elif page_ranges:
                # Split by ranges
                range_num = 1
                for start_page, end_page in page_ranges:
                    if 0 <= start_page < self.page_count and 0 <= end_page < self.page_count and start_page <= end_page:
                        new_doc = fitz.open()
                        new_doc.insert_pdf(self.doc, from_page=start_page, to_page=end_page)
                        # Determine output filename based on range
                        if start_page == end_page:
                            range_desc = f"page_{start_page + 1}"
                        else:
                            range_desc = f"pages_{start_page + 1}-{end_page + 1}"
                        output_filename = os.path.join(output_dir, f"{base_filename}_{range_desc}.pdf")
                        new_doc.save(output_filename)
                        new_doc.close()
                        split_count += 1
                        range_num += 1
                    else:
                        print(f"Skipping invalid page range: {start_page+1}-{end_page+1}")
                message = f"{split_count} PDF dosyası belirtilen aralıklara göre başarıyla oluşturuldu."
            
            else:
                return False, "Geçersiz bölme seçeneği."

            return True, message

        except Exception as e:
            error_message = f"PDF bölme sırasında hata oluştu: {e}"
            print(error_message)
            return False, error_message

    def extract_text(self, page_num: int) -> str | None:
        """Extracts text from a specific page."""
        if not self.doc or not (0 <= page_num < self.page_count):
            print(f"Invalid document or page number: {page_num}")
            return None
            
        try:
            # Get the page
            page = self.doc[page_num]
            
            # Extract text from the page
            text = page.get_text()
            
            return text
        except Exception as e:
            print(f"Error extracting text from page {page_num}: {e}")
            return None
            
    def save_page_as_image(self, page_num: int, filepath: str, dpi: int = 300, image_format: str = "png"):
        """Saves a specific page as an image file.
        
        Args:
            page_num: The page number to save (0-indexed).
            filepath: The path where the image will be saved.
            dpi: The resolution in dots per inch (default: 300).
            image_format: The image format (png, jpg, etc.).
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.doc or not (0 <= page_num < self.page_count):
            print(f"Invalid document or page number: {page_num}")
            return False
            
        try:
            # Get the page
            page = self.doc[page_num]
            
            # Calculate the zoom factor based on DPI
            # Standard PDF resolution is 72 DPI, so we calculate the zoom factor
            zoom = dpi / 72
            
            # Create a pixmap with the specified zoom factor
            # Use RGB color space (no alpha channel)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            
            pix.save(filepath)
            return True
        except Exception as e:
            print(f"Error saving page as image: {e}")
            return False
            
    def add_note(self, page_index, position, content, username=None):
        """Add a note annotation to the PDF.
        
        Args:
            page_index: The 0-based index of the page.
            position: The position (QPoint) where the note should be placed.
            content: The content of the note.
            username: The username of the note creator.
            
        Returns:
            The annotation object if successful, None otherwise.
        """
        if not self.doc or not self.annotations or not (0 <= page_index < self.page_count):
            return None
            
        # Create a small rectangle around the position
        x, y = position.x(), position.y()
        rect = QRectF(x - 10, y - 10, 20, 20)  # 20x20 rectangle centered at position
        
        # Add the note annotation
        annot = self.annotations.add_note(page_index, rect, content, username)
        if annot:
            self.modified = True
            return annot
        return None
        
    def add_textbox(self, page_index, rect, content, fontsize=12, color=(0, 0, 0)):
        """Add a FreeText annotation to the PDF."""
        if self.annotations:
            return self.annotations.add_text_annotation(page_index, rect, content, fontsize, color)
        return None

    def add_line(self, page_index, start_point, end_point, color=(1, 0, 0), width=2.0):
        """Add a line annotation to the PDF."""
        if self.annotations:
            return self.annotations.add_line_annotation(page_index, start_point, end_point, color, width)
        return None

    def add_circle(self, page_index, rect, color=(1, 0, 0), width=2.0):
        """Add a circle annotation to the PDF."""
        if self.annotations:
            return self.annotations.add_circle_annotation(page_index, rect, color, width)
        return None

    def add_highlight(self, page_index, rect, color=(1, 1, 0)):
        """Add a highlight annotation to the PDF."""
        if self.annotations:
            return self.annotations.add_highlight_annotation(page_index, rect, color)
        return None

    def add_stamp(self, page_index, rect, stamp_index=0):
        """Add a stamp annotation to the PDF."""
        if self.annotations:
            return self.annotations.add_stamp_annotation(page_index, rect, stamp_index)
        return None

    def _get_annotations_filepath(self):
        """Constructs the filepath for the annotations JSON file (Disabled)."""
        return None



