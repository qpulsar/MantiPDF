import sys
import os # Import os
import qt_material # Import qt_material to get its path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from qt_material import apply_stylesheet, set_icons_theme, get_theme

# Import the main window class
from gui.main_window import MainWindow

def main():
    """Main function to run the MantiPDF application."""
    app = QApplication(sys.argv)

    # Apply the initial theme saved in settings
    settings = QSettings("MantiPDF", "Editor")
    initial_theme = settings.value("theme", "dark_teal")
    try:
        # Construct full path to the theme file
        qt_material_path = qt_material.__path__[0]
        theme_file_path = os.path.join(qt_material_path, 'themes', f"{initial_theme}.xml")

        print(f"Attempting to apply initial theme file path from main.py: {theme_file_path}")
        if os.path.exists(theme_file_path):
            apply_stylesheet(app, theme=theme_file_path) # Pass full path
            print(f"apply_stylesheet called with path: {theme_file_path}")
            # Optionally set initial icon theme here too, if needed
            theme_data = get_theme(initial_theme) # get_theme still uses the name without extension
            if theme_data and 'icon_theme' in theme_data:
                set_icons_theme(theme_data['icon_theme'])
            print(f"Initial theme {initial_theme} applied successfully from main.py.")
        else:
             print(f"ERROR: Initial theme file not found at {theme_file_path}")

    except Exception as e:
        print(f"ERROR applying initial theme {initial_theme} in main.py: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for detailed error info

    # Create and show the main window
    window = MainWindow(app) # Pass the themed app instance
    window.show()

    # Start the application event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
