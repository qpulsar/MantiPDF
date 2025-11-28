from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QListWidget, QListWidgetItem, QGroupBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
import os

class MergeFolderDialog(QDialog):
    """Klasörden PDF birleştirme için sıralama diyalogu."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Klasörden PDF Birleştir")
        self.setMinimumWidth(520)
        self.folder_path = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # Klasör seçimi
        folder_group = QGroupBox("Klasör Seçimi")
        folder_layout = QHBoxLayout(folder_group)
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        browse_btn = QPushButton("Gözat...")
        browse_btn.clicked.connect(self._choose_folder)
        folder_layout.addWidget(self.folder_edit)
        folder_layout.addWidget(browse_btn)
        main_layout.addWidget(folder_group)

        # Seçenekler
        options_layout = QHBoxLayout()
        self.include_subdirs_chk = QCheckBox("Alt klasörleri dahil et")
        options_layout.addWidget(self.include_subdirs_chk)
        options_layout.addStretch(1)
        main_layout.addLayout(options_layout)

        # PDF listesi ve kontroller
        list_group = QGroupBox("Birleştirme Sırası")
        list_layout = QVBoxLayout(list_group)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.DropAction.MoveAction)
        list_layout.addWidget(self.list_widget)

        # Sıralama butonları
        sort_buttons_layout = QHBoxLayout()
        sort_name_btn = QPushButton("İsme göre sırala (A→Z)")
        sort_name_btn.clicked.connect(self._sort_by_name)
        sort_name_desc_btn = QPushButton("İsme göre sırala (Z→A)")
        sort_name_desc_btn.clicked.connect(lambda: self._sort_by_name(reverse=True))
        move_up_btn = QPushButton("Yukarı Taşı")
        move_up_btn.clicked.connect(self._move_up)
        move_down_btn = QPushButton("Aşağı Taşı")
        move_down_btn.clicked.connect(self._move_down)

        sort_buttons_layout.addWidget(sort_name_btn)
        sort_buttons_layout.addWidget(sort_name_desc_btn)
        sort_buttons_layout.addStretch(1)
        sort_buttons_layout.addWidget(move_up_btn)
        sort_buttons_layout.addWidget(move_down_btn)
        list_layout.addLayout(sort_buttons_layout)

        main_layout.addWidget(list_group)

        # Onay butonları
        btns_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Birleştir")
        self.ok_btn.clicked.connect(self._accept_if_valid)
        self.ok_btn.setEnabled(False)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btns_layout.addWidget(self.ok_btn)
        btns_layout.addWidget(cancel_btn)
        main_layout.addLayout(btns_layout)

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç")
        if not folder:
            return
        self.folder_path = folder
        self.folder_edit.setText(folder)
        self._load_pdfs()

    def _load_pdfs(self):
        self.list_widget.clear()
        pdf_files = self._find_pdfs(self.folder_path, self.include_subdirs_chk.isChecked())
        for path in pdf_files:
            item = QListWidgetItem(os.path.basename(path))
            item.setToolTip(path)
            # Tam yolu UserRole'a koy
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.list_widget.addItem(item)
        self.ok_btn.setEnabled(self.list_widget.count() > 0)

    def _find_pdfs(self, root, include_subdirs):
        result = []
        if include_subdirs:
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if fn.lower().endswith('.pdf'):
                        result.append(os.path.join(dirpath, fn))
        else:
            try:
                for fn in os.listdir(root):
                    if fn.lower().endswith('.pdf'):
                        result.append(os.path.join(root, fn))
            except FileNotFoundError:
                pass
        # Varsayılan olarak isim artan sırada
        result.sort(key=lambda p: os.path.basename(p).lower())
        return result

    def _sort_by_name(self, reverse=False):
        items = [self.list_widget.item(i) for i in range(self.list_widget.count())]
        items.sort(key=lambda it: it.text().lower(), reverse=reverse)
        self.list_widget.clear()
        for it in items:
            self.list_widget.addItem(it)

    def _move_up(self):
        rows = sorted([idx.row() for idx in self.list_widget.selectedIndexes()])
        if not rows:
            return
        if rows[0] == 0:
            return
        for row in rows:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row - 1, item)
            item.setSelected(True)

    def _move_down(self):
        rows = sorted([idx.row() for idx in self.list_widget.selectedIndexes()], reverse=True)
        if not rows:
            return
        if rows[0] == self.list_widget.count() - 1:
            return
        for row in rows:
            item = self.list_widget.takeItem(row)
            self.list_widget.insertItem(row + 1, item)
            item.setSelected(True)

    def _accept_if_valid(self):
        if self.list_widget.count() == 0:
            QMessageBox.information(self, "Birleştirme", "Birleştirilecek PDF bulunamadı.")
            return
        self.accept()

    def get_ordered_file_paths(self):
        paths = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                paths.append(path)
        return paths
