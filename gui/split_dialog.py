from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QRadioButton, QButtonGroup, QFileDialog,
                            QListWidget, QListWidgetItem, QMessageBox, QGroupBox)
from PyQt6.QtCore import Qt

class SplitDialog(QDialog):
    """Dialog for splitting PDF files."""
    
    def __init__(self, parent=None, page_count=0):
        """Initialize the split dialog.
        
        Args:
            parent: The parent widget.
            page_count: The number of pages in the PDF document.
        """
        super().__init__(parent)
        self.parent = parent
        self.page_count = page_count
        self.output_dir = ""
        self.page_ranges = []
        
        self.setWindowTitle("PDF Böl")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(f"PDF dosyası {self.page_count} sayfa içeriyor.")
        main_layout.addWidget(info_label)
        
        # Split options group
        options_group = QGroupBox("Bölme Seçenekleri")
        options_layout = QVBoxLayout(options_group)
        
        # Radio buttons for split options
        self.split_all_radio = QRadioButton("Her sayfayı ayrı PDF olarak kaydet")
        self.split_range_radio = QRadioButton("Sayfa aralıklarına göre böl")
        
        # Group radio buttons
        self.option_group = QButtonGroup(self)
        self.option_group.addButton(self.split_all_radio, 1)
        self.option_group.addButton(self.split_range_radio, 2)
        self.split_all_radio.setChecked(True)  # Default option
        
        options_layout.addWidget(self.split_all_radio)
        options_layout.addWidget(self.split_range_radio)
        
        main_layout.addWidget(options_group)
        
        # Page ranges input (for split_range option)
        ranges_group = QGroupBox("Sayfa Aralıkları")
        ranges_layout = QVBoxLayout(ranges_group)
        
        ranges_info = QLabel("Sayfa aralıklarını virgülle ayırarak girin (örn: 1-3,5,7-10)\nSayfa numaraları 1'den başlar.")
        self.ranges_input = QLineEdit()
        self.ranges_input.setPlaceholderText("1-3,5,7-10")
        self.ranges_input.setEnabled(False)  # Disabled by default
        
        ranges_layout.addWidget(ranges_info)
        ranges_layout.addWidget(self.ranges_input)
        
        main_layout.addWidget(ranges_group)
        
        # Output directory selection
        dir_group = QGroupBox("Çıktı Dizini")
        dir_layout = QHBoxLayout(dir_group)
        
        self.dir_input = QLineEdit()
        self.dir_input.setReadOnly(True)
        self.dir_input.setPlaceholderText("Çıktı dizinini seçin...")
        
        dir_button = QPushButton("Gözat...")
        dir_button.clicked.connect(self.select_output_dir)
        
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(dir_button)
        
        main_layout.addWidget(dir_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.split_button = QPushButton("Böl")
        self.split_button.clicked.connect(self.accept)
        self.split_button.setEnabled(False)  # Disabled until output dir is selected
        
        cancel_button = QPushButton("İptal")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.split_button)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Connect signals
        self.option_group.buttonClicked.connect(self.on_option_changed)
    
    def on_option_changed(self, button):
        """Handle option change."""
        self.ranges_input.setEnabled(button == self.split_range_radio)
    
    def select_output_dir(self):
        """Open a dialog to select the output directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Çıktı Dizinini Seç")
        if dir_path:
            self.output_dir = dir_path
            self.dir_input.setText(dir_path)
            self.split_button.setEnabled(True)
    
    def get_page_ranges(self):
        """Parse the page ranges input and return a list of (start_page, end_page) tuples.
        
        Returns:
            A list of (start_page, end_page) tuples if split_range option is selected,
            None if split_all option is selected.
        """
        if self.option_group.checkedId() == 1:  # split_all option
            return None
        
        # Parse page ranges
        ranges_text = self.ranges_input.text().strip()
        if not ranges_text:
            return None
        
        try:
            page_ranges = []
            for range_str in ranges_text.split(','):
                range_str = range_str.strip()
                if '-' in range_str:
                    start, end = map(int, range_str.split('-'))
                    # Convert to 0-indexed
                    start = max(1, start) - 1
                    end = min(self.page_count, end) - 1
                    page_ranges.append((start, end))
                else:
                    page_num = int(range_str)
                    # Convert to 0-indexed
                    page_num = max(1, min(self.page_count, page_num)) - 1
                    page_ranges.append((page_num, page_num))
            
            return page_ranges
        except ValueError:
            QMessageBox.warning(self, "Geçersiz Sayfa Aralığı", 
                               "Sayfa aralıklarını doğru formatta girin (örn: 1-3,5,7-10)")
            return None
    
    def accept(self):
        """Handle the accept action."""
        if not self.output_dir:
            QMessageBox.warning(self, "Çıktı Dizini Seçilmedi", 
                               "Lütfen çıktı dizinini seçin.")
            return
        
        if self.option_group.checkedId() == 2:  # split_range option
            ranges_text = self.ranges_input.text().strip()
            if not ranges_text:
                QMessageBox.warning(self, "Sayfa Aralıkları Girilmedi", 
                                   "Lütfen sayfa aralıklarını girin veya her sayfayı ayrı PDF olarak kaydetme seçeneğini seçin.")
                return
            
            # Validate page ranges
            page_ranges = self.get_page_ranges()
            if page_ranges is None:
                return
        
        super().accept()