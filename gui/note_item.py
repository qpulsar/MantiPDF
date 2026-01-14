from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPolygon
from PyQt6.QtCore import Qt, QPoint, QDateTime, QSize
import getpass

class NoteItem(QWidget):
    """Widget to display a note on a PDF page."""

    def __init__(self, parent=None, position=None, username=None):
        """Initialize the note widget.

        Args:
            parent: The parent widget.
            position: The position of the note on the PDF page.
            username: The username of the note creator.
        """
        super().__init__(parent)
        self.parent = parent
        self.position = position or QPoint(100, 100)  # Default position
        self.anchor_position = self.position  # Position where the note is anchored on the PDF
        self.username = username or getpass.getuser()  # Get current username if not provided
        self.timestamp = QDateTime.currentDateTime()  # Current time
        self.note_text = ""  # Note content
        self.is_selected = False  # Selection state
        self.is_being_moved = False  # Moving state
        self.move_start_pos = None  # Starting position for move operation
        
        # Set fixed size for the note
        self.setFixedSize(250, 150)
        
        # Set position
        self.move(self.position)
        
        # Set up the UI
        self.setup_ui()
        
        # Make the widget transparent for mouse events except for its children
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Set stylesheet
        self.setStyleSheet("""
            QWidget#noteWidget {
                background-color: #FFFF88;
                border: 1px solid #DDDD00;
                border-radius: 5px;
            }
            QLabel#headerLabel {
                background-color: #EEEE00;
                color: #000000;
                padding: 2px;
                font-weight: bold;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTextEdit {
                background-color: #FFFF99;
                border: none;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QPushButton {
                background-color: #EEEE00;
                border: 1px solid #DDDD00;
                border-radius: 2px;
                padding: 2px;
                max-width: 20px;
                max-height: 20px;
            }
            QPushButton:hover {
                background-color: #FFFF00;
            }
        """)

    def setup_ui(self):
        """Set up the UI components of the note."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header with username and timestamp
        self.header_widget = QWidget()
        self.header_widget.setObjectName("headerLabel")
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(5, 2, 5, 2)
        
        # Username and timestamp
        self.header_label = QLabel(f"{self.username} {self.timestamp.toString('dd.MM.yyyy, HH:mm:ss')}")
        self.header_label.setObjectName("headerLabel")
        
        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(16, 16)
        self.close_button.clicked.connect(self.close_note)
        
        # Add widgets to header layout
        self.header_layout.addWidget(self.header_label)
        self.header_layout.addWidget(self.close_button)
        
        # Text edit for note content
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Not eklemek için buraya yazın...")
        self.text_edit.textChanged.connect(self.on_text_changed)
        
        # Add widgets to main layout
        self.layout.addWidget(self.header_widget)
        self.layout.addWidget(self.text_edit)
        
        # Set the widget as the main note widget
        self.setObjectName("noteWidget")

    def on_text_changed(self):
        """Handle text changes in the note."""
        self.note_text = self.text_edit.toPlainText()
        
        # Update the note in the PDF document
        if self.parent and hasattr(self.parent, 'pdf_handler') and self.parent.pdf_handler:
            # Find the index of this note in the parent's notes list
            if self in self.parent.notes:
                try:
                    note_index = self.parent.notes.index(self)
                    if self.parent.current_page_index >= 0:
                        # Remove the old note and add a new one with updated content
                        try:
                            self.parent.pdf_handler.remove_note(self.parent.current_page_index, note_index)
                        except Exception:
                            pass
                        
                        try:
                            self.parent.pdf_handler.add_note(self.parent.current_page_index, self.anchor_position, self.note_text, self.username)
                        except Exception:
                            pass
                except Exception:
                    pass

    def close_note(self):
        """Close and remove the note."""
        if self.parent:
            self.parent.remove_note(self)
        self.deleteLater()

    def paintEvent(self, event):
        """Paint the note and the connection line."""
        super().paintEvent(event)
        
        # Paint the connection line between the note and the anchor point
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate the start point (on the note) and end point (on the PDF)
        # The start point is at the bottom center of the note
        start_point = QPoint(self.width() // 2, self.height())
        
        # The end point is the anchor position relative to the note's position
        end_point = self.mapFromParent(self.anchor_position)
        
        # Draw the connection line
        pen = QPen(QColor(255, 255, 0), 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        # Create a small triangle at the anchor point to make it look like a speech bubble
        triangle = QPolygon()
        triangle.append(end_point)
        triangle.append(QPoint(end_point.x() - 5, end_point.y() - 10))
        triangle.append(QPoint(end_point.x() + 5, end_point.y() - 10))
        
        # Draw the line and the triangle
        painter.drawLine(start_point, QPoint(end_point.x(), end_point.y() - 10))
        painter.setBrush(QColor(255, 255, 0))
        painter.drawPolygon(triangle)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_being_moved = True
            self.move_start_pos = event.pos()
            self.raise_()

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.is_being_moved and self.move_start_pos:
            delta = event.pos() - self.move_start_pos
            self.move(self.pos() + delta)
            # Update the position property
            self.position = self.pos()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_being_moved = False
            self.move_start_pos = None

    def get_data(self):
        """Get the note data for saving."""
        return {
            "position": (self.position.x(), self.position.y()),
            "anchor_position": (self.anchor_position.x(), self.anchor_position.y()),
            "username": self.username,
            "timestamp": self.timestamp.toString(Qt.DateFormat.ISODate),
            "note_text": self.note_text
        }

    def set_data(self, data):
        """Set the note data from saved data."""
        if "position" in data:
            self.position = QPoint(*data["position"])
            self.move(self.position)
        if "anchor_position" in data:
            self.anchor_position = QPoint(*data["anchor_position"])
        if "username" in data:
            self.username = data["username"]
        if "timestamp" in data:
            self.timestamp = QDateTime.fromString(data["timestamp"], Qt.DateFormat.ISODate)
        if "note_text" in data:
            self.note_text = data["note_text"]
            self.text_edit.setText(self.note_text)
        
        # Update the header label
        self.header_label.setText(f"{self.username} {self.timestamp.toString('dd.MM.yyyy, HH:mm:ss')}")