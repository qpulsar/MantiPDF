from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

from core.pdf_handler import PDFHandler # Import PDFHandler for type hinting

class PDFViewer(QScrollArea): # Change to QScrollArea for scrolling large pages
    """Widget to display a PDF page within a scrollable area."""

    def __init__(self, parent=None):
        """Initialize the PDF viewer."""
        super().__init__(parent)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.layout = QVBoxLayout(self) # No longer need separate layout
        # self.layout.addWidget(self.image_label)
        # self.setLayout(self.layout)
        self.setWidget(self.image_label) # Set label as the scroll area's widget
        self.setWidgetResizable(True) # Allow the label to resize with the scroll area

        self.current_pixmap: QPixmap | None = None
        self.current_scale = 1.0
        self.pdf_handler: PDFHandler | None = None
        self.current_page_index: int = -1

    def display_page(self, pdf_handler: PDFHandler, page_index: int):
        """Display the given PDF page using the handler.

        Args:
            pdf_handler: The PDFHandler instance containing the document.
            page_index: The 0-based index of the page to display.
        """
        self.pdf_handler = pdf_handler
        self.current_page_index = page_index
        self.current_scale = 1.0 # Reset scale on page change

        pixmap = self.pdf_handler.get_page_pixmap(self.current_page_index, scale=self.current_scale)

        if pixmap:
            self.current_pixmap = pixmap
            self.image_label.setPixmap(self.current_pixmap)
        else:
            self.clear_display()
            self.image_label.setText(f"Error loading page {page_index + 1}.")

    def clear_display(self):
        """Clears the currently displayed page."""
        self.image_label.clear()
        self.image_label.setText("No PDF loaded or page selected.")
        self.current_pixmap = None
        self.pdf_handler = None
        self.current_page_index = -1
        self.current_scale = 1.0

    def update_display(self):
        """Re-renders the current page, e.g., after zoom or rotation."""
        if self.pdf_handler and self.current_page_index >= 0:
            # TODO: Add rotation parameter if viewer handles independent rotation
            pixmap = self.pdf_handler.get_page_pixmap(self.current_page_index, scale=self.current_scale)
            if pixmap:
                self.current_pixmap = pixmap
                self.image_label.setPixmap(self.current_pixmap)
            else:
                # Keep old pixmap? Or show error?
                print(f"Error updating display for page {self.current_page_index + 1}")
                # self.image_label.setText(f"Error updating display for page {self.current_page_index + 1}.")

    # --- Zoom Methods (Basic Implementation) ---
    def zoom_in(self):
        """Zooms in on the current page."""
        self.set_scale(self.current_scale * 1.2)

    def zoom_out(self):
        """Zooms out on the current page."""
        self.set_scale(self.current_scale / 1.2)

    def zoom_fit(self):
        """Zooms to fit the page within the viewer's viewport."""
        if not self.current_pixmap: return
        # Calculate scale to fit based on viewport size and original pixmap size
        # This requires the original, unscaled pixmap size ideally, or careful calculation
        # Basic approximation:
        viewport_size = self.viewport().size()
        pixmap_size = self.current_pixmap.size() / self.current_scale # Estimate original size

        if pixmap_size.width() == 0 or pixmap_size.height() == 0:
             return

        scale_w = viewport_size.width() / pixmap_size.width()
        scale_h = viewport_size.height() / pixmap_size.height()
        self.set_scale(min(scale_w, scale_h))

    def zoom_width(self):
        """Zooms to fit the page width to the viewer's viewport width."""
        if not self.current_pixmap: return
        viewport_width = self.viewport().width()
        pixmap_width = self.current_pixmap.width() / self.current_scale # Estimate original width

        if pixmap_width == 0: return

        self.set_scale(viewport_width / pixmap_width)

    def set_scale(self, scale):
        """Sets the zoom scale and updates the display."""
        # Add min/max scale limits if desired
        self.current_scale = max(0.1, min(scale, 10.0)) # Example limits
        self.update_display()
