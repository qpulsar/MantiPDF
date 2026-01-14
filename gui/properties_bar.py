from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSpinBox, QComboBox, QPushButton, QColorDialog
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor

class PropertiesBar(QWidget):
    """Bar containing properties for the active annotation tool."""
    
    properties_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)
        
        # Default properties
        self.current_props = {
            "stroke_color": QColor(255, 0, 0),
            "fill_color": QColor(255, 255, 0, 0), # Transparent yellow default
            "thickness": 2,
            "font_size": 12,
            "font_family": "helv",
            "arrow_type": "none"
        }
        
        self.setup_ui()
        self.hide() # Hidden by default, shown when a tool is active
        
    def setup_ui(self):
        # Stroke Color
        self.layout.addWidget(QLabel("Renk:"))
        self.stroke_btn = QPushButton()
        self.stroke_btn.setFixedSize(20, 20)
        self.update_color_btn(self.stroke_btn, self.current_props["stroke_color"])
        self.stroke_btn.clicked.connect(self.pick_stroke_color)
        self.layout.addWidget(self.stroke_btn)
        
        # Thickness
        self.layout.addWidget(QLabel("Kalınlık:"))
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 20)
        self.thickness_spin.setMinimumWidth(50)
        self.thickness_spin.setValue(self.current_props["thickness"])
        self.thickness_spin.valueChanged.connect(self.on_thickness_changed)
        self.layout.addWidget(self.thickness_spin)
        
        # Fill Color (initially hidden or enabled based on tool)
        self.fill_label = QLabel("Dolgu:")
        self.layout.addWidget(self.fill_label)
        self.fill_btn = QPushButton()
        self.fill_btn.setFixedSize(20, 20)
        self.update_color_btn(self.fill_btn, self.current_props["fill_color"])
        self.fill_btn.clicked.connect(self.pick_fill_color)
        self.layout.addWidget(self.fill_btn)
        
        # Font Size
        self.font_label = QLabel("Boyut:")
        self.layout.addWidget(self.font_label)
        self.font_spin = QSpinBox()
        self.font_spin.setRange(6, 72)
        self.font_spin.setMinimumWidth(50)
        self.font_spin.setValue(self.current_props["font_size"])
        self.font_spin.valueChanged.connect(self.on_font_size_changed)
        self.layout.addWidget(self.font_spin)
        
        # Font Family
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["helv", "tiro", "cour", "symb", "zabd"])
        self.font_family_combo.setMinimumWidth(80)
        self.font_family_combo.currentTextChanged.connect(self.on_font_family_changed)
        self.layout.addWidget(self.font_family_combo)

        # Arrow Type
        self.arrow_label = QLabel("Ok:")
        self.layout.addWidget(self.arrow_label)
        self.arrow_combo = QComboBox()
        self.arrow_combo.addItems(["none", "start", "end", "both"])
        self.arrow_combo.setMinimumWidth(80)
        self.arrow_combo.currentTextChanged.connect(self.on_arrow_type_changed)
        self.layout.addWidget(self.arrow_combo)

        self.layout.addStretch()

    def update_color_btn(self, btn, color):
        if color.alpha() == 0:
            btn.setStyleSheet("background-color: white; border: 1px dashed gray;")
        else:
            btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

    def pick_stroke_color(self):
        color = QColorDialog.getColor(self.current_props["stroke_color"], self, "Renk Seç")
        if color.isValid():
            self.current_props["stroke_color"] = color
            self.update_color_btn(self.stroke_btn, color)
            self.properties_changed.emit(self.current_props)

    def pick_fill_color(self):
        color = QColorDialog.getColor(self.current_props["fill_color"], self, "Dolgu Rengi Seç", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            self.current_props["fill_color"] = color
            self.update_color_btn(self.fill_btn, color)
            self.properties_changed.emit(self.current_props)

    def on_thickness_changed(self, val):
        self.current_props["thickness"] = val
        self.properties_changed.emit(self.current_props)

    def on_font_size_changed(self, val):
        self.current_props["font_size"] = val
        self.properties_changed.emit(self.current_props)

    def on_font_family_changed(self, text):
        self.current_props["font_family"] = text
        self.properties_changed.emit(self.current_props)

    def on_arrow_type_changed(self, text):
        self.current_props["arrow_type"] = text
        self.properties_changed.emit(self.current_props)

    def set_current_properties(self, props):
        """Updates the UI widgets with the given properties without emitting signals."""
        self.current_props = props.copy()
        
        self.blockSignals(True)
        self.thickness_spin.blockSignals(True)
        self.font_spin.blockSignals(True)
        self.font_family_combo.blockSignals(True)
        self.arrow_combo.blockSignals(True)
        
        self.update_color_btn(self.stroke_btn, self.current_props["stroke_color"])
        self.update_color_btn(self.fill_btn, self.current_props["fill_color"])
        self.thickness_spin.setValue(self.current_props["thickness"])
        self.font_spin.setValue(self.current_props["font_size"])
        
        index = self.font_family_combo.findText(self.current_props["font_family"])
        if index >= 0:
            self.font_family_combo.setCurrentIndex(index)
            
        index = self.arrow_combo.findText(self.current_props["arrow_type"])
        if index >= 0:
            self.arrow_combo.setCurrentIndex(index)
            
        self.arrow_combo.blockSignals(False)
        self.font_family_combo.blockSignals(False)
        self.font_spin.blockSignals(False)
        self.thickness_spin.blockSignals(False)
        self.blockSignals(False)

    def update_for_annot_type(self, annot_type):
        """Updates control visibility based on the annotation type name (e.g., 'Circle', 'Line')."""
        self.show()
        
        # Mapping fitz type names to our internal logic
        is_text = annot_type in ["Text", "FreeText", "StickyNote", "note", "text"]
        is_line = annot_type in ["Line", "PolyLine", "line"]
        is_shape = annot_type in ["Circle", "Square", "Polygon", "circle"]
        
        self.fill_label.setVisible(is_shape)
        self.fill_btn.setVisible(is_shape)
        
        self.font_label.setVisible(is_text)
        self.font_spin.setVisible(is_text)
        self.font_family_combo.setVisible(is_text)
        
        self.arrow_label.setVisible(is_line)
        self.arrow_combo.setVisible(is_line)

    def update_for_tool(self, tool_mode):
        if tool_mode is None:
             self.hide()
             return

        self.show()
        if tool_mode == "select":
             # Wait for selection signal to show specific properties
             # or show all by default if that's preferred.
             # User asked for unused ones to be hidden, so we start empty or with general ones.
             self.update_for_annot_type("select") 
             return
        
        # Re-use the logic by passing tool_mode as annot_type
        self.update_for_annot_type(tool_mode)
