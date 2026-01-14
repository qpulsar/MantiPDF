from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QMenu
from PyQt6.QtGui import QPixmap, QImage, QCursor, QPainter, QPen, QColor, QPolygon
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QRectF

from core.pdf_handler import PDFHandler # Import PDFHandler for type hinting
from gui.note_item import NoteItem # Import the NoteItem class

class PDFViewer(QScrollArea): # Change to QScrollArea for scrolling large pages
    """Widget to display a PDF page within a scrollable area."""
    
    # Signal to notify when a note is added
    note_added = pyqtSignal(NoteItem)
    # Signal to notify when a note is removed
    note_removed = pyqtSignal(NoteItem)
    # Signal to notify when a note is opened
    note_opened = pyqtSignal(NoteItem)
    # Signals for overscroll page navigation
    overscrollNext = pyqtSignal()
    overscrollPrevious = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the PDF viewer."""
        super().__init__(parent)
        self.parent_window = parent
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
        
        # Note related attributes
        self.notes = []  # List to store note markers on the current page
        self.annotation_mode = None  # Current active tool (note, text, line, circle, highlight, stamp)
        
        # Drawing related attributes for rubber-banding
        self.start_pos = None
        self.current_pos = None
        self.is_drawing = False
        
        # Overscroll tracking
        self.overscroll_delta = 0
        self.overscroll_threshold = 400  # Cumulative delta needed to trigger page change
        self.is_at_top = True
        self.is_at_bottom = False
        
        # Enable mouse tracking for the image label
        self.image_label.setMouseTracking(True)
        # Install event filter to capture mouse events on the image label
        self.image_label.installEventFilter(self)

    def display_page(self, pdf_handler: PDFHandler, page_index: int):
        """Display the given PDF page using the handler."""
        # Clear existing temporary markers when changing pages
        self.clear_markers()
        
        self.pdf_handler = pdf_handler
        self.current_page_index = page_index
        self.overscroll_delta = 0
        self.image_label.move(0, 0)

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
        """Re-renders the current page and updates the image label."""
        if self.pdf_handler and self.current_page_index >= 0:
            pixmap = self.pdf_handler.get_page_pixmap(self.current_page_index, scale=self.current_scale)
            if pixmap:
                self.current_pixmap = pixmap
                self.image_label.setPixmap(self.current_pixmap)

    # --- Tool Management ---
    def set_annotation_mode(self, mode):
        """Sets the current annotation tool."""
        self.annotation_mode = mode
        if mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def clear_markers(self):
        """Clear temporary UI markers (not necessary if we re-render PDF)."""
        pass

    def save_notes(self):
        """Placeholder for backward compatibility in main_window.py."""
        pass

    # --- Event Handling ---
    def eventFilter(self, obj, event):
        """Filter events for the image label to handle annotations."""
        if obj is self.image_label:
            if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                if self.annotation_mode:
                    self.start_pos = event.pos()
                    self.current_pos = event.pos()
                    self.is_drawing = True
                    return True
            
            elif event.type() == event.Type.MouseMove and self.is_drawing:
                self.current_pos = event.pos()
                self.image_label.update()  # Trigger repaint for rubber band
                return True
            
            elif event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton and self.is_drawing:
                self.is_drawing = False
                self.finish_annotation(event.pos())
                self.image_label.update()
                return True

            elif event.type() == event.Type.Paint and self.is_drawing:
                # Let the default paint happen, then draw rubber band on top
                pass # Logic moves to a custom paint method if we were subclassing label
                # Since we use eventFilter on a label, we catch Paint of the label
                # But it's better to use a custom widget or draw on a copy of pixmap
                # For simplicity, let's trigger a logic to draw on the label:
                self.draw_rubber_band()

        return super().eventFilter(obj, event)

    def draw_rubber_band(self):
        """Draws a preview of the annotation while dragging."""
        if not self.is_drawing or not self.start_pos or not self.current_pos:
            return

        painter = QPainter(self.image_label)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine)
        painter.setPen(pen)

        rect = QRectF(QPointF(self.start_pos), QPointF(self.current_pos)).normalized()

        if self.annotation_mode == "line":
            painter.drawLine(self.start_pos, self.current_pos)
        elif self.annotation_mode == "circle":
            painter.drawEllipse(rect)
        elif self.annotation_mode == "highlight":
            painter.setBrush(QColor(255, 255, 0, 100))
            painter.drawRect(rect)
        elif self.annotation_mode == "stamp":
            painter.drawRect(rect)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "STAMP")
        elif self.annotation_mode in ["note", "text"]:
             painter.drawRect(rect)

        painter.end()

    def finish_annotation(self, end_pos):
        """Finalize the annotation and add it to the PDF."""
        if not self.pdf_handler or self.current_page_index < 0:
            return

        # Calculate offset due to centering in image_label
        offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
        offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2

        # Convert screen coordinates back to PDF units (adjusted for offset and scale)
        s_pos = QPoint(int((self.start_pos.x() - offset_x) / self.current_scale), 
                      int((self.start_pos.y() - offset_y) / self.current_scale))
        e_pos = QPoint(int((end_pos.x() - offset_x) / self.current_scale), 
                      int((end_pos.y() - offset_y) / self.current_scale))
        rect = QRectF(QPointF(s_pos), QPointF(e_pos)).normalized()

        # Handle zero-sized or very small rectangles (e.g., single clicks)
        is_small = rect.width() < 5 and rect.height() < 5
        if is_small:
            if self.annotation_mode in ["note", "text", "stamp", "circle"]:
                # Default size for point-like annotations
                rect = QRectF(s_pos.x(), s_pos.y(), 50, 50)
            else:
                # For line or highlight, ignore very small movements
                return

        if self.annotation_mode == "note":
            # Just add a sticky note at the click position
            self.pdf_handler.add_note(self.current_page_index, rect, "Yeni Not")
        elif self.annotation_mode == "text":
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "Metin Ekle", "Metin giriniz:")
            if ok and text:
                self.pdf_handler.add_textbox(self.current_page_index, rect, text)
        elif self.annotation_mode == "line":
            if is_small: return
            self.pdf_handler.add_line(self.current_page_index, s_pos, e_pos)
        elif self.annotation_mode == "circle":
            self.pdf_handler.add_circle(self.current_page_index, rect)
        elif self.annotation_mode == "highlight":
            if is_small: return
            self.pdf_handler.add_highlight(self.current_page_index, rect)
        elif self.annotation_mode == "stamp":
            self.pdf_handler.add_stamp(self.current_page_index, rect, 0) # 0 = Approved

        # Clear mode after application if desired, or keep it for multiple additions
        # self.set_annotation_mode(None)
        
        # Re-render to show the new annotation
        self.update_display()

    # --- Zoom Methods ---
    def zoom_in(self):
        self.set_scale(self.current_scale * 1.2)

    def zoom_out(self):
        self.set_scale(self.current_scale / 1.2)

    def set_scale(self, scale):
        self.current_scale = max(0.1, min(scale, 10.0))
        self.update_display()

    def zoom_fit(self):
        if not self.current_pixmap: return
        viewport_size = self.viewport().size()
        pixmap_size = self.current_pixmap.size() / self.current_scale
        if pixmap_size.width() == 0 or pixmap_size.height() == 0: return
        scale_w = viewport_size.width() / pixmap_size.width()
        scale_h = viewport_size.height() / pixmap_size.height()
        self.set_scale(min(scale_w, scale_h))

    def zoom_width(self):
        if not self.current_pixmap: return
        viewport_width = self.viewport().width()
        pixmap_width = self.current_pixmap.width() / self.current_scale
        if pixmap_width == 0: return
        self.set_scale(viewport_width / pixmap_width)

    # --- Wheeler event for overscroll ---
    def wheelEvent(self, event):
        v_bar = self.verticalScrollBar()
        self.is_at_top = (v_bar.value() == v_bar.minimum())
        self.is_at_bottom = (v_bar.value() == v_bar.maximum())
        delta = event.angleDelta().y()

        if (delta > 0 and self.overscroll_delta < 0) or (delta < 0 and self.overscroll_delta > 0):
            self.overscroll_delta = 0
            self.image_label.move(0, 0)
            
        if self.is_at_bottom and delta < 0:
            self.overscroll_delta += delta
            shift = max(-30, self.overscroll_delta // 10)
            self.image_label.move(0, shift)
            if abs(self.overscroll_delta) >= self.overscroll_threshold:
                self.overscrollNext.emit()
                self.overscroll_delta = 0
                self.image_label.move(0, 0)
            event.accept()
            return
        elif self.is_at_top and delta > 0:
            self.overscroll_delta += delta
            shift = min(30, self.overscroll_delta // 10)
            self.image_label.move(0, shift)
            if abs(self.overscroll_delta) >= self.overscroll_threshold:
                self.overscrollPrevious.emit()
                self.overscroll_delta = 0
                self.image_label.move(0, 0)
            event.accept()
            return

        if self.overscroll_delta != 0:
            self.overscroll_delta = 0
            self.image_label.move(0, 0)
        super().wheelEvent(event)
