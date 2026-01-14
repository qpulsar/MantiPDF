from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QMenu
from PyQt6.QtGui import QPixmap, QImage, QCursor, QPainter, QPen, QColor, QPolygon
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QRectF
import fitz
import re

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
    # Signal emitted when an annotation is selected (type_name, properties)
    annotation_selected = pyqtSignal(str, dict)
    # Signal emitted when selection is cleared
    annotation_deselected = pyqtSignal()

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
        self.current_fitz_page = None # Keep the fitz.Page object alive for annotations
        
        # Note related attributes
        self.notes = []  # List to store note markers on the current page
        self.annotation_mode = None  # Current active tool (note, text, line, circle, highlight, stamp)
        self.selected_annot = None # Reference to the selected fitz.Annot
        self.current_properties = {
            "stroke_color": QColor(255, 0, 0),
            "fill_color": QColor(0, 0, 0, 0),
            "thickness": 2,
            "font_size": 12,
            "font_family": "helv",
            "arrow_type": "none"
        }
        
        # Drawing related attributes for rubber-banding
        self.start_pos = None
        self.current_pos = None
        self.is_drawing = False
        self.is_dragging_annot = False
        self.drag_start_pdf_pos = None # Point in PDF units where drag started
        self.drag_displacement_pdf = (0, 0) # Current displacement (dx, dy)
        self.original_annot_rect = None # Original rect of the annotation
        self.original_vertices = None # Original vertices if it's a line/poly
        
        # Selection feedback
        self.selection_color = QColor(0, 120, 215)
        self.handle_size = 8
        
        # Resize handle tracking (0-7: TL, T, TR, R, BR, B, BL, L)
        self.active_resize_handle = -1
        self.is_resizing = False
        self.resize_start_rect = None
        
        # Per-tool property storage
        self.tool_properties = {
            "note": {"stroke_color": QColor(255, 200, 0), "fill_color": QColor(0,0,0,0), "thickness": 1, "font_size": 12, "font_family": "helv", "arrow_type": "none"},
            "text": {"stroke_color": QColor(0, 0, 0), "fill_color": QColor(0,0,0,0), "thickness": 1, "font_size": 12, "font_family": "helv", "arrow_type": "none"},
            "line": {"stroke_color": QColor(255, 0, 0), "fill_color": QColor(0,0,0,0), "thickness": 2, "font_size": 12, "font_family": "helv", "arrow_type": "none"},
            "circle": {"stroke_color": QColor(255, 0, 0), "fill_color": QColor(0,0,0,0), "thickness": 2, "font_size": 12, "font_family": "helv", "arrow_type": "none"},
            "highlight": {"stroke_color": QColor(255, 255, 0), "fill_color": QColor(0,0,0,0), "thickness": 1, "font_size": 12, "font_family": "helv", "arrow_type": "none"},
            "stamp": {"stroke_color": QColor(0, 128, 0), "fill_color": QColor(0,0,0,0), "thickness": 1, "font_size": 12, "font_family": "helv", "arrow_type": "none"},
        }
        
        # Overscroll tracking
        self.overscroll_delta = 0
        self.overscroll_threshold = 400  # Cumulative delta needed to trigger page change
        self.is_at_top = True
        self.is_at_bottom = False
        
        # Enable mouse tracking for the image label
        self.image_label.setMouseTracking(True)
        # Install event filter to capture mouse events on the image label
        self.image_label.installEventFilter(self)
        
        # Allow capturing keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.installEventFilter(self)

    def display_page(self, pdf_handler: PDFHandler, page_index: int):
        """Display the given PDF page using the handler."""
        # Clear existing temporary markers when changing pages
        self.clear_markers()
        
        self.pdf_handler = pdf_handler
        self.current_page_index = page_index
        self.current_fitz_page = self.pdf_handler.doc[page_index] if self.pdf_handler.doc else None
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
        self.current_fitz_page = None
        self.current_scale = 1.0

    def update_display(self):
        """Re-renders the current page and updates the image label."""
        if self.pdf_handler and self.current_page_index >= 0:
            # Re-bind selection if it exists using xref to prevent ReferenceError
            old_xref = None
            try:
                if self.selected_annot:
                    old_xref = self.selected_annot.xref
            except:
                pass

            self.current_fitz_page = self.pdf_handler.doc[self.current_page_index] if self.pdf_handler.doc else None
            
            if old_xref and self.current_fitz_page:
                self.selected_annot = None
                try:
                    for annot in self.current_fitz_page.annots():
                        if annot.xref == old_xref:
                            self.selected_annot = annot
                            break
                except Exception as e:
                    print(f"Error re-binding annotation: {e}")

            pixmap = self.pdf_handler.get_page_pixmap(self.current_page_index, scale=self.current_scale)
            if pixmap:
                self.current_pixmap = pixmap
                self.image_label.setPixmap(self.current_pixmap)

    # --- Tool Management ---
    def set_annotation_mode(self, mode):
        """Sets the current annotation tool."""
        old_mode = self.annotation_mode
        self.annotation_mode = mode
        
        # Clear selection when changing tools
        if self.selected_annot:
            self.selected_annot = None
            self.annotation_deselected.emit()
        
        # Load properties for the new tool from storage
        if mode and mode != "select" and mode in self.tool_properties:
            self.current_properties = self.tool_properties[mode].copy()
        
        if mode:
            if mode == "select":
                self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        self.image_label.update()

    def set_properties(self, props):
        """Updates the current styling properties."""
        self.current_properties = props.copy()
        
        # Store properties for the current tool so new annotations use them
        if self.annotation_mode and self.annotation_mode != "select" and self.annotation_mode in self.tool_properties:
            self.tool_properties[self.annotation_mode] = props.copy()
        
        # If an annotation is selected, update its properties immediately
        if self.selected_annot and self.annotation_mode == "select":
            self.apply_properties_to_annot(self.selected_annot)
            self.update_display()

    def apply_properties_to_annot(self, annot):
        """Applies current properties to a fitz.Annot object."""
        try:
            if not annot or not annot.this:
                if annot == self.selected_annot: # Check if the invalid annot is the selected one
                    self.selected_annot = None
                return
            
            # Access a property to ensure object is still bound/alive
            _ = annot.rect
        except (ReferenceError, Exception):
            # If the object is no longer valid (e.g., deleted or weakly referenced)
            if annot == self.selected_annot:
                self.selected_annot = None
            return

        try:
            p = self.current_properties
            # Normalize colors (0-1)
            stroke = (p["stroke_color"].red()/255, p["stroke_color"].green()/255, p["stroke_color"].blue()/255)
            fill = None
            if p["fill_color"].alpha() > 0:
                fill = (p["fill_color"].red()/255, p["fill_color"].green()/255, p["fill_color"].blue()/255)
            
            annot.set_colors(stroke=stroke, fill=fill)
            
            # Use alpha of the fill color as the global opacity for the annotation
            # (Note: PDF doesn't easily support separate stroke/fill opacity for standard annots)
            if p["fill_color"].alpha() < 255 and p["fill_color"].alpha() > 0:
                annot.set_opacity(p["fill_color"].alpha() / 255)
            elif p["fill_color"].alpha() == 0:
                annot.set_opacity(1.0) # Always fully opaque if no fill, but fill is None anyway
            else:
                annot.set_opacity(1.0)

            annot.set_border(width=p["thickness"])
            
            # Handle type specific properties
            if annot.type[0] == 2: # FreeText
                # For FreeText, background color is passed to update() as fill_color
                annot.update(fontsize=p["font_size"], fontname=p["font_family"], 
                             text_color=stroke, fill_color=fill)
            elif annot.type[0] == 3: # Line
                if p["arrow_type"] == "start":
                    annot.set_line_ends(fitz.PDF_ANNOT_LE_CLOSED_ARROW, fitz.PDF_ANNOT_LE_NONE)
                elif p["arrow_type"] == "end":
                    annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
                elif p["arrow_type"] == "both":
                    annot.set_line_ends(fitz.PDF_ANNOT_LE_CLOSED_ARROW, fitz.PDF_ANNOT_LE_CLOSED_ARROW)
                else:
                    annot.set_line_ends(fitz.PDF_ANNOT_LE_NONE, fitz.PDF_ANNOT_LE_NONE)
            
            annot.update()
            self.pdf_handler.modified = True
        except Exception as e:
            # Only reset selection if it's a critical reference error
            if "weakly-referenced" in str(e) or "ReferenceError" in str(type(e)):
                self.selected_annot = None
            else:
                print(f"Error applying properties to annotation: {e}")

    def get_annot_properties(self, annot):
        """Extracts current properties from a fitz.Annot object."""
        props = self.current_properties.copy()
        try:
            if not annot or not annot.this:
                return props

            colors = annot.colors
            if "stroke" in colors and colors["stroke"]:
                s = colors["stroke"]
                props["stroke_color"] = QColor(int(s[0]*255), int(s[1]*255), int(s[2]*255))
            
            if "fill" in colors and colors["fill"]:
                f = colors["fill"]
                # Use annot.opacity if available to recreate the semi-transparent feel
                alpha = int(annot.opacity * 255) if annot.opacity is not None else 255
                props["fill_color"] = QColor(int(f[0]*255), int(f[1]*255), int(f[2]*255), alpha)
            else:
                props["fill_color"] = QColor(0, 0, 0, 0)
            
            props["thickness"] = int(annot.border.get("width", 1))

            if annot.type[0] == 2: # FreeText
                # fitz properties for FreeText can be tricky. Primary source for Text Color and Font is DA string.
                da = annot.info.get("DA", "")
                if da:
                    # Parse Font: /Name size Tf
                    match_font = re.search(r'/(\w+)\s+([\d.]+)\s+Tf', da)
                    if match_font:
                        font_name = match_font.group(1).lower()
                        # Map common PDF font abbreviations to internal names if needed
                        # For now, just pass it through or normalized
                        props["font_family"] = font_name
                        props["font_size"] = int(float(match_font.group(2)))
                    
                    # Parse Text Color (RGB): r g b rg
                    match_rgb = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
                    if match_rgb:
                        r, g, b = float(match_rgb.group(1)), float(match_rgb.group(2)), float(match_rgb.group(3))
                        props["stroke_color"] = QColor(int(r*255), int(g*255), int(b*255))
                    else:
                        # Parse Text Color (Gray): g g
                        match_gray = re.search(r'([\d.]+)\s+g', da)
                        if match_gray:
                            g = float(match_gray.group(1))
                            props["stroke_color"] = QColor(int(g*255), int(g*255), int(g*255))
                        else:
                            # Parse Text Color (CMYK): c m y k k (less common for simple viewer but good to check)
                            # Or default to black if no color operator found in DA but font is there
                            pass
                
                # Check for border color equivalent to stroke if DA didn't have it (fallback)
                if "stroke" in colors and colors["stroke"] and "stroke_color" not in props:
                     s = colors["stroke"]
                     props["stroke_color"] = QColor(int(s[0]*255), int(s[1]*255), int(s[2]*255))

            if annot.type[0] == 3: # Line
                ends = annot.line_ends
                if ends[0] == fitz.PDF_ANNOT_LE_CLOSED_ARROW and ends[1] == fitz.PDF_ANNOT_LE_NONE:
                    props["arrow_type"] = "start"
                elif ends[0] == fitz.PDF_ANNOT_LE_NONE and ends[1] == fitz.PDF_ANNOT_LE_CLOSED_ARROW:
                    props["arrow_type"] = "end"
                elif ends[0] == fitz.PDF_ANNOT_LE_CLOSED_ARROW and ends[1] == fitz.PDF_ANNOT_LE_CLOSED_ARROW:
                    props["arrow_type"] = "both"
                else:
                    props["arrow_type"] = "none"
                    
        except Exception as e:
            print(f"Error getting properties from annotation: {e}")
        
        return props

    def clear_markers(self):
        """Clear temporary UI markers (not necessary if we re-render PDF)."""
        pass

    def save_notes(self):
        """Placeholder for backward compatibility in main_window.py."""
        pass

    def show_context_menu(self, annot, global_pos):
        """Shows a context menu for the given annotation."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        annot_type = annot.type[0]
        annot_type_name = annot.type[1]
        
        # Common actions
        delete_action = menu.addAction("Sil")
        delete_action.triggered.connect(lambda: self.delete_annotation(annot))
        
        menu.addSeparator()
        
        # Type-specific actions
        if annot_type == 2:  # FreeText
            edit_action = menu.addAction("Metni Düzenle")
            edit_action.triggered.connect(lambda: self.edit_freetext(annot))
        
        elif annot_type == 3:  # Line
            arrow_menu = menu.addMenu("Ok Tipi")
            for arrow_type in ["none", "start", "end", "both"]:
                action = arrow_menu.addAction(arrow_type.capitalize())
                action.triggered.connect(lambda checked, at=arrow_type: self.set_line_arrow(annot, at))
        
        elif annot_type in [4, 5]:  # Circle, Square
            toggle_fill_action = menu.addAction("Dolguyu Değiştir")
            toggle_fill_action.triggered.connect(lambda: self.toggle_fill(annot))
        
        menu.exec(global_pos)
    
    def delete_annotation(self, annot):
        """Deletes the given annotation."""
        try:
            self.current_fitz_page.delete_annot(annot)
            self.pdf_handler.modified = True
            self.selected_annot = None
            self.annotation_deselected.emit()
            self.update_display()
            self.parent_window.status_bar.showMessage("Nesne silindi.")
        except Exception as e:
            print(f"Error deleting annotation: {e}")
    
    def edit_freetext(self, annot):
        """Opens a dialog to edit FreeText content."""
        from PyQt6.QtWidgets import QInputDialog
        current_text = annot.info.get("content", "")
        new_text, ok = QInputDialog.getText(self, "Metni Düzenle", "Yeni metin:", text=current_text)
        if ok and new_text:
            try:
                annot.set_info(content=new_text)
                annot.update()
                self.pdf_handler.modified = True
                self.update_display()
            except Exception as e:
                print(f"Error editing text: {e}")
    
    def set_line_arrow(self, annot, arrow_type):
        """Sets the arrow type for a line annotation."""
        try:
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
            self.update_display()
        except Exception as e:
            print(f"Error setting arrow type: {e}")
    
    def toggle_fill(self, annot):
        """Toggles fill color on/off for shape annotations."""
        try:
            colors = annot.colors
            if colors.get("fill"):
                annot.set_colors(fill=None)
            else:
                # Use current stroke color as fill
                stroke = colors.get("stroke", (1, 0, 0))
                annot.set_colors(fill=stroke)
            annot.update()
            self.pdf_handler.modified = True
            self.update_display()
        except Exception as e:
            print(f"Error toggling fill: {e}")
    
    def reflow_freetext_annotation(self, annot):
        """Re-creates a FreeText annotation to reflow text to the new rect."""
        try:
            # Get current properties
            rect = annot.rect
            content = annot.info.get("content", "")
            da = annot.info.get("DA", "")
            colors = annot.colors
            opacity = annot.opacity
            
            # Parse font info from DA
            font_name = "helv"
            font_size = 12
            text_color = (0, 0, 0)
            
            match_font = re.search(r'/(\w+)\s+([\d.]+)\s+Tf', da)
            if match_font:
                font_name = match_font.group(1)
                font_size = float(match_font.group(2))
            
            match_rgb = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg', da)
            if match_rgb:
                text_color = (float(match_rgb.group(1)), float(match_rgb.group(2)), float(match_rgb.group(3)))
            
            fill_color = colors.get("fill")
            
            # Delete old annotation
            self.current_fitz_page.delete_annot(annot)
            
            # Create new annotation with same properties
            new_annot = self.current_fitz_page.add_freetext_annot(
                rect,
                content,
                fontsize=font_size,
                fontname=font_name,
                text_color=text_color,
                fill_color=fill_color
            )
            new_annot.set_opacity(opacity)
            new_annot.update()
            
            self.selected_annot = new_annot
            self.pdf_handler.modified = True
            
        except Exception as e:
            print(f"Error reflowing text: {e}")

    # --- Event Handling ---
    def eventFilter(self, obj, event):
        """Filter events for the image label to handle annotations."""
        if obj is self.image_label:
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    if self.annotation_mode == "select":
                        # Selection logic
                        screen_pos = event.pos()
                        offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
                        offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2
                        fitz_point = fitz.Point((screen_pos.x() - offset_x) / self.current_scale, 
                                               (screen_pos.y() - offset_y) / self.current_scale)
                        
                        # Check if clicking on a resize handle first
                        # Skip resize for line-like annotations (they use vertices, not rect)
                        is_line_like = self.selected_annot and self.selected_annot.type[0] in [3, 4, 7, 8]
                        if self.selected_annot and not is_line_like and hasattr(self, 'handle_rects') and self.handle_rects:
                            for i, hr in enumerate(self.handle_rects):
                                if hr.contains(QPointF(screen_pos)):
                                    self.active_resize_handle = i
                                    self.is_resizing = True
                                    self.resize_start_rect = fitz.Rect(self.selected_annot.rect)
                                    self.drag_start_pdf_pos = fitz_point
                                    return True
                        
                        # Prioritize existing selection for dragging
                        already_hit = False
                        if self.selected_annot:
                            try:
                                if fitz_point in self.selected_annot.rect:
                                    already_hit = True
                            except:
                                self.selected_annot = None

                        if not already_hit:
                            # Search for new selection (reverse search to pick topmost)
                            old_selected = self.selected_annot
                            self.selected_annot = None
                            if self.current_fitz_page:
                                try:
                                    annots = list(self.current_fitz_page.annots())
                                    for annot in reversed(annots):
                                        if fitz_point in annot.rect:
                                            self.selected_annot = annot
                                            break
                                except Exception as e:
                                    print(f"Error accessing annotations: {e}")
                            
                            # Emit deselect if we had something and now don't
                            if old_selected and not self.selected_annot:
                                self.annotation_deselected.emit()
                        
                        if self.selected_annot:
                            # Emit properties to update bars
                            self.annotation_selected.emit(
                                self.selected_annot.type[1], 
                                self.get_annot_properties(self.selected_annot)
                            )
                            # Prepare for dragging
                            self.is_dragging_annot = True
                            self.drag_start_pdf_pos = fitz_point
                            self.drag_displacement_pdf = (0, 0)
                            self.original_annot_rect = fitz.Rect(self.selected_annot.rect)
                            if self.selected_annot.type[0] in [3, 4, 7, 8]: # Line, PolyLine, PolyLine(7), Polygon
                                self.original_vertices = list(self.selected_annot.vertices)
                            else:
                                self.original_vertices = None

                            try:
                                annot_type = self.selected_annot.type[1]
                                self.parent_window.status_bar.showMessage(f"Seçildi: {annot_type} (Taşımak için sürükleyin, köşelerden boyutlandırın)")
                            except Exception:
                                self.parent_window.status_bar.showMessage("Nesne seçildi.")
                        
                        self.image_label.update()
                        return True
                    
                    elif self.annotation_mode:
                        self.start_pos = event.pos()
                        self.current_pos = event.pos()
                        self.is_drawing = True
                        return True
                
                elif event.button() == Qt.MouseButton.RightButton:
                    # Context menu for annotations
                    if self.annotation_mode == "select":
                        screen_pos = event.pos()
                        offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
                        offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2
                        fitz_point = fitz.Point((screen_pos.x() - offset_x) / self.current_scale, 
                                               (screen_pos.y() - offset_y) / self.current_scale)
                        
                        # Find annotation at click position
                        clicked_annot = None
                        if self.current_fitz_page:
                            try:
                                annots = list(self.current_fitz_page.annots())
                                for annot in reversed(annots):
                                    if fitz_point in annot.rect:
                                        clicked_annot = annot
                                        break
                            except Exception as e:
                                print(f"Error finding annotation for context menu: {e}")
                        
                        if clicked_annot:
                            self.selected_annot = clicked_annot
                            self.annotation_selected.emit(
                                self.selected_annot.type[1], 
                                self.get_annot_properties(self.selected_annot)
                            )
                            self.show_context_menu(clicked_annot, event.globalPosition().toPoint())
                            self.image_label.update()
                        return True
            
            elif event.type() == event.Type.MouseMove:
                # Handle resize first
                if self.is_resizing and self.selected_annot and self.resize_start_rect:
                    offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
                    offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2
                    current_pdf_point = fitz.Point((event.pos().x() - offset_x) / self.current_scale, 
                                                  (event.pos().y() - offset_y) / self.current_scale)
                    
                    # Calculate new rect based on which handle is being dragged
                    r = self.resize_start_rect
                    new_rect = fitz.Rect(r)
                    h = self.active_resize_handle
                    
                    # Handle indices: 0=TL, 1=T, 2=TR, 3=R, 4=BR, 5=B, 6=BL, 7=L
                    if h == 0: # Top-Left
                        new_rect.x0 = current_pdf_point.x
                        new_rect.y0 = current_pdf_point.y
                    elif h == 1: # Top
                        new_rect.y0 = current_pdf_point.y
                    elif h == 2: # Top-Right
                        new_rect.x1 = current_pdf_point.x
                        new_rect.y0 = current_pdf_point.y
                    elif h == 3: # Right
                        new_rect.x1 = current_pdf_point.x
                    elif h == 4: # Bottom-Right
                        new_rect.x1 = current_pdf_point.x
                        new_rect.y1 = current_pdf_point.y
                    elif h == 5: # Bottom
                        new_rect.y1 = current_pdf_point.y
                    elif h == 6: # Bottom-Left
                        new_rect.x0 = current_pdf_point.x
                        new_rect.y1 = current_pdf_point.y
                    elif h == 7: # Left
                        new_rect.x0 = current_pdf_point.x
                    
                    # Ensure min size (10x10 PDF units)
                    if new_rect.width < 10:
                        if h in [0, 6, 7]:
                            new_rect.x0 = new_rect.x1 - 10
                        else:
                            new_rect.x1 = new_rect.x0 + 10
                    if new_rect.height < 10:
                        if h in [0, 1, 2]:
                            new_rect.y0 = new_rect.y1 - 10
                        else:
                            new_rect.y1 = new_rect.y0 + 10
                    
                    try:
                        # Skip set_rect for line-like annotations
                        is_line_like = self.selected_annot.type[0] in [3, 4, 7, 8]
                        if not is_line_like:
                            self.selected_annot.set_rect(new_rect)
                            self.selected_annot.update()
                            self.pdf_handler.modified = True
                    except Exception as e:
                        print(f"Resize error: {e}")
                    
                    self.update_display()
                    return True
                
                if self.is_dragging_annot and self.selected_annot:
                    offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
                    offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2
                    current_pdf_point = fitz.Point((event.pos().x() - offset_x) / self.current_scale, 
                                                  (event.pos().y() - offset_y) / self.current_scale)
                    
                    # Calculate displacement in PDF units
                    dx = current_pdf_point.x - self.drag_start_pdf_pos.x
                    dy = current_pdf_point.y - self.drag_start_pdf_pos.y
                    self.drag_displacement_pdf = (dx, dy)
                    
                    try:
                        # Safety check for dead object
                        _ = self.selected_annot.rect

                        # Calculate displacement in PDF units from original position
                        new_rect = fitz.Rect(self.original_annot_rect.x0 + dx, self.original_annot_rect.y0 + dy,
                                            self.original_annot_rect.x1 + dx, self.original_annot_rect.y1 + dy)
                        
                        # Handle line-like annotations separately - they don't support set_rect
                        is_line_like = self.selected_annot.type[0] in [3, 4, 7, 8] # Line, PolyLine, Polygon
                        
                        # Don't call set_rect during drag - just update visual
                        # The actual move happens on MouseRelease
                    except:
                        # If object died, clear selection
                        pass
                    
                    # Only update visual feedback (selection frame shows displacement)
                    self.image_label.update()
                    return True

                elif self.is_drawing:
                    self.current_pos = event.pos()
                    self.image_label.update()
                else:
                    self.show_annotation_tooltip(event.pos())
                return True
            
            elif event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
                # Handle resize release
                if self.is_resizing:
                    self.is_resizing = False
                    self.active_resize_handle = -1
                    
                    # For FreeText, trigger text reflow by re-creating the annotation
                    if self.selected_annot and self.selected_annot.type[0] == 2:  # FreeText
                        try:
                            self.reflow_freetext_annotation(self.selected_annot)
                        except Exception as e:
                            print(f"Error during text reflow: {e}")
                    
                    self.resize_start_rect = None
                    self.update_display()
                    return True
                
                if self.is_dragging_annot:
                    self.is_dragging_annot = False
                    dx, dy = self.drag_displacement_pdf
                    if abs(dx) > 0.1 or abs(dy) > 0.1:
                        # Perform final move for line-like if needed
                        if self.selected_annot.type[0] in [3, 4, 7]: # Line, PolyLine
                            try:
                                # Re-create the line at the new position
                                if self.original_vertices:
                                    new_vertices = []
                                    for v in self.original_vertices:
                                        vx = v.x if hasattr(v, "x") else v[0]
                                        vy = v.y if hasattr(v, "y") else v[1]
                                        new_vertices.append((vx + dx, vy + dy))
                                    
                                    # Copy properties
                                    colors = self.selected_annot.colors
                                    width = self.selected_annot.border.get("width", 1)
                                    info = self.selected_annot.info
                                    opacity = self.selected_annot.opacity
                                    
                                    # Remove old
                                    self.current_fitz_page.delete_annot(self.selected_annot)
                                    
                                    # Add new (as polyline)
                                    new_annot = self.current_fitz_page.add_polyline_annot(new_vertices)
                                    new_annot.set_colors(stroke=colors.get("stroke"), fill=colors.get("fill"))
                                    new_annot.set_border(width=width)
                                    new_annot.set_info(info)
                                    new_annot.set_opacity(opacity)
                                    
                                    # Update
                                    new_annot.update()
                                    self.selected_annot = new_annot
                            except Exception as e:
                                print(f"Error moving line: {e}")
                        else:
                            # For non-line annotations (Circle, Square, FreeText, etc.)
                            # Apply the final move now
                            try:
                                new_rect = fitz.Rect(
                                    self.original_annot_rect.x0 + dx, 
                                    self.original_annot_rect.y0 + dy,
                                    self.original_annot_rect.x1 + dx, 
                                    self.original_annot_rect.y1 + dy
                                )
                                self.selected_annot.set_rect(new_rect)
                                self.selected_annot.update()
                            except Exception as e:
                                print(f"Error moving annotation: {e}")
                        
                        self.pdf_handler.modified = True
                    
                    self.drag_start_pdf_pos = None
                    self.drag_displacement_pdf = (0, 0)
                    self.original_annot_rect = None
                    self.original_vertices = None
                    self.update_display()
                    return True
                
                if self.is_drawing:
                    self.is_drawing = False
                    self.finish_annotation(event.pos())
                    self.image_label.update()
                    return True

            elif event.type() == event.Type.Paint:
                # We handle the entire painting of image_label to control Z-order
                painter = QPainter(obj)
                
                # 1. Draw the actual page content (pixmap)
                pix = obj.pixmap()
                if pix:
                    # Calculate centering offset to match QLabel's alignment and hit-testing logic
                    offset_x = (obj.width() - pix.width()) / 2
                    offset_y = (obj.height() - pix.height()) / 2
                    painter.drawPixmap(int(offset_x), int(offset_y), pix)
                
                # 2. Draw overlays on top
                if self.is_drawing:
                    self.draw_rubber_band(painter)
                
                if self.selected_annot and self.annotation_mode == "select":
                    self.draw_selection_frame(painter)
                
                painter.end()
                return True # Tell Qt we've handled the painting

        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete and self.selected_annot:
                # Remove the selected annotation
                self.pdf_handler.doc[self.current_page_index].delete_annot(self.selected_annot)
                self.pdf_handler.modified = True
                self.selected_annot = None
                self.update_display()
                self.parent_window.status_bar.showMessage("Nesne silindi.")
                return True

        return super().eventFilter(obj, event)

    def show_annotation_tooltip(self, pos):
        """Show a tooltip if the mouse is over an annotation."""
        if not self.pdf_handler or self.current_page_index < 0:
            return
            
        # Convert screen coordinates to PDF units
        offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
        offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2
        
        pdf_point = QPoint(int((pos.x() - offset_x) / self.current_scale), 
                          int((pos.y() - offset_y) / self.current_scale))
                          
        content = self.pdf_handler.get_annotation_content_at_point(self.current_page_index, pdf_point)
        
        from PyQt6.QtWidgets import QToolTip
        if content:
            QToolTip.showText(self.image_label.mapToGlobal(pos), content, self.image_label)
        else:
            QToolTip.hideText()

    def draw_selection_frame(self, painter=None):
        """Draws a bounding box and handles around the selected annotation."""
        try:
            if not self.selected_annot or not self.current_pixmap:
                return
            
            # Access rect to check if object is still alive
            r = self.selected_annot.rect
        except (ReferenceError, Exception):
            self.selected_annot = None
            return

        if painter is None:
            painter = QPainter(self.image_label)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            should_end_painter = True
        else:
            should_end_painter = False
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate screen coordinates for the annotation rect
        offset_x = (self.image_label.width() - (self.current_pixmap.width() if self.current_pixmap else 0)) / 2
        offset_y = (self.image_label.height() - (self.current_pixmap.height() if self.current_pixmap else 0)) / 2
        
        r = self.selected_annot.rect
        dx, dy = self.drag_displacement_pdf
        
        rect = QRectF((r.x0 + dx) * self.current_scale + offset_x, 
                      (r.y0 + dy) * self.current_scale + offset_y,
                      (r.x1 - r.x0) * self.current_scale, 
                      (r.y1 - r.y0) * self.current_scale)

        # Draw main bounding box
        pen = QPen(self.selection_color, 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

        # Calculate 8 handle positions: TL, T, TR, R, BR, B, BL, L
        hs = self.handle_size
        cx, cy = rect.center().x(), rect.center().y()
        
        handle_positions = [
            QPointF(rect.left(), rect.top()),           # 0: Top-Left
            QPointF(cx, rect.top()),                    # 1: Top
            QPointF(rect.right(), rect.top()),          # 2: Top-Right
            QPointF(rect.right(), cy),                  # 3: Right
            QPointF(rect.right(), rect.bottom()),       # 4: Bottom-Right
            QPointF(cx, rect.bottom()),                 # 5: Bottom
            QPointF(rect.left(), rect.bottom()),        # 6: Bottom-Left
            QPointF(rect.left(), cy),                   # 7: Left
        ]
        
        # Store handle rects for hit testing (screen coordinates)
        self.handle_rects = []
        painter.setBrush(self.selection_color)
        for p in handle_positions:
            handle_rect = QRectF(p.x() - hs/2, p.y() - hs/2, hs, hs)
            self.handle_rects.append(handle_rect)
            painter.drawRect(handle_rect)
        
        if should_end_painter:
            painter.end()

    def draw_rubber_band(self, painter=None):
        """Draws a preview of the annotation while dragging."""
        if not self.is_drawing or not self.start_pos or not self.current_pos:
            return

        if painter is None:
            painter = QPainter(self.image_label)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            should_end_painter = True
        else:
            should_end_painter = False
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = self.current_properties.get("stroke_color", QColor(255, 0, 0))
        pen = QPen(color, 2, Qt.PenStyle.DashLine)
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

        if should_end_painter:
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
                # Default size for point-like annotations, centered around s_pos
                rect = QRectF(s_pos.x() - 25, s_pos.y() - 25, 50, 50)
            else:
                # For line or highlight, ignore very small movements
                return

        p = self.current_properties
        stroke = (p["stroke_color"].red()/255, p["stroke_color"].green()/255, p["stroke_color"].blue()/255)
        fill = None
        if p["fill_color"].alpha() > 0:
            fill = (p["fill_color"].red()/255, p["fill_color"].green()/255, p["fill_color"].blue()/255)

        if self.annotation_mode == "note":
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "Not Ekle", "Not içeriğini giriniz:")
            if ok and text:
                self.pdf_handler.add_note(self.current_page_index, s_pos, text, color=stroke)
        elif self.annotation_mode == "text":
            from PyQt6.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "Metin Ekle", "Metin giriniz:")
            if ok and text:
                self.pdf_handler.add_textbox(self.current_page_index, rect, text, 
                                           fontsize=p["font_size"], color=stroke, fontname=p["font_family"])
        elif self.annotation_mode == "line":
            if is_small: return
            self.pdf_handler.add_line(self.current_page_index, s_pos, e_pos, 
                                    color=stroke, width=p["thickness"], arrow_type=p["arrow_type"])
        elif self.annotation_mode == "circle":
            self.pdf_handler.add_circle(self.current_page_index, rect, 
                                      color=stroke, fill_color=fill, width=p["thickness"])
        elif self.annotation_mode == "highlight":
            if is_small: return
            self.pdf_handler.add_highlight(self.current_page_index, rect, color=stroke)
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
