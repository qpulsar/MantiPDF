import fitz  # PyMuPDF
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

class PDFHandler:
    """Handles PDF document loading, manipulation, and rendering."""

    def __init__(self):
        self.doc: fitz.Document | None = None
        self.filepath: str | None = None
        self.modified: bool = False # Track if changes have been made

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
            print(f"Opened PDF: {filepath}")
            return True
        except Exception as e:
            print(f"Error opening PDF {filepath}: {e}")
            self.doc = None
            self.filepath = None
            return False

    def close_document(self):
        """Closes the currently open PDF document."""
        if self.doc:
            try:
                self.doc.close()
                print(f"Closed PDF: {self.filepath}")
            except Exception as e:
                print(f"Error closing PDF {self.filepath}: {e}")
            finally:
                self.doc = None
                self.filepath = None
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
                # Calculate the effective rotation
                effective_rotation = (page.rotation + rotation) % 360

                zoom_matrix = fitz.Matrix(scale, scale)
                rotation_matrix = fitz.Matrix(1, 1).prerotate(effective_rotation)
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
            self.modified = False
            # If saving to a new path, update the internal filepath
            if filepath:
                self.filepath = filepath
            print(f"Document saved to: {save_path}")
            return True
        except Exception as e:
            print(f"Error saving PDF to {save_path}: {e}")
            return False

    def rotate_page(self, page_num: int, angle: int):
        """Rotates a specific page by the given angle (90, 180, 270)."""
        if not self.doc or not (0 <= page_num < self.page_count):
            return False
        if angle not in [90, 180, 270]:
             print(f"Invalid rotation angle: {angle}. Must be 90, 180, or 270.")
             return False

        try:
            page = self.doc[page_num]
            current_rotation = page.rotation
            new_rotation = (current_rotation + angle) % 360
            page.set_rotation(new_rotation)
            self.modified = True
            print(f"Rotated page {page_num} by {angle} degrees. New rotation: {new_rotation}")
            return True
        except Exception as e:
            print(f"Error rotating page {page_num}: {e}")
            return False

    # --- Placeholder methods for other operations ---
    def add_blank_page(self, width: float = 595, height: float = 842, index: int = -1):
        """Adds a blank page."""
        if not self.doc: return False
        try:
            # Default A4 size in points
            self.doc.new_page(pno=index, width=width, height=height)
            self.modified = True
            print(f"Added blank page at index {index if index != -1 else self.page_count-1}")
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
            print(f"Deleted page {page_num}")
            return True
        except Exception as e:
            print(f"Error deleting page {page_num}: {e}")
            return False

    def merge_pdf(self, other_pdf_path: str):
        """Merges another PDF into the current one."""
        if not self.doc: return False
        try:
            with fitz.open(other_pdf_path) as other_doc:
                self.doc.insert_pdf(other_doc)
            self.modified = True
            print(f"Merged PDF: {other_pdf_path}")
            return True
        except Exception as e:
            print(f"Error merging PDF {other_pdf_path}: {e}")
            return False

    # Add more methods as needed (text insertion, annotation, etc.)
