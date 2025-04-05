import os
from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QVBoxLayout, QComboBox, QFileDialog
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, QSize
from gui.svg_utils import get_icon_for_theme

class ToolbarManager:
    """Manages the toolbars for the MantiPDF Editor."""

    def __init__(self, main_window):
        """Initialize the toolbar manager."""
        self.main_window = main_window
        self.toolbars = {}
        # Buton ikonlarını ve isimlerini saklayacak sözlük
        self.button_icons = {}

    def create_toolbar(self, name):
        """Create a toolbar with the given name."""
        toolbar = QToolBar(name, self.main_window)
        self.main_window.addToolBar(toolbar)
        self.toolbars[name] = toolbar
        return toolbar

    def add_button(self, toolbar, text, icon_name, callback):
        """Add a button to the toolbar."""
        text_view = False
        if not text_view:
            text1 = ""
        else:
            text1 = text
        button = QPushButton(text1)
        # Gelen text'i tooltip (ipucu) olarak ata
        button.setToolTip(text)
        if icon_name:
            # Tema bazlı ikon yolunu al
            icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
            current_theme = self.main_window.current_theme
            icon_path = get_icon_for_theme(f"{icon_name}.svg", current_theme, icons_dir)
            button.setIcon(QIcon(icon_path))
            # İkon boyutunu ayarla (32x32 piksel)
            button.setIconSize(QSize(26, 26))
            # Butonun minimum boyutunu ayarla
            button.setMinimumSize(32, 32)
            # İkon adını ve buton referansını sakla
            self.button_icons[button] = icon_name
        
        # Butonlara hover efekti ekle
        button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 4px;
                padding: 3px;
                background-color: transparent;
                transition-duration: 0.2s;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 0.2);
                border: 1px solid rgba(128, 128, 128, 0.3);
                margin: -1px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(128, 128, 128, 0.4);
                border: 1px solid rgba(128, 128, 128, 0.5);
                margin: -1px;
            }
        """)
        
        button.clicked.connect(callback)
        toolbar.addWidget(button)
        return button
        
    def update_button_icons(self, theme_name):
        """Toolbar butonlarının ikonlarını belirtilen temaya göre günceller."""
        try:
            print(f"Toolbar butonlarının ikonları '{theme_name}' temasına göre güncelleniyor...")
            icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
            
            # Saklanan buton ve ikon adlarını kullanarak ikonları güncelle
            for button, icon_name in self.button_icons.items():
                icon_path = get_icon_for_theme(f"{icon_name}.svg", theme_name, icons_dir)
                button.setIcon(QIcon(icon_path))
                # İkon boyutunu korumak için tekrar ayarla
                button.setIconSize(QSize(26, 26))
                print(f"'{button.text()}' butonu için ikon güncellendi: {icon_path}")
                
            print("Toolbar butonlarının ikonları güncellendi.")
        except Exception as e:
            print(f"Toolbar butonlarının ikonları güncellenirken hata oluştu: {e}")
            import traceback
            traceback.print_exc()

    def add_action(self, toolbar, action):
        """Add an action to the toolbar."""
        toolbar.addAction(action)

    def add_separator(self, toolbar):
        """Add a separator to the toolbar."""
        toolbar.addSeparator()

    def add_widget(self, toolbar, widget):
        """Add a widget to the toolbar."""
        toolbar.addWidget(widget)
