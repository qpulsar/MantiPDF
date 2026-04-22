import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QLineEdit, QPushButton, QLabel, QScrollArea, 
                             QFrame, QSplitter, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor, QFont
from core.structuring_handler import StructuringHandler

class AIChatBubble(QFrame):
    """A single message bubble in the chat UI."""
    def __init__(self, text, sender="user", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        
        self.sender_label = QLabel(sender.upper())
        self.sender_label.setStyleSheet("font-weight: bold; font-size: 10px; color: gray;")
        
        self.text_label = QLabel(text)
        self.text_label.setWordWrap(True)
        self.text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if sender == "user":
            self.setStyleSheet("background-color: rgba(0, 150, 136, 0.1); border-radius: 10px; margin-left: 20px;")
        else:
            self.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; margin-right: 20px;")
            
        layout.addWidget(self.sender_label)
        layout.addWidget(self.text_label)

class AIAssistantDock(QWidget):
    """Dockable widget for AI interactions (Chat, Summarize, etc.)."""
    
    send_query = pyqtSignal(str) # Emitted when user sends a chat message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.ai_handler = main_window.ai_handler
        self.struct_handler = StructuringHandler(self.ai_handler)
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Quick Actions ---
        actions_layout = QHBoxLayout()
        self.summarize_btn = QPushButton("Özetle")
        self.summarize_btn.setToolTip("Tüm belgeyi özetle")
        self.keywords_btn = QPushButton("Anahtar Kelimeler")
        self.timeline_btn = QPushButton("Zaman Çizelgesi")
        
        actions_layout.addWidget(self.summarize_btn)
        actions_layout.addWidget(self.keywords_btn)
        actions_layout.addWidget(self.timeline_btn)
        layout.addLayout(actions_layout)

        # --- Chat Area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()
        
        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area)

        # --- Progress Bar (Hidden by default) ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(2)
        layout.addWidget(self.progress_bar)

        # --- Input Area ---
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("PDF hakkında bir soru sorun...")
        self.chat_input.returnPressed.connect(self.on_send_clicked)
        
        self.send_btn = QPushButton("Gönder")
        self.send_btn.clicked.connect(self.on_send_clicked)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)

    def connect_signals(self):
        self.ai_handler.response_received.connect(self.on_ai_response)
        self.ai_handler.error_occurred.connect(self.on_ai_error)
        self.ai_handler.progress_updated.connect(self.on_progress)
        
        self.summarize_btn.clicked.connect(self.main_window.ai_summarize_doc)
        self.keywords_btn.clicked.connect(self.on_keywords_clicked)
        self.timeline_btn.clicked.connect(self.on_timeline_clicked)

    def on_progress(self, value, message):
        self.progress_bar.setVisible(True)
        if value < 100:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setVisible(False)
        self.main_window.status_bar.showMessage(message)

    def on_keywords_clicked(self):
        self.add_message("Belgedeki anahtar kavramlar çıkarılıyor...", "ai")
        prompt = "Lütfen bu belgedeki anahtar kavramları ve aralarındaki ilişkileri liste şeklinde çıkar."
        self.ai_handler.generate_response(prompt)

    def on_timeline_clicked(self):
        self.add_message("Belgedeki kronolojik olaylar analiz ediliyor...", "ai")
        # Extract text for indexing/timeline (first 10 pages for now)
        text = ""
        for i in range(min(10, self.main_window.pdf_handler.page_count)):
            text += self.main_window.pdf_handler.doc[i].get_text()
            
        # We can run this in background
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # This is a bit blocking for now, ideally should be in a thread
        data = self.struct_handler.generate_timeline_data(text)
        self.progress_bar.setVisible(False)
        
        if data and isinstance(data, list):
            formatted_timeline = "### Zaman Çizelgesi\n\n"
            for item in data:
                formatted_timeline += f"- **{item.get('date', 'Belirsiz')}**: {item.get('event', '')}\n"
            self.add_message(formatted_timeline, "ai")
        else:
            self.add_message("Zaman çizelgesi oluşturulamadı.", "ai")

    def on_send_clicked(self):
        text = self.chat_input.text().strip()
        if text:
            self.add_message(text, "user")
            self.chat_input.clear()
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0) # Indeterminate
            
            # Start AI request
            self.ai_handler.generate_response(text)

    @pyqtSlot(str)
    def on_ai_response(self, response):
        self.progress_bar.setVisible(False)
        self.add_message(response, "ai")

    @pyqtSlot(str)
    def on_ai_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.add_message(f"Hata: {error_msg}", "ai")

    def add_message(self, text, sender):
        bubble = AIChatBubble(text, sender)
        # Add before the stretch
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        
        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
