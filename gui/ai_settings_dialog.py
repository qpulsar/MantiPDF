import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QGroupBox, 
                             QFormLayout, QMessageBox, QTabWidget, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from core.security_manager import SecurityManager
from gui.svg_utils import get_icon_for_theme

class AISettingsDialog(QDialog):
    """Dialog for configuring AI providers and API keys."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Ayarları ve API Anahtarları")
        self.setMinimumWidth(500)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        header_label = QLabel("Yapay Zeka Yapılandırması")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        info_label = QLabel("API anahtarlarınız sisteminizin güvenli anahtar zincirinde (Keychain) saklanır.")
        info_label.setStyleSheet("color: gray; margin-bottom: 20px;")
        layout.addWidget(info_label)

        self.tabs = QTabWidget()
        
        # --- OpenAI Tab ---
        self.openai_tab = QWidget()
        openai_layout = QFormLayout(self.openai_tab)
        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("sk-...")
        openai_layout.addRow("OpenAI API Key:", self.openai_key)
        
        self.openai_model = QComboBox()
        self.openai_model.addItems([
            "gpt-5.4", 
            "gpt-5.4-mini", 
            "gpt-5.4-thinking", 
            "gpt-5.4-pro",
            "o1", 
            "o1-mini"
        ])
        
        self.openai_update_btn = QPushButton("Modelleri Güncelle")
        self.openai_update_btn.clicked.connect(self.update_openai_models)
        
        openai_layout.addRow("Varsayılan Model:", self.openai_model)
        openai_layout.addRow("", self.openai_update_btn)
        self.tabs.addTab(self.openai_tab, "OpenAI")

        # --- Anthropic Tab ---
        self.anthropic_tab = QWidget()
        anthropic_layout = QFormLayout(self.anthropic_tab)
        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.EchoMode.Password)
        anthropic_layout.addRow("Anthropic API Key:", self.anthropic_key)
        self.anthropic_model = QComboBox()
        self.anthropic_model.addItems([
            "claude-opus-4.7", 
            "claude-sonnet-4.6", 
            "claude-3-7-sonnet",
            "claude-3-5-sonnet-latest", 
            "claude-3-5-haiku-latest"
        ])
        self.anthropic_update_btn = QPushButton("Modelleri Güncelle")
        self.anthropic_update_btn.clicked.connect(self.update_anthropic_models)
        anthropic_layout.addRow("Varsayılan Model:", self.anthropic_model)
        anthropic_layout.addRow("", self.anthropic_update_btn)
        self.tabs.addTab(self.anthropic_tab, "Anthropic")

        # --- Gemini Tab ---
        self.gemini_tab = QWidget()
        gemini_layout = QFormLayout(self.gemini_tab)
        self.gemini_key = QLineEdit()
        self.gemini_key.setEchoMode(QLineEdit.EchoMode.Password)
        gemini_layout.addRow("Google Gemini API Key:", self.gemini_key)
        self.gemini_model = QComboBox()
        self.gemini_model.addItems([
            "gemini-3.1-pro", 
            "gemini-3.1-flash", 
            "gemini-3.1-flash-lite-preview",
            "gemini-2.0-flash-exp", 
            "gemini-1.5-pro-latest"
        ])
        
        self.gemini_update_btn = QPushButton("Modelleri Güncelle")
        self.gemini_update_btn.clicked.connect(self.update_gemini_models)
        
        gemini_layout.addRow("Varsayılan Model:", self.gemini_model)
        gemini_layout.addRow("", self.gemini_update_btn)
        self.tabs.addTab(self.gemini_tab, "Google Gemini")

        # --- Kimi Tab ---
        self.kimi_tab = QWidget()
        kimi_layout = QFormLayout(self.kimi_tab)
        self.kimi_key = QLineEdit()
        self.kimi_key.setEchoMode(QLineEdit.EchoMode.Password)
        kimi_layout.addRow("Kimi (Moonshot) API Key:", self.kimi_key)
        self.kimi_model = QComboBox()
        self.kimi_model.addItems([
            "kimi-k2.6", 
            "moonshot-v1-128k", 
            "moonshot-v1-32k", 
            "moonshot-v1-8k"
        ])
        self.kimi_update_btn = QPushButton("Modelleri Güncelle")
        self.kimi_update_btn.clicked.connect(self.update_kimi_models)
        kimi_layout.addRow("Varsayılan Model:", self.kimi_model)
        kimi_layout.addRow("", self.kimi_update_btn)
        self.tabs.addTab(self.kimi_tab, "Kimi")

        # --- Local Tab ---
        self.local_tab = QWidget()
        local_layout = QFormLayout(self.local_tab)
        self.local_url = QLineEdit()
        self.local_url.setPlaceholderText("http://localhost:11434")
        local_layout.addRow("Ollama/Local URL:", self.local_url)
        self.tabs.addTab(self.local_tab, "Yerel (Ollama)")

        layout.addWidget(self.tabs)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Kaydet")
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

    def load_settings(self):
        """Load keys from SecurityManager."""
        self.openai_key.setText(SecurityManager.get_api_key("openai") or "")
        self.anthropic_key.setText(SecurityManager.get_api_key("anthropic") or "")
        self.gemini_key.setText(SecurityManager.get_api_key("gemini") or "")
        self.kimi_key.setText(SecurityManager.get_api_key("kimi") or "")
        
        # Load other non-key settings from QSettings
        from PyQt6.QtCore import QSettings
        settings = QSettings("MantiPDF", "AI")
        self.openai_model.setCurrentText(settings.value("openai_model", "gpt-5.4"))
        self.anthropic_model.setCurrentText(settings.value("anthropic_model", "claude-sonnet-4.6"))
        self.gemini_model.setCurrentText(settings.value("gemini_model", "gemini-3.1-flash"))
        self.kimi_model.setCurrentText(settings.value("kimi_model", "kimi-k2.6"))
        self.local_url.setText(settings.value("local_url", "http://localhost:11434"))

    def save_settings(self):
        """Save keys to SecurityManager and other settings to QSettings."""
        success = True
        success &= SecurityManager.set_api_key("openai", self.openai_key.text().strip())
        success &= SecurityManager.set_api_key("anthropic", self.anthropic_key.text().strip())
        success &= SecurityManager.set_api_key("gemini", self.gemini_key.text().strip())
        success &= SecurityManager.set_api_key("kimi", self.kimi_key.text().strip())
        
        from PyQt6.QtCore import QSettings
        settings = QSettings("MantiPDF", "AI")
        settings.setValue("openai_model", self.openai_model.currentText())
        settings.setValue("anthropic_model", self.anthropic_model.currentText())
        settings.setValue("gemini_model", self.gemini_model.currentText())
        settings.setValue("kimi_model", self.kimi_model.currentText())
        settings.setValue("local_url", self.local_url.text().strip())
        
        if success:
            QMessageBox.information(self, "Başarılı", "AI ayarları güvenli bir şekilde kaydedildi.")
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Bazı ayarlar kaydedilirken bir sorun oluştu.")

    def update_openai_models(self):
        """Fetch latest models from OpenAI API."""
        api_key = self.openai_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir API anahtarı girin.")
            return
            
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            models = client.models.list()
            model_names = [m.id for m in models.data if any(x in m.id for x in ["gpt", "o1", "o3", "gpt-5"])]
            model_names.sort()
            
            self.openai_model.clear()
            self.openai_model.addItems(model_names)
            QMessageBox.information(self, "Başarılı", f"{len(model_names)} adet model başarıyla güncellendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Modeller alınamadı: {str(e)}")

    def update_gemini_models(self):
        """Fetch latest models from Gemini API."""
        api_key = self.gemini_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir API anahtarı girin.")
            return
            
        try:
            from google import genai
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            models = client.models.list()
            model_names = [m.name for m in models]
            model_names.sort()
            
            self.gemini_model.clear()
            self.gemini_model.addItems(model_names)
            QMessageBox.information(self, "Başarılı", f"{len(model_names)} adet model (v1beta) başarıyla güncellendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Modeller alınamadı: {str(e)}")

    def update_anthropic_models(self):
        """Fetch latest models from Anthropic API."""
        api_key = self.anthropic_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir API anahtarı girin.")
            return
            
        try:
            import requests
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            response = requests.get("https://api.anthropic.com/v1/models", headers=headers)
            if response.status_code == 200:
                models = response.json()["data"]
                model_names = [m["id"] for m in models]
                model_names.sort()
                self.anthropic_model.clear()
                self.anthropic_model.addItems(model_names)
                QMessageBox.information(self, "Başarılı", f"{len(model_names)} adet model başarıyla güncellendi.")
            else:
                QMessageBox.critical(self, "Hata", f"Modeller alınamadı: {response.text}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Modeller alınamadı: {str(e)}")

    def update_kimi_models(self):
        """Fetch latest models from Kimi (Moonshot) API."""
        api_key = self.kimi_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Hata", "Lütfen önce bir API anahtarı girin.")
            return
            
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
            models = client.models.list()
            model_names = [m.id for m in models.data]
            model_names.sort()
            
            self.kimi_model.clear()
            self.kimi_model.addItems(model_names)
            QMessageBox.information(self, "Başarılı", f"{len(model_names)} adet model başarıyla güncellendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Modeller alınamadı: {str(e)}")
