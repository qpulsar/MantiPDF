import logging
from core.ai_handler import AIHandler

class FormHandler:
    """Handles PDF form field detection and AI-powered auto-filling suggestions."""
    
    def __init__(self, ai_handler: AIHandler):
        self.ai_handler = ai_handler

    def detect_form_fields(self, fitz_doc):
        """Identifies interactive form fields in the PDF."""
        fields = []
        for page_num, page in enumerate(fitz_doc):
            for widget in page.widgets():
                fields.append({
                    "page": page_num,
                    "name": widget.field_name,
                    "type": widget.field_type_string,
                    "value": widget.field_value,
                    "rect": [widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1]
                })
        return fields

    def suggest_form_values(self, fields, context_text=""):
        """Uses AI to suggest values for the detected form fields."""
        if not fields:
            return {}
            
        field_names = [f["name"] for f in fields]
        system_prompt = (
            "Sen bir form doldurma asistanısın. Verilen form alanları için en uygun değerleri öner. "
            "Eğer metin bağlamı (context) verilmişse, oradaki bilgileri kullan. "
            "Çıktıyı SADECE şu JSON formatında ver: "
            '{"alan_adi": "oneri_degeri", ...}'
        )
        
        prompt = f"Şu form alanları için önerilerde bulun: {', '.join(field_names)}\n\nBAĞLAM:\n{context_text}"
        
        response = self.ai_handler.generate_response(prompt, system_prompt=system_prompt, use_context=False)
        
        try:
            import json
            clean_json = response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3].strip()
            return json.loads(clean_json)
        except:
            return {}

    def fill_form(self, fitz_doc, data):
        """Fills the PDF form fields with the provided data dictionary."""
        for page in fitz_doc:
            for widget in page.widgets():
                if widget.field_name in data:
                    widget.field_value = str(data[widget.field_name])
                    widget.update()
        return True
