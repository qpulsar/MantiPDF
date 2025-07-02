from PyQt6.QtWidgets import QListWidget, QListView, QListWidgetItem, QAbstractItemView
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, pyqtSignal

class ThumbnailView(QListWidget):
    """
    A widget to display thumbnails of PDF pages, with drag-and-drop reordering.
    """
    page_moved = pyqtSignal(int, int)  # from_index, to_index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setIconSize(QSize(100, 150))
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setSpacing(10)
        
        # Enable drag and drop for reordering
        self.setMovement(QListView.Movement.Snap)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def dropEvent(self, event):
        if event.source() == self and event.dropAction() == Qt.DropAction.MoveAction:
            source_item = self.currentItem()
            if not source_item:
                return
            
            from_index = self.row(source_item)
            
            # Let the parent class handle the visual move
            super().dropEvent(event)
            
            # Get the new index after the move
            to_index = self.row(source_item)
            
            if from_index != to_index:
                # Emit a signal that the user has reordered a page
                self.page_moved.emit(from_index, to_index)
        else:
            super().dropEvent(event)

    def add_thumbnail(self, pixmap: QPixmap, page_num: int):
        """
        Adds a thumbnail to the view.
        """
        if not pixmap.isNull():
            item = QListWidgetItem(QIcon(pixmap), f"Page {page_num + 1}")
            item.setData(Qt.ItemDataRole.UserRole, page_num)
            item.setSizeHint(self.iconSize())
            self.addItem(item)

    def clear_thumbnails(self):
        """
        Removes all thumbnails from the view.
        """
        self.clear()

    def update_thumbnails(self, pdf_handler):
        """
        Updates the thumbnails based on the current PDF document.
        """
        self.clear_thumbnails()
        if pdf_handler and pdf_handler.doc:
            for page_num in range(pdf_handler.page_count):
                # Use a smaller scale for thumbnails
                pixmap = pdf_handler.get_page_pixmap(page_num, scale=0.2)
                if pixmap:
                    self.add_thumbnail(pixmap, page_num)

