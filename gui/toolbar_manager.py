from PyQt6.QtWidgets import QToolBar, QPushButton, QWidget, QVBoxLayout, QComboBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

class ToolbarManager:
    """Manages the toolbars for the MantiPDF Editor."""

    def __init__(self, main_window):
        """Initialize the toolbar manager."""
        self.main_window = main_window
        self.toolbars = {}

    def create_toolbar(self, name):
        """Create a toolbar with the given name."""
        toolbar = QToolBar(name, self.main_window)
        self.main_window.addToolBar(toolbar)
        self.toolbars[name] = toolbar
        return toolbar

    def add_button(self, toolbar, text, icon_name, callback):
        """Add a button to the toolbar."""
        button = QPushButton(text)
        if icon_name:
            button.setIcon(QIcon(f"icon:/{icon_name}"))
        button.clicked.connect(callback)
        toolbar.addWidget(button)
        return button

    def add_action(self, toolbar, action):
        """Add an action to the toolbar."""
        toolbar.addAction(action)

    def add_separator(self, toolbar):
        """Add a separator to the toolbar."""
        toolbar.addSeparator()

    def add_widget(self, toolbar, widget):
        """Add a widget to the toolbar."""
        toolbar.addWidget(widget)
