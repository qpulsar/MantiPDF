from PyQt6.QtWidgets import QListWidget, QListView, QListWidgetItem
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt

class ThumbnailView(QListWidget):
    """
    A widget to display thumbnails of PDF pages.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setIconSize(QSize(100, 150)) # Adjust size as needed
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static) # Prevent dragging for now
        self.setSpacing(10) # Space between thumbnails

    def add_thumbnail(self, pixmap: QPixmap, page_num: int):
        """
        Adds a thumbnail to the view.
        """
        if not pixmap.isNull():
            item = QListWidgetItem(QIcon(pixmap), f"Page {page_num + 1}")
            item.setData(Qt.ItemDataRole.UserRole, page_num) # Store page number
            item.setSizeHint(self.iconSize()) # Ensure item size matches icon size
            self.addItem(item)

    def clear_thumbnails(self):
        """
        Removes all thumbnails from the view.
        """
        self.clear()

    def update_thumbnails(self, pdf_handler):
        """
        Updates the thumbnails based on the current PDF document.

        Args:
            pdf_handler: An instance of the PDFHandler containing the document.
        """
        self.clear_thumbnails()
        if pdf_handler and pdf_handler.doc:
            for page_num in range(len(pdf_handler.doc)):
                pixmap = pdf_handler.get_page_pixmap(page_num, scale=0.2) # Get a smaller pixmap for thumbnail
                if pixmap:
                    self.add_thumbnail(pixmap, page_num)

    # Optional: Connect selection changes to update the main view
    # self.itemSelectionChanged.connect(self.on_thumbnail_selected)
    # def on_thumbnail_selected(self):
    #     selected_items = self.selectedItems()
    #     if selected_items:
    #         page_num = selected_items[0].data(Qt.ItemDataRole.UserRole)
    #         # Emit a signal or call a method to change the main view to page_num
    #         print(f"Thumbnail selected: Page {page_num + 1}")

