from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QMenu
from PyQt6.QtGui import QPixmap, QImage, QCursor, QPainter, QPen, QColor, QPolygon
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRectF

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
        self.notes = []  # List to store notes on the current page
        self.note_markers = []  # List to store note markers on the current page
        self.add_note_mode = False  # Flag to indicate if we're in add note mode
        self.notes_dict = {}  # Dictionary mapping page index to list of note dicts
        
        # Enable mouse tracking for the image label
        self.image_label.setMouseTracking(True)
        # Install event filter to capture mouse events on the image label
        self.image_label.installEventFilter(self)

    def display_page(self, pdf_handler: PDFHandler, page_index: int):
        """Display the given PDF page using the handler.

        Args:
            pdf_handler: The PDFHandler instance containing the document.
            page_index: The 0-based index of the page to display.
        """
        # Clear existing notes when changing pages
        self.clear_notes()
        
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
        
        # Load notes for this page if any
        self.load_notes()

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
        
    # --- Note Management Methods ---
    def toggle_add_note_mode(self):
        """Toggle the add note mode."""
        self.add_note_mode = not self.add_note_mode
        if self.add_note_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)  # Change cursor to cross when in add note mode
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)  # Change cursor back to arrow
        return self.add_note_mode
        
    def add_note(self, position):
        """Add a note at the specified position.
        
        Args:
            position: The position on the PDF page where the note should be anchored.
        """
        import logging
        logger = logging.getLogger('pdf_viewer')
        
        logger.debug(f"Adding note at position: {position.x()}, {position.y()}")
        
        if not self.pdf_handler or self.current_page_index < 0:
            logger.error("PDF handler not available or invalid page index")
            return None
            
        # Create a new note widget
        try:
            logger.debug("Creating new NoteItem")
            note = NoteItem(self, position)
            
            # Set the note's anchor position to the clicked position
            note.anchor_position = position
            logger.debug(f"Set anchor position: {position.x()}, {position.y()}")
            
            # Position the note slightly above and to the right of the anchor point
            note_pos = QPoint(position.x() + 20, position.y() - 150)
            note.position = note_pos
            note.move(note_pos)
            logger.debug(f"Set note position: {note_pos.x()}, {note_pos.y()}")
            
            # Show the note
            note.show()
            logger.debug("Note widget shown")
            
            # Add the note to the list
            self.notes.append(note)
            logger.debug(f"Added note to list, total notes: {len(self.notes)}")
            
            # Add the note to the PDF document
            try:
                logger.debug(f"Adding note to PDF document at page {self.current_page_index}")
                result = self.pdf_handler.add_note(self.current_page_index, position, note.note_text, note.username)
                logger.debug(f"Result of add_note: {result}")
            except Exception as e:
                logger.error(f"Error adding note to PDF document: {e}")
            
            # Emit the note_added signal
            self.note_added.emit(note)
            logger.debug("Emitted note_added signal")
            
            return note
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return None
        
    def remove_note(self, note):
        """Remove a note from the viewer.
        
        Args:
            note: The note to remove.
        """
        if note in self.notes:
            # Get the index of the note
            note_index = self.notes.index(note)
            
            # Remove the note from the list
            self.notes.remove(note)
            
            # Remove the note from the PDF document
            if self.pdf_handler and self.current_page_index >= 0:
                self.pdf_handler.remove_note(self.current_page_index, note_index)
            
            # Emit the note_removed signal
            self.note_removed.emit(note)
            
    def clear_notes(self):
        """Clear all notes from the viewer."""
        # Make a copy of the list to avoid modification during iteration
        notes_copy = self.notes.copy()
        for note in notes_copy:
            note.deleteLater()
        self.notes.clear()
        
    def save_notes(self):
        """Save notes for the current page."""
        if not self.pdf_handler or self.current_page_index < 0 or not self.notes:
            return
            
        # Notes are automatically saved to the PDF document when added
        # and when the document is saved
        print("Saving notes:", self.notes_dict)
        # TODO: Integrate with pdf_handler to embed notes into the PDF document

    def load_notes(self):
        """Load notes for the current page."""
        if not self.pdf_handler or self.current_page_index < 0:
            return
            
        # Get notes for the current page from the PDF handler
        notes_data = self.pdf_handler.get_notes(self.current_page_index)
        
        # Create note widgets for each note
        for note_data in notes_data:
            if note_data["type"] == "note":
                # Create a rectangle from the note data
                rect = note_data["rect"]
                position = QPoint(rect[0] + 10, rect[1] + 10)  # Center of the rectangle
                
                # Create a new note
                note = NoteItem(self, position)
                note.anchor_position = position
                
                # Position the note slightly above and to the right of the anchor point
                note_pos = QPoint(position.x() + 20, position.y() - 150)
                note.position = note_pos
                note.move(note_pos)
                
                # Set the note data
                note.username = note_data.get("username", "Kullanıcı")
                note.note_text = note_data.get("content", "")
                note.text_edit.setText(note.note_text)
                
                # Update the header label
                timestamp = note_data.get("creation_date", "")
                if timestamp:
                    note.header_label.setText(f"{note.username} {timestamp}")
                
                # Show the note
                note.show()
                
                # Add the note to the list
                self.notes.append(note)

    def mousePressEvent(self, event):
        if self.add_note_mode:
            # Get current page index
            page = self.current_page_index
            if page not in self.notes_dict:
                self.notes_dict[page] = []
            # Add a new note at the clicked position
            self.notes_dict[page].append({"pos": event.pos() })
            # Optionally, disable note mode after adding one note
            self.add_note_mode = False
            self.update()  # trigger repaint
            # TODO: Emit a signal to update the sidebar note list if needed
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        qp = QPainter(self.viewport())
        # Draw note markers for the current page
        current_page = self.current_page_index
        if current_page in self.notes_dict:
            qp.setBrush(QColor('red'))
            for note in self.notes_dict[current_page]:
                # Draw a small circle at the note position (radius = 5)
                qp.drawEllipse(note["pos"], 5, 5)

    # --- Event Handling ---
    def eventFilter(self, obj, event):
        """Filter events for the image label."""
        if obj is self.image_label:
            # Handle mouse press events
            if event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                # Store the last clicked position
                self.last_clicked_position = event.pos()
                if self.add_note_mode:
                    # Add a circle at the clicked position
                    pos = event.pos()
                    self.add_circle_annotation(pos)
                    # Turn off add note mode after adding a circle
                    self.toggle_add_note_mode()
                    return True
                    
            # Handle mouse move events
            elif event.type() == event.Type.MouseMove:
                # You can add hover effects or other interactions here
                pass
                
            # Handle context menu events
            elif event.type() == event.Type.ContextMenu:
                # Show context menu
                menu = QMenu(self)
                add_note_action = menu.addAction("Not Ekle")
                add_note_action.triggered.connect(lambda: self.add_note(event.pos()))
                menu.exec(QCursor.pos())
                return True
                
        # Pass the event to the parent class
        return super().eventFilter(obj, event)

    def get_current_rect(self):
        """Get the current rectangle on the PDF page."""
        # Return the last clicked rectangle
        if hasattr(self, 'last_clicked_position'):
            x, y = self.last_clicked_position.x(), self.last_clicked_position.y()
            return QRectF(x - 10, y - 10, 20, 20)  # 20x20 rectangle centered at position
        else:
            return QRectF(0, 0, 20, 20)  # Default rectangle if no click has occurred

    def add_circle_annotation(self, position):
        """Add a circle annotation at the specified position.
        
        Args:
            position: The position on the PDF page where the circle should be anchored.
        """
        import logging
        logger = logging.getLogger('pdf_viewer')
        
        logger.debug(f"Adding circle annotation at position: {position.x()}, {position.y()}")
        
        if not self.pdf_handler or self.current_page_index < 0:
            logger.error("PDF handler not available or invalid page index")
            return None
            
        # Get the current page index
        page_index = self.current_page_index
        logger.debug(f"Current page index: {page_index}")

        # Create a small rectangle around the position
        try:
            x, y = position.x(), position.y()
            rect = QRectF(x - 10, y - 10, 20, 20)  # 20x20 rectangle centered at position
            logger.debug(f"Created QRectF: x={rect.x()}, y={rect.y()}, width={rect.width()}, height={rect.height()}")
        except Exception as e:
            logger.error(f"Error creating QRectF: {e}")
            return None

        # Call the add_circle_annotation function
        try:
            logger.debug("Calling pdf_annotations.add_circle_annotation")
            result = self.pdf_handler.pdf_annotations.add_circle_annotation(page_index, rect, "Circle Annotation")
            logger.debug(f"Result of add_circle_annotation: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in add_circle_annotation: {e}")
            return None

    def add_circle_annotation(self, rect):
        """Add a circle annotation to the current page using pdf_handler if available."""
        import logging
        logger = logging.getLogger('pdf_viewer')
        logger.debug('Calling pdf_annotations.add_circle_annotation')
        if hasattr(self.pdf_handler, 'pdf_annotations') and hasattr(self.pdf_handler.pdf_annotations, 'add_circle_annotation'):
            try:
                self.pdf_handler.pdf_annotations.add_circle_annotation(self.current_page_index, rect)
            except Exception as e:
                logger.error(f'Error in add_circle_annotation: {e}')
        else:
            logger.error('PDFHandler object has no attribute "pdf_annotations"')
