import json
import logging
from core.ai_handler import AIHandler

class ProfessionalHandler:
    """Handles business and professional AI tasks like contract analysis and data extraction."""
    
    def __init__(self, ai_handler: AIHandler):
        self.ai_handler = ai_handler

    def analyze_contract(self, text):
        """Analyzes a contract for risks and critical obligations."""
        system_prompt = (
            "Sen uzman bir hukuk danışmanısın. Verilen sözleşme metnini analiz et. "
            "Riskli maddeleri, kritik yükümlülükleri ve dikkat edilmesi gereken noktaları çıkar. "
            "Yanıtını Markdown formatında, başlıklar ve maddeler kullanarak ver."
        )
        
        prompt = f"Lütfen aşağıdaki sözleşmeyi analiz et:\n\n{text}"
        
        return self.ai_handler.generate_response(prompt, system_prompt=system_prompt, use_context=False)

    def extract_invoice_data(self, text):
        """Extracts structured data from an invoice or financial document."""
        system_prompt = (
            "Sen bir finansal veri çıkarma uzmanısın. Belgedeki fatura numarası, tarih, "
            "toplam tutar, vergi miktarı ve kalem listesini çıkar. "
            "Çıktıyı SADECE şu JSON formatında ver: "
            '{"invoice_no": "...", "date": "...", "total": "...", "items": [{"desc": "...", "amount": "..."}]}'
        )
        
        prompt = f"Lütfen şu belgeden fatura verilerini çıkar:\n\n{text}"
        
        response = self.ai_handler.generate_response(prompt, system_prompt=system_prompt, use_context=False)
        return response # Raw JSON response from LLM
