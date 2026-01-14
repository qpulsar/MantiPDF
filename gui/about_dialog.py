from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QWidget
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
import os

class AboutDialog(QDialog):
    """About dialog showing app information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hakkında - MantıPDF")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "splash.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # App Name
        title_label = QLabel("MantıPDF")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(title_label)
        
        # Slogan
        slogan_label = QLabel('"PDF\'ye lezzet katan editör."')
        slogan_font = QFont()
        slogan_font.setPointSize(14)
        slogan_font.setItalic(True)
        slogan_label.setFont(slogan_font)
        slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slogan_label.setStyleSheet("color: #666;")
        layout.addWidget(slogan_label)
        
        # Acronym explanation
        acronym_text = """
<div style="text-align: center; line-height: 1.8;">
<b>M</b>anipüle et · <b>A</b>not al · <b>N</b>ot Tut · <b>T</b>asarla · <b>İ</b>ncele – <b>PDF</b>
<br><br>
🛠️ <b>Manipülasyon</b> · 🖋️ <b>Not alma</b> · 🎨 <b>Tasarım</b> · 🔎 <b>İnceleme</b>
</div>
"""
        acronym_label = QLabel(acronym_text)
        acronym_label.setTextFormat(Qt.TextFormat.RichText)
        acronym_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        acronym_label.setWordWrap(True)
        layout.addWidget(acronym_label)
        
        # Developer
        dev_label = QLabel("Developed by <b>Mehmet Emin Korkusuz</b>")
        dev_label.setTextFormat(Qt.TextFormat.RichText)
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dev_label)
        
        # Links
        links_text = """
<div style="text-align: center;">
<a href="https://github.com/qpulsar/MantiPDF" style="color: #2196F3;">GitHub</a>
&nbsp;·&nbsp;
<a href="https://korkusuz.gen.tr" style="color: #2196F3;">korkusuz.gen.tr</a>
</div>
"""
        links_label = QLabel(links_text)
        links_label.setTextFormat(Qt.TextFormat.RichText)
        links_label.setOpenExternalLinks(True)
        links_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(links_label)
        
        layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Kapat")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
