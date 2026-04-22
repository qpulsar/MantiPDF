from core.security_manager import SecurityManager
from core.pdf_indexer import PDFIndexer
from PyQt6.QtCore import QObject, pyqtSignal, QSettings

class AIHandler(QObject):
    """Central handler for AI requests and provider management."""
    
    # Signals for async communication
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int, str)

    def __init__(self):
        super().__init__()
        self.settings = QSettings("MantiPDF", "AI")
        self.current_provider = self.settings.value("provider", "openai")
        self.indexer = PDFIndexer()
        self.indexed_doc_path = None

    def set_provider(self, provider):
        """Sets the active AI provider."""
        self.current_provider = provider
        self.settings.setValue("provider", provider)

    def get_active_model(self):
        """Returns the configured model for the current provider."""
        return self.settings.value(f"{self.current_provider}_model")

    def prepare_pdf_context(self, fitz_doc, filepath):
        """Indexes the PDF if it's not already indexed."""
        if self.indexed_doc_path == filepath:
            return True
        
        self.progress_updated.emit(0, "Belge dizinleniyor...")
        if self.indexer.index_document(fitz_doc):
            self.indexed_doc_path = filepath
            self.progress_updated.emit(100, "Dizinleme tamamlandı.")
            return True
        return False

    def generate_response(self, prompt, system_prompt="Sen yardımcı bir PDF asistanısın.", stream=False, use_context=True):
        """
        Main entry point for generating AI responses with retry and fallback logic.
        """
        # Get list of potential providers
        all_providers = ["openai", "anthropic", "gemini", "kimi", "local"]
        
        # Reorder to start with current preferred provider
        providers_to_try = [self.current_provider] + [p for p in all_providers if p != self.current_provider]
        
        # Add context if requested
        if use_context and self.indexed_doc_path:
            relevant_docs = self.indexer.similarity_search(prompt)
            context_text = "\n---\n".join([d.page_content for d in relevant_docs])
            system_prompt += f"\n\nPDF BAĞLAMI:\n{context_text}\n\nLütfen SADECE yukarıdaki bağlama dayanarak cevap ver. Eğer cevap bağlamda yoksa, bunu belirt."

        last_error = None
        for provider in providers_to_try:
            api_key = SecurityManager.get_api_key(provider)
            if not api_key and provider != "local":
                continue
                
            self.progress_updated.emit(50, f"{provider.capitalize()} üzerinden yanıt oluşturuluyor...")
            
            # Try the provider (with up to 2 internal retries for transient errors)
            for attempt in range(2):
                try:
                    result = None
                    if provider == "openai":
                        result = self._call_openai(prompt, system_prompt, api_key, stream)
                    elif provider == "anthropic":
                        result = self._call_anthropic(prompt, system_prompt, api_key, stream)
                    elif provider == "gemini":
                        result = self._call_gemini(prompt, system_prompt, api_key, stream)
                    elif provider == "kimi":
                        result = self._call_kimi(prompt, system_prompt, api_key, stream)
                    elif provider == "local":
                        result = self._call_local(prompt, system_prompt, stream)
                    
                    if result:
                        self.response_received.emit(result)
                        return result
                        
                except Exception as e:
                    last_error = str(e)
                    # If it's a 503 or 429, wait and retry
                    if "503" in last_error or "429" in last_error:
                        import time
                        time.sleep(1) # Small delay before retry
                        continue
                    else:
                        break # Other errors: try next provider
            
            # If we reach here, this provider failed.
            import logging
            logging.getLogger("ai_handler").warning(f"Provider {provider} failed: {last_error}. Trying next available provider...")

        # If all providers failed
        error_msg = f"Tüm AI sağlayıcıları başarısız oldu. Son hata: {last_error}"
        self.error_occurred.emit(error_msg)
        return None

    def _call_openai(self, prompt, system_prompt, api_key, stream):
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = self.get_active_model() or "gpt-5.4"
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=stream
        )
        
        if stream:
            # Handle streaming logic
            return None
        else:
            return response.choices[0].message.content

    def _call_anthropic(self, prompt, system_prompt, api_key, stream):
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        model = self.get_active_model() or "claude-sonnet-4.6"
        
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text

    def _call_gemini(self, prompt, system_prompt, api_key, stream):
        from google import genai
        client = genai.Client(api_key=api_key)
        model_id = self.get_active_model() or "gemini-3.1-flash"
        
        full_prompt = f"{system_prompt}\n\nKullanıcı İstemi: {prompt}"
        # This will raise exception on 503/429 for the caller to handle
        response = client.models.generate_content(model=model_id, contents=full_prompt)
        return response.text

    def _call_kimi(self, prompt, system_prompt, api_key, stream):
        """Kimi (Moonshot) is OpenAI-compatible."""
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1")
        model = self.get_active_model() or "kimi-k2.6"
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=stream
        )
        return response.choices[0].message.content

    def _call_local(self, prompt, system_prompt, stream):
        # Placeholder for Ollama integration
        url = self.settings.value("local_url", "http://localhost:11434")
        self.error_occurred.emit("Yerel model entegrasyonu henüz tamamlanmadı.")
        return None
