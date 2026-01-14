import fitz  # PyMuPDF
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pdf_annotations')

class PDFAnnotations:
    """Handles PDF annotations such as notes, highlights, etc."""

    def __init__(self, pdf_handler):
        """Initialize the PDF annotations handler.

        Args:
            pdf_handler: The PDFHandler instance containing the document.
        """
        self.pdf_handler = pdf_handler
        self.annotations = {}  # Dictionary to store annotations by page

    def add_note(self, page_index, rect, content, username=None, color=(1, 1, 0)):
        """Add a sticky note (text) annotation to the PDF."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return None

        try:
            page = self.pdf_handler.doc[page_index]
            timestamp = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
            title = f"{username or 'Kullanıcı'} {timestamp}"
            
            point = fitz.Point(rect.x(), rect.y())
            annot = page.add_text_annot(point, content, icon="Comment")
            annot.set_info(title=title, content=content)
            annot.set_colors(stroke=color)
            annot.update()
            
            self.pdf_handler.modified = True
            return annot
        except Exception as e:
            logger.error(f"Error adding note annotation: {e}")
            return None

    def add_text_annotation(self, page_index, rect, content, fontsize=12, color=(0, 0, 0), fontname="helv"):
        """Add a FreeText annotation (visible text on page)."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return None
        try:
            page = self.pdf_handler.doc[page_index]
            fitz_rect = fitz.Rect(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            
            annot = page.add_freetext_annot(fitz_rect, content, fontsize=fontsize, text_color=color, fontname=fontname)
            annot.update(fontname=fontname)
            
            self.pdf_handler.modified = True
            return annot
        except Exception as e:
            logger.error(f"Error adding text annotation: {e}")
            return None

    def add_line_annotation(self, page_index, start_point, end_point, color=(1, 0, 0), width=1, arrow_type="none"):
        """Adds a line (as a polyline) annotation to the given page."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return None
        try:
            page = self.pdf_handler.doc[page_index]
            p1 = fitz.Point(start_point.x(), start_point.y())
            p2 = fitz.Point(end_point.x(), end_point.y())
            
            # Use polyline for better compatibility with set_vertices/movement
            annot = page.add_polyline_annot([p1, p2])
            annot.set_colors(stroke=color)
            annot.set_border(width=width)
            
            # Map arrow types to fitz constants
            if arrow_type == "start":
                annot.set_line_ends(fitz.PDF_ANNOT_LE_CLOSED_ARROW, fitz.PDF_ANNOT_LE_NONE)
            elif arrow_type == "end":
                annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
            elif arrow_type == "both":
                annot.set_line_ends(fitz.PDF_ANNOT_LE_CLOSED_ARROW, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
            else:
                annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_NONE)
            
            annot.update()
            
            self.pdf_handler.modified = True
            return annot
        except Exception as e:
            logger.error(f"Error adding line annotation: {e}")
            return None

    def add_circle_annotation(self, page_index, rect, color=(1, 0, 0), fill_color=None, width=2.0):
        """Add a circle (ellipse) annotation."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return None
        try:
            page = self.pdf_handler.doc[page_index]
            fitz_rect = fitz.Rect(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            
            annot = page.add_circle_annot(fitz_rect)
            annot.set_colors(stroke=color, fill=fill_color)
            annot.set_border(width=width)
            annot.update()
            
            self.pdf_handler.modified = True
            return annot
        except Exception as e:
            logger.error(f"Error adding circle annotation: {e}")
            return None

    def add_highlight_annotation(self, page_index, rect, color=(1, 1, 0)):
        """Add a highlight annotation."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return None
        try:
            page = self.pdf_handler.doc[page_index]
            fitz_rect = fitz.Rect(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            
            annot = page.add_highlight_annot(fitz_rect)
            annot.set_colors(stroke=color)
            annot.update()
            
            self.pdf_handler.modified = True
            return annot
        except Exception as e:
            logger.error(f"Error adding highlight annotation: {e}")
            return None

    def add_stamp_annotation(self, page_index, rect, stamp_index=0):
        """Add a stamp annotation."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return None
        try:
            page = self.pdf_handler.doc[page_index]
            fitz_rect = fitz.Rect(rect.x(), rect.y(), rect.x() + rect.width(), rect.y() + rect.height())
            
            annot = page.add_stamp_annot(fitz_rect, stamp=stamp_index)
            annot.update()
            
            self.pdf_handler.modified = True
            return annot
        except Exception as e:
            logger.error(f"Error adding stamp annotation: {e}")
            return None

    def remove_annotation(self, page_index, annot_index):
        """Remove an annotation from the PDF by its index on the page."""
        if not self.pdf_handler.doc or not (0 <= page_index < self.pdf_handler.page_count):
            return False
        try:
            page = self.pdf_handler.doc[page_index]
            annots = list(page.annots())
            if 0 <= annot_index < len(annots):
                page.delete_annot(annots[annot_index])
                self.pdf_handler.modified = True
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing annotation: {e}")
            return False
