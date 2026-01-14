import sys
import os # Import os
import qt_material # Import qt_material to get its path

from PyQt6.QtGui import QAction, QIcon, QPainter
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel, QMenu, QMenuBar, QFileDialog, QComboBox, QPushButton, \
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from core.pdf_handler import PDFHandler 
from gui.pdf_viewer import PDFViewer
from gui.thumbnail_view import ThumbnailView 
from gui.toolbar_manager import ToolbarManager
from gui.svg_utils import get_icon_for_theme
from qt_material import apply_stylesheet, set_icons_theme, get_theme

class MainWindow(QMainWindow):
    """Main application window for MantiPDF Editor."""

    def __init__(self, app, parent=None):
        """Initialize the main window."""
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("MantiPDF Editor")
        self.setGeometry(100, 100, 1200, 800) # x, y, width, height

        self.settings = QSettings("MantiPDF", "Editor")
        self.current_theme = self.settings.value("theme", "dark_teal")
        # self.apply_theme(self.current_theme) # MOVED: Apply theme after UI is built
        
        # Uygulama başlangıcında tema bazlı SVG ikonlarını hazırla
        self._prepare_themed_icons()

        # Initialize PDF Handler
        self.pdf_handler = PDFHandler()
        self.current_page_index = 0

        # Initialize PDF viewer
        self.pdf_viewer = PDFViewer(self)
        self.setCentralWidget(self.pdf_viewer)

        # Initialize Thumbnail view
        self.thumbnail_view = ThumbnailView(self)
        self.thumbnail_view.itemSelectionChanged.connect(self.on_thumbnail_selected)
        self.thumbnail_view.page_moved.connect(self.on_page_moved)

        # Create Dock Widget for Thumbnails and reorder buttons
        self.thumbnail_dock = QDockWidget("Pages", self)
        thumbnail_container = QWidget()
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        thumbnail_layout.setSpacing(5)

        thumbnail_layout.addWidget(self.thumbnail_view)

        # Create reorder buttons
        reorder_toolbar = QHBoxLayout()
        icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
        
        # Use themed icons
        self.move_to_top_btn = QPushButton("")
        self.move_up_btn = QPushButton("")
        self.move_down_btn = QPushButton("")
        self.move_to_bottom_btn = QPushButton("")
        
        # Initial icons
        self.move_to_top_btn.setIcon(QIcon(get_icon_for_theme("move-top.svg", self.current_theme, icons_dir)))
        self.move_up_btn.setIcon(QIcon(get_icon_for_theme("move-up.svg", self.current_theme, icons_dir)))
        self.move_down_btn.setIcon(QIcon(get_icon_for_theme("move-down.svg", self.current_theme, icons_dir)))
        self.move_to_bottom_btn.setIcon(QIcon(get_icon_for_theme("move-bottom.svg", self.current_theme, icons_dir)))

        self.move_to_top_btn.setToolTip("Move Page to Top")
        self.move_up_btn.setToolTip("Move Page Up")
        self.move_down_btn.setToolTip("Move Page Down")
        self.move_to_bottom_btn.setToolTip("Move Page to Bottom")

        reorder_toolbar.addWidget(self.move_to_top_btn)
        reorder_toolbar.addWidget(self.move_up_btn)
        reorder_toolbar.addWidget(self.move_down_btn)
        reorder_toolbar.addWidget(self.move_to_bottom_btn)

        thumbnail_layout.addLayout(reorder_toolbar)

        self.thumbnail_dock.setWidget(thumbnail_container)
        self.thumbnail_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.thumbnail_dock)

        # Connect reorder button signals
        self.move_to_top_btn.clicked.connect(lambda: self.move_selected_page("top"))
        self.move_up_btn.clicked.connect(lambda: self.move_selected_page("up"))
        self.move_down_btn.clicked.connect(lambda: self.move_selected_page("down"))
        self.move_to_bottom_btn.clicked.connect(lambda: self.move_selected_page("bottom"))

        # Initialize toolbar manager
        self.toolbar_manager = ToolbarManager(self)
        
        # Register thumbnail move buttons to toolbar manager for theme updates
        self.toolbar_manager.button_icons[self.move_to_top_btn] = "move-top"
        self.toolbar_manager.button_icons[self.move_up_btn] = "move-up"
        self.toolbar_manager.button_icons[self.move_down_btn] = "move-down"
        self.toolbar_manager.button_icons[self.move_to_bottom_btn] = "move-bottom"

        self.create_menu_bar()
        self.create_toolbars()

        self.create_status_bar()

        # Restore window geometry and state (including toolbars and docks)
        self.restoreGeometry(self.settings.value("geometry", b'')) # Provide default empty QByteArray
        self.restoreState(self.settings.value("windowState", b'')) # Provide default empty QByteArray

        # Restore zoom level
        saved_scale = self.settings.value("zoomScale", 1.0) # Default to 100%
        try:
            scale_factor = float(saved_scale)
            # Ensure the page is loaded *before* setting scale if possible,
            # but we might not have a page yet. set_scale handles this.
            self.pdf_viewer.set_scale(scale_factor)
        except (ValueError, TypeError): # Catch TypeError if value isn't convertible
            print(f"Warning: Could not restore zoom scale from settings ('{saved_scale}'). Using default.")
            self.pdf_viewer.set_scale(1.0)


        # Initial theme is now applied in main.py BEFORE window creation
        # self.apply_theme(self.current_theme) # REMOVED

        # Connect overscroll signals for page navigation
        self.pdf_viewer.overscrollNext.connect(self.next_page)
        self.pdf_viewer.overscrollPrevious.connect(self.previous_page)

    def create_menu_bar(self):
        """Create the application's menu bar."""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar) # Set menu bar early

        # --- File Menu ---
        file_menu = menu_bar.addMenu("File")
        self.add_menu_action(file_menu, "Open PDF", self.open_pdf, "Ctrl+O", "open")
        self.add_menu_action(file_menu, "Save PDF", self.save_pdf, "Ctrl+S")
        self.add_menu_action(file_menu, "Save As...", self.save_pdf_as, "Ctrl+Shift+S")
        self.add_menu_action(file_menu, "Print", self.print_pdf, "Ctrl+P", "print")

        # --- Edit Menu ---
        edit_menu = menu_bar.addMenu("Edit")
        # Add edit actions here later

        # --- View Menu ---
        view_menu = menu_bar.addMenu("View")
        toggle_thumbs_action = self.thumbnail_dock.toggleViewAction()
        toggle_thumbs_action.setText("Toggle Page Thumbnails")
        toggle_thumbs_action.setShortcut("Ctrl+T")
        view_menu.addAction(toggle_thumbs_action)
        # Add zoom actions etc. to View Menu if desired

        # --- Page Menu ---
        page_menu = menu_bar.addMenu("Page")
        self.add_menu_action(page_menu, "First Page", self.first_page, "Home") # First page shortcut
        self.add_menu_action(page_menu, "Previous Page", self.previous_page, "PgUp") # Common shortcut
        self.add_menu_action(page_menu, "Next Page", self.next_page, "PgDown") # Common shortcut
        self.add_menu_action(page_menu, "Last Page", self.last_page, "End") # Last page shortcut
        page_menu.addSeparator()
        self.add_menu_action(page_menu, "Rotate Left", self.rotate_left, "Ctrl+Shift+L")
        self.add_menu_action(page_menu, "Rotate Right", self.rotate_right, "Ctrl+Shift+R")
        self.add_menu_action(page_menu, "Rotate 180", self.rotate_180)
        page_menu.addSeparator()
        self.add_menu_action(page_menu, "Add Blank Page", self.add_page, "Ctrl+Shift+N")
        self.add_menu_action(page_menu, "Delete Current Page", self.delete_page, "Ctrl+Shift+D")

        # --- Tools Menu ---
        tools_menu = menu_bar.addMenu("Tools")
        self.add_menu_action(tools_menu, "Merge PDF...", self.merge_pdf)
        self.add_menu_action(tools_menu, "Split PDF...", self.split_pdf)
        self.add_menu_action(tools_menu, "Klasörden PDF Birleştir...", self.merge_pdfs_in_folder)


    def add_menu_action(self, menu, text, slot, shortcut=None, icon_name=None):
        """Helper to add an action to a menu."""
        action = QAction(text, self)
        if icon_name:
            action.setIcon(QIcon.fromTheme(icon_name)) # Requires theme setup or resource file
        action.triggered.connect(slot)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def create_toolbars(self):
        # File toolbar
        file_toolbar = self.toolbar_manager.create_toolbar("File")
        self.toolbar_manager.add_button(file_toolbar, "Open", "open", self.open_pdf).setShortcut("Ctrl+O")
        self.toolbar_manager.add_button(file_toolbar, "Save", "file-save", self.save_pdf).setShortcut("Ctrl+S")
        self.toolbar_manager.add_button(file_toolbar, "Save As", "file-save-as", self.save_pdf_as).setShortcut("Ctrl+Shift+S")
        self.toolbar_manager.add_button(file_toolbar, "Print", "print", self.print_pdf).setShortcut("Ctrl+P")

        # Print toolbar
        # print_toolbar = self.toolbar_manager.create_toolbar("Print")
        # self.toolbar_manager.add_button(print_toolbar, "Print", "print", self.print_pdf).setShortcut("Ctrl+P")

        # Page toolbar
        page_toolbar = self.toolbar_manager.create_toolbar("Page")
        self.toolbar_manager.add_button(page_toolbar, "Add Page", "page-add", self.add_page).setShortcut("Ctrl+Shift+N")
        self.toolbar_manager.add_button(page_toolbar, "Delete Page", "page-delete", self.delete_page).setShortcut("Ctrl+Shift+D")
        self.toolbar_manager.add_button(page_toolbar, "Rotate Left", "page-rotate-left", self.rotate_left).setShortcut("Ctrl+Shift+L")
        self.toolbar_manager.add_button(page_toolbar, "Rotate Right", "page-rotate-right", self.rotate_right).setShortcut("Ctrl+Shift+R")
        self.toolbar_manager.add_button(page_toolbar, "Rotate 180", "page-rotate-180", self.rotate_180)

        # View toolbar
        view_toolbar = self.toolbar_manager.create_toolbar("View")
        zoom_in_button = self.toolbar_manager.add_button(view_toolbar, "Zoom In", "zoom-in", self.zoom_in)
        zoom_in_button.setShortcut("Ctrl++")
        zoom_out_button = self.toolbar_manager.add_button(view_toolbar, "Zoom Out", "zoom-out", self.zoom_out)
        zoom_out_button.setShortcut("Ctrl+-")
        self.toolbar_manager.add_button(view_toolbar, "Zoom Fit", "zoom-fit", self.zoom_fit)
        self.toolbar_manager.add_button(view_toolbar, "Zoom Width", "zoom-width", self.zoom_width)
        
        # Navigation toolbar - Sayfa gezinme kontrolleri için ayrı bir toolbar
        navigation_toolbar = self.toolbar_manager.create_toolbar("Navigation")
        first_page_button = self.toolbar_manager.add_button(navigation_toolbar, "First Page", "go-first-page", self.first_page)
        first_page_button.setShortcut("Home")
        previous_page_button = self.toolbar_manager.add_button(navigation_toolbar, "Previous Page", "go-previous", self.previous_page)
        previous_page_button.setShortcut("PgUp")

        # Add page number display/input
        self.page_label = QLabel("Page: 0 / 0")
        self.toolbar_manager.add_widget(navigation_toolbar, self.page_label)
        # Consider adding a QSpinBox or QLineEdit for direct page input later


        next_page_button = self.toolbar_manager.add_button(navigation_toolbar, "Next Page", "go-next", self.next_page)
        next_page_button.setShortcut("PgDown")
        last_page_button = self.toolbar_manager.add_button(navigation_toolbar, "Last Page", "go-last-page", self.last_page)
        last_page_button.setShortcut("End")


        # Theme selection
        theme_combo = QComboBox()
        themes = [
            "dark_amber", "dark_blue", "dark_cyan", "dark_lightgreen", "dark_medical",
            "dark_pink", "dark_purple", "dark_red", "dark_teal", "dark_yellow",
            "light_amber", "light_blue_500", "light_blue", "light_cyan_500", "light_cyan",
            "light_lightgreen_500", "light_lightgreen", "light_orange", "light_pink_500",
            "light_pink", "light_purple_500", "light_purple", "light_red_500", "light_red",
            "light_teal_500", "light_teal", "light_yellow"
        ]
        theme_combo.addItems(themes)
        theme_combo.setCurrentText(self.current_theme)
        theme_combo.currentTextChanged.connect(self.apply_theme)
        print(f"DEBUG: Connected theme_combo.currentTextChanged to {self.apply_theme}") # Add debug print
        print(f"DEBUG: Is self.apply_theme callable? {callable(self.apply_theme)}") # Check if callable
        self.toolbar_manager.add_widget(view_toolbar, theme_combo)

        # Edit toolbar
        edit_toolbar = self.toolbar_manager.create_toolbar("Edit")
        self.toolbar_manager.add_button(edit_toolbar, "Add Note", "edit-add-note", self.add_note)
        self.toolbar_manager.add_button(edit_toolbar, "Add Text", "edit-add-text", self.add_text)
        self.toolbar_manager.add_button(edit_toolbar, "Add Line", "edit-add-line", self.add_line)
        self.toolbar_manager.add_button(edit_toolbar, "Highlight", "edit-highlight", self.highlight)
        self.toolbar_manager.add_button(edit_toolbar, "Add Circle", "edit-add-circle", self.add_circle)
        self.toolbar_manager.add_button(edit_toolbar, "Add Stamp", "edit-add-stamp", self.add_stamp)

    def open_pdf(self):
        """Opens a PDF file using a file dialog."""
        filepath, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if filepath:
            # Close existing document first (handled within pdf_handler.open_document)
            # self.pdf_handler.close_document() # No longer needed here
            if self.pdf_handler.open_document(filepath):
                self.current_page_index = 0
                self.display_page(self.current_page_index)
                self.update_thumbnails() # Update thumbnails after opening
                self.update_status_bar()
                self.setWindowTitle(f"MantiPDF Editor - {self.pdf_handler.filepath}")
            else:
                print("Error opening PDF.") # TODO: Show error dialog
                self.setWindowTitle("MantiPDF Editor")
                self.pdf_viewer.clear_display()
                self.thumbnail_view.clear_thumbnails()
                self.update_status_bar()

    def save_pdf(self):
        """Save the PDF document along with notes."""
        # First, save notes from the PDF viewer
        if hasattr(self, 'pdf_viewer'):
            self.pdf_viewer.save_notes()
        # Then, proceed with PDF saving using the existing pdf_handler
        result = self.pdf_handler.save_pdf()
        return result

    def save_pdf_as(self):
        """Saves the PDF file with a new name."""
        if not self.pdf_handler.doc:
            print("No document open to save.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Save PDF As...", self.pdf_handler.filepath or ".", "PDF Files (*.pdf)")
        if filepath:
            if self.pdf_handler.save_document(filepath):
                self.update_status_bar()
                self.setWindowTitle(f"MantiPDF Editor - {self.pdf_handler.filepath}")
                print(f"Document saved as {filepath}.") # TODO: Status bar message
            else:
                print(f"Failed to save document to {filepath}.") # TODO: Error dialog

    def display_page(self, page_index):
        """Displays the page at the given index."""
        if self.pdf_handler.doc and 0 <= page_index < self.pdf_handler.page_count:
            # Pass the handler and index to the viewer
            self.pdf_viewer.display_page(self.pdf_handler, page_index)
            self.current_page_index = page_index
            self.update_status_bar()
            # Update thumbnail selection without triggering signal loop
            self.thumbnail_view.blockSignals(True)
            items = self.thumbnail_view.findItems(f"Page {page_index + 1}", Qt.MatchFlag.MatchExactly)
            if items:
                self.thumbnail_view.setCurrentItem(items[0])
            self.thumbnail_view.blockSignals(False)
        else:
            # Clear display if page index is invalid (e.g., after deleting last page)
            self.pdf_viewer.clear_display()
            self.current_page_index = -1 # Indicate no page is selected
            self.update_status_bar()


    def update_status_bar(self):
        """Updates the status bar with the current page number and modified status."""
        if self.pdf_handler.doc:
            page_num_text = f"Page {self.current_page_index + 1} of {self.pdf_handler.page_count}"
            modified_text = " *" if self.pdf_handler.modified else ""
            self.status_bar.showMessage(f"{page_num_text}{modified_text} | {self.pdf_handler.filepath or 'Untitled'}")
            self.page_label.setText(page_num_text) # Update toolbar label too
        else:
            self.status_bar.showMessage("No PDF loaded")
            self.page_label.setText("Page: 0 / 0")

    def update_thumbnails(self):
        """Updates the thumbnail view with pages from the current document."""
        self.thumbnail_view.update_thumbnails(self.pdf_handler)
        # Optionally select the current page's thumbnail
        if self.pdf_handler.doc and 0 <= self.current_page_index < self.pdf_handler.page_count:
             items = self.thumbnail_view.findItems(f"Page {self.current_page_index + 1}", Qt.MatchFlag.MatchExactly)
             if items:
                 self.thumbnail_view.setCurrentItem(items[0])

    def on_thumbnail_selected(self):
        """Slot connected to thumbnail selection changes."""
        selected_items = self.thumbnail_view.selectedItems()
        if selected_items:
            page_num = selected_items[0].data(Qt.ItemDataRole.UserRole) # Retrieve stored page number
            if page_num is not None and page_num != self.current_page_index:
                self.display_page(page_num)

    def on_page_moved(self, from_index, to_index):
        """Handles the reordering of pages from the thumbnail view."""
        if self.pdf_handler.move_page(from_index, to_index):
            # The moved page is now at to_index. Let's make it the current page.
            self.current_page_index = to_index
            
            # Refresh UI to reflect the new order
            self.update_thumbnails()
            self.display_page(self.current_page_index)

    def move_selected_page(self, direction):
        """Moves the currently selected page using the reorder buttons."""
        selected_items = self.thumbnail_view.selectedItems()
        if not selected_items or not self.pdf_handler.doc:
            return

        from_index = self.thumbnail_view.row(selected_items[0])
        page_count = self.pdf_handler.page_count

        if direction == "top":
            to_index = 0
        elif direction == "up":
            to_index = from_index - 1
        elif direction == "down":
            to_index = from_index + 1
        elif direction == "bottom":
            to_index = page_count - 1
        else:
            return

        if 0 <= to_index < page_count and from_index != to_index:
            self.on_page_moved(from_index, to_index)

    # def save_pdf_as(self):
    #     """Saves the PDF file with a new name."""
    #     print("Save PDF As") # Replaced above

    def previous_page(self):
        """Displays the previous page."""
        if self.pdf_handler.doc and self.current_page_index > 0:
            self.display_page(self.current_page_index - 1)

    def next_page(self):
        """Displays the next page."""
        if self.pdf_handler.doc and self.current_page_index < self.pdf_handler.page_count - 1:
            self.display_page(self.current_page_index + 1)
            
    def first_page(self):
        """Displays the first page of the document."""
        if self.pdf_handler.doc and self.pdf_handler.page_count > 0:
            self.display_page(0)
            
    def last_page(self):
        """Displays the last page of the document."""
        if self.pdf_handler.doc and self.pdf_handler.page_count > 0:
            self.display_page(self.pdf_handler.page_count - 1)

    def print_pdf(self):
        """Prints the PDF file using QPrinter and QPrintDialog."""
        if not self.pdf_handler.doc:
            print("No document open to print.")
            return
            
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Document")
        
        # Set default print range to all pages
        dialog.setOption(QPrintDialog.PrintDialogOption.PrintToFile, True)
        dialog.setOption(QPrintDialog.PrintDialogOption.PrintSelection, False)
        
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # User clicked print
            try:
                # Get selected page range
                print_range = dialog.printRange()
                from_page = dialog.fromPage()
                to_page = dialog.toPage()
                
                # Adjust for 0-based indexing in PDF handler vs 1-based in dialog
                if from_page > 0:
                    from_page -= 1
                if to_page > 0:
                    to_page -= 1
                else:
                    to_page = self.pdf_handler.page_count - 1
                
                # If no specific range is selected, print all pages
                if print_range == QPrintDialog.PrintRange.AllPages:
                    from_page = 0
                    to_page = self.pdf_handler.page_count - 1
                
                # Print the document
                self._print_document(printer, from_page, to_page)
                print(f"Document printed successfully. Pages {from_page+1} to {to_page+1}")
            except Exception as e:
                print(f"Error printing document: {e}")
        else:
            print("Printing canceled by user.")
    
    def _print_document(self, printer, from_page, to_page):
        """Handles the actual printing of the document."""
        painter = QPainter()
        if painter.begin(printer):
            try:
                for i in range(from_page, to_page + 1):
                    if i > from_page:
                        printer.newPage()
                    
                    # Get the page as a pixmap
                    pixmap = self.pdf_handler.get_page_pixmap(i, scale=2.0)  # Higher resolution for printing
                    if pixmap:
                        # Calculate scaling to fit the page to the printer
                        printer_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
                        pixmap_size = pixmap.size()
                        
                        # Scale pixmap to fit printer page while maintaining aspect ratio
                        scale_factor = min(printer_rect.width() / pixmap_size.width(),
                                          printer_rect.height() / pixmap_size.height())
                        
                        target_width = int(pixmap_size.width() * scale_factor)
                        target_height = int(pixmap_size.height() * scale_factor)
                        
                        # Center the pixmap on the page
                        x = (printer_rect.width() - target_width) // 2
                        y = (printer_rect.height() - target_height) // 2
                        
                        # Draw the pixmap on the printer
                        painter.drawPixmap(x, y, target_width, target_height, pixmap)
            finally:
                painter.end()

    def add_page(self):
        """Adds a new blank page after the current page."""
        if self.pdf_handler.add_blank_page(index=self.current_page_index + 1):
            self.update_thumbnails() # Update thumbnails
            self.display_page(self.current_page_index + 1) # Display the new page
            self.update_status_bar()
        else:
            print("Failed to add blank page.") # TODO: Error message

    def delete_page(self):
        """Deletes the current page from the PDF file."""
        if not self.pdf_handler.doc or self.current_page_index < 0:
             print("No page selected to delete.")
             return

        page_to_delete = self.current_page_index
        page_count_before = self.pdf_handler.page_count

        if self.pdf_handler.delete_page(page_to_delete):
            self.update_thumbnails() # Update thumbnails
            self.update_status_bar() # Update page count

            # Decide which page to display next
            new_page_index = -1
            if self.pdf_handler.page_count > 0:
                new_page_index = min(page_to_delete, self.pdf_handler.page_count - 1)

            self.display_page(new_page_index) # Display adjacent page or clear if empty

        else:
            print(f"Failed to delete page {page_to_delete}.") # TODO: Error message

    def rotate_left(self):
        """Rotates the current page 90 degrees counter-clockwise (saat yönünün tersine)."""
        self.rotate_page(270) # 270 derece = saat yönünün tersine 90 derece

    def rotate_right(self):
        """Rotates the current page 90 degrees clockwise (saat yönünde)."""
        self.rotate_page(90) # 90 derece = saat yönünde 90 derece

    def rotate_180(self):
        """Rotates the current page 180 degrees."""
        self.rotate_page(180) # 180 derece = sayfayı baş aşağı çevirme

    def rotate_page(self, angle):
        """Rotates the current page by the specified angle and updates views."""
        if self.pdf_handler.doc and 0 <= self.current_page_index < self.pdf_handler.page_count:
            if self.pdf_handler.rotate_page(self.current_page_index, angle):
                self.display_page(self.current_page_index) # Refresh the main view
                self.update_thumbnails() # Update all thumbnails (rotation affects them)
                self.update_status_bar()
                self.pdf_viewer.update() # Explicitly update the PDF viewer
            else:
                print(f"Failed to rotate page {self.current_page_index} by {angle} degrees.") # TODO: Error msg
        else:
             print("No page selected or loaded to rotate.")

    def merge_pdf(self):
        """Merges another PDF into the current one."""
        if not self.pdf_handler.doc:
             print("Open a base PDF document first before merging.") # TODO: Message box
             return

        filepath, _ = QFileDialog.getOpenFileName(self, "Select PDF to Merge", "", "PDF Files (*.pdf)")
        if filepath:
            if self.pdf_handler.merge_pdf(filepath):
                 self.update_thumbnails()
                 self.update_status_bar()
                 print(f"Successfully merged {filepath}") # TODO: Status bar
            else:
                 print(f"Failed to merge {filepath}") # TODO: Error dialog
                 
    def merge_pdfs_in_folder(self):
        """Seçilen klasördeki PDF dosyalarını kullanıcı sırasına göre birleştirir."""
        from PyQt6.QtWidgets import QMessageBox
        try:
            # Dialog'u içe aktar ve göster
            from gui.merge_folder_dialog import MergeFolderDialog
            dialog = MergeFolderDialog(self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                pdf_paths = dialog.get_ordered_file_paths()
                if not pdf_paths:
                    QMessageBox.information(self, "Birleştirme", "Birleştirilecek PDF bulunamadı.")
                    return
                # Eğer açık belge yoksa ilk PDF'i aç, kalanları ekle
                start_index = 0
                if not self.pdf_handler.doc:
                    if self.pdf_handler.open_document(pdf_paths[0]):
                        self.current_page_index = 0
                        self.display_page(self.current_page_index)
                        start_index = 1
                    else:
                        QMessageBox.warning(self, "Birleştirme", f"Açılamadı: {pdf_paths[0]}")
                        return
                merged_count = 0
                for path in pdf_paths[start_index:]:
                    if self.pdf_handler.merge_pdf(path):
                        merged_count += 1
                    else:
                        print(f"Merge failed: {path}")
                # UI güncelle
                self.update_thumbnails()
                self.update_status_bar()
                QMessageBox.information(self, "Birleştirme Tamamlandı", 
                                          f"{len(pdf_paths)} dosyadan {merged_count + (1 if start_index==1 else 0)} dosya birleştirildi.")
        except Exception as e:
            print(f"merge_pdfs_in_folder error: {e}")

    def split_pdf(self):
        """Splits the current PDF into separate files based on user selection."""
        if not self.pdf_handler.doc:
            print("PDF bölmek için önce bir PDF dosyası açın.") # TODO: Message box
            return
            
        # Import the split dialog
        from gui.split_dialog import SplitDialog
        
        # Create and show the split dialog
        dialog = SplitDialog(self, self.pdf_handler.page_count)
        if dialog.exec() == SplitDialog.DialogCode.Accepted:
            # Get the output directory and page ranges from the dialog
            output_dir = dialog.output_dir
            page_ranges = dialog.get_page_ranges()
            
            # Split the PDF
            created_files = self.pdf_handler.split_pdf(output_dir, page_ranges)
            
            if created_files:
                # Show success message with the number of created files
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "PDF Bölme Başarılı", 
                                      f"{len(created_files)} PDF dosyası oluşturuldu.\n\nKonum: {output_dir}")
                
                # Update status bar
                self.status_bar.showMessage(f"{len(created_files)} PDF dosyası oluşturuldu.")
            else:
                # Show error message
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "PDF Bölme Başarısız", 
                                  "PDF dosyası bölünürken bir hata oluştu.")
                
                # Update status bar
                self.status_bar.showMessage("PDF bölme işlemi başarısız oldu.")

    # --- Zoom methods --- (Forward to PDFViewer)
    def zoom_in(self):
        self.pdf_viewer.zoom_in()

    def zoom_out(self):
        self.pdf_viewer.zoom_out()

    def zoom_fit(self):
        self.pdf_viewer.zoom_fit()

    def zoom_width(self):
        self.pdf_viewer.zoom_width()

    # --- Theme handling ---
    def _prepare_themed_icons(self):
        """Uygulama başlangıcında tüm temalar için SVG ikonlarını hazırlar."""
        try:
            from gui.svg_utils import create_themed_icons
            icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
            
            # Tema dizinlerini kontrol et, yoksa oluştur
            print("Tema bazlı SVG ikonları hazırlanıyor...")
            create_themed_icons(icons_dir)
            print("Tema bazlı SVG ikonları hazırlandı.")
        except Exception as e:
            print(f"Tema bazlı SVG ikonları hazırlanırken hata oluştu: {e}")
            import traceback
            traceback.print_exc()
            
    # _update_toolbar_icons metodu kaldırıldı ve toolbar_manager.py'deki update_button_icons metodu kullanılıyor
    
    def apply_theme(self, theme_name):
        """Applies the selected qt-material theme and updates SVG icons."""
        print(f"--- Applying theme: {theme_name} ---")
        try:
            # Construct full path to the theme file
            qt_material_path = qt_material.__path__[0]
            theme_file_path = os.path.join(qt_material_path, 'themes', f"{theme_name}.xml")

            print(f"Attempting to apply theme file path: {theme_file_path}")
            if os.path.exists(theme_file_path):
                apply_stylesheet(self.app, theme=theme_file_path) # Pass full path
                print(f"qt_material.apply_stylesheet called with path: {theme_file_path}")
            else:
                print(f"ERROR: Theme file not found at {theme_file_path}")
                return # Don't proceed if file not found

            # Tema verilerini al ve ikon temasını ayarla (get_theme uses name without extension)
            try:
                theme_data = get_theme(theme_name)
                if theme_data and 'icon_theme' in theme_data:
                    print(f"Setting icon theme: {theme_data['icon_theme']}") # Debug print
                    set_icons_theme(theme_data['icon_theme'])
                    
                    # Tema değiştiğinde önceden hazırlanmış tema bazlı SVG ikonlarını kullanacağız
                    # İlk çalıştırmada, eğer tema bazlı ikonlar oluşturulmamışsa oluşturalım
                    from gui.svg_utils import create_themed_icons
                    icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
                    
                    # Tema dizinlerini kontrol et, yoksa oluştur
                    theme_dir = os.path.join(icons_dir, theme_name)
                    if not os.path.exists(theme_dir):
                        print(f"Tema için ikon dizini oluşturuluyor: {theme_name}")
                        create_themed_icons(icons_dir)
                else:
                    # If no specific icon theme is defined, don't call set_icons_theme.
                    # Let qt-material handle defaults based on the main theme.
                    print(f"No specific icon theme found for {theme_name}. Skipping explicit icon theme setting.") # Debug print
            except Exception as theme_error:
                # If getting theme data fails, don't call set_icons_theme.
                print(f"Error getting theme data: {theme_error}. Skipping explicit icon theme setting.")
            
            # Tema ayarlarını kaydet
            self.current_theme = theme_name
            self.settings.setValue("theme", theme_name)
            print(f"Theme successfully set to: {theme_name}") # Debug print
            
            # Toolbar butonlarının ikonlarını güncelle
            self.toolbar_manager.update_button_icons(theme_name)
            
            # Arayüzü yenile (Repolish deneyelim)
            # self.update() # update() yeterli olmayabilir
            self.style().unpolish(self)
            self.style().polish(self)
            # Ayrıca uygulama genelinde stilin yenilenmesini tetikleyebiliriz
            self.app.processEvents() # Olay döngüsünü işleterek güncellemelerin görünmesini sağla
            print(f"Theme application finished for: {theme_name}") # Bitiş logu
        except Exception as e:
            print(f"ERROR applying theme {theme_name}: {e}") # Catch and print any exception
            import traceback
            traceback.print_exc() # Print full traceback for detailed error info

    # --- Edit Toolbar Actions ---
    def add_note(self):
        """Enable note adding mode."""
        if self._check_doc_open():
            self.pdf_viewer.set_annotation_mode("note")
            self.status_bar.showMessage("Not eklemek için tıklayın.")

    def add_text(self):
        """Enable text adding mode."""
        if self._check_doc_open():
            self.pdf_viewer.set_annotation_mode("text")
            self.status_bar.showMessage("Metin eklemek için tıklayıp sürükleyin veya tıklayın.")

    def add_line(self):
        """Enable line adding mode."""
        if self._check_doc_open():
            self.pdf_viewer.set_annotation_mode("line")
            self.status_bar.showMessage("Çizgi eklemek için tıklayıp sürükleyin.")

    def highlight(self):
        """Enable highlight mode."""
        if self._check_doc_open():
            self.pdf_viewer.set_annotation_mode("highlight")
            self.status_bar.showMessage("Vurgulamak için metni seçin.")

    def add_circle(self):
        """Enable circle adding mode."""
        if self._check_doc_open():
            self.pdf_viewer.set_annotation_mode("circle")
            self.status_bar.showMessage("Çember eklemek için tıklayıp sürükleyin.")

    def add_stamp(self):
        """Enable stamp adding mode."""
        if self._check_doc_open():
            self.pdf_viewer.set_annotation_mode("stamp")
            self.status_bar.showMessage("Damga (ONAYLANDI) eklemek için tıklayın.")

    def _check_doc_open(self):
        """Helper to check if a document is open."""
        if not self.pdf_handler or not self.pdf_handler.doc:
            print("Lütfen önce bir PDF dosyası açın.")
            self.status_bar.showMessage("Hata: PDF dosyası açık değil.")
            return False
        return True

    # --- Window close event ---
    def closeEvent(self, event):
        """Handle the window close event."""
        # TODO: Check for unsaved changes before closing
        if self.pdf_handler.modified:
            # Ask user if they want to save changes
            # reply = QMessageBox.question(self, 'Save Changes?',
            #                            'The document has been modified. Save changes?',
            #                            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            # if reply == QMessageBox.StandardButton.Save:
            #     if not self.save_pdf():
            #         event.ignore() # Prevent closing if save failed
            #         return
            # elif reply == QMessageBox.StandardButton.Cancel:
            #     event.ignore()
            #     return
            pass # For now, just close

        # Save preferences before closing
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        # Use the correct attribute name from PDFViewer
        self.settings.setValue("zoomScale", self.pdf_viewer.current_scale) # Save current zoom scale
        self.settings.setValue("theme", self.current_theme) # Ensure theme is saved (redundant but safe)

        self.pdf_handler.close_document() # Ensure document is closed
        super().closeEvent(event)

    def create_status_bar(self):
        """Creates the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

# Example usage for testing this window directly (optional)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())
