import json
import logging
from core.ai_handler import AIHandler

class StructuringHandler:
    """Handles extraction of structured information like Mind Maps and Knowledge Graphs."""
    
    def __init__(self, ai_handler: AIHandler):
        self.ai_handler = ai_handler

    def generate_mind_map_data(self, text):
        """
        Extracts a hierarchical mind map structure from text.
        Returns a JSON-compatible dictionary.
        """
        system_prompt = (
            "Sen bir bilgi yapılandırma uzmanısın. Verilen metinden hiyerarşik bir zihin haritası çıkar. "
            "Çıktıyı SADECE şu JSON formatında ver: "
            '{"title": "Ana Başlık", "children": [{"title": "Alt Başlık 1", "children": [...]}, ...]}'
        )
        
        prompt = f"Lütfen şu metni bir zihin haritasına dönüştür:\n\n{text}"
        
        # We use a blocking call here or we can use signals. 
        # For simplicity in infrastructure, let's assume ai_handler has a direct call.
        response = self.ai_handler.generate_response(prompt, system_prompt=system_prompt, use_context=False)
        
        return self._parse_json_response(response)

    def generate_knowledge_graph(self, text):
        """
        Extracts entities and relationships for a knowledge graph.
        Returns a dictionary with 'nodes' and 'edges'.
        """
        system_prompt = (
            "Sen bir veri bilimcisin. Metindeki varlıkları (entities) ve aralarındaki ilişkileri (relationships) çıkar. "
            "Çıktıyı SADECE şu JSON formatında ver: "
            '{"nodes": [{"id": "1", "label": "Varlık Adı", "type": "Kişi/Kurum/vb"}, ...], '
            '"edges": [{"from": "1", "to": "2", "label": "ilişki tipi"}, ...]}'
        )
        
        prompt = f"Lütfen şu metni bir bilgi grafına (knowledge graph) dönüştür:\n\n{text}"
        
        response = self.ai_handler.generate_response(prompt, system_prompt=system_prompt, use_context=False)
        
        return self._parse_json_response(response)

    def generate_timeline_data(self, text):
        """
        Extracts chronological events from text for a timeline view.
        Returns a JSON list of events.
        """
        system_prompt = (
            "Sen bir kronoloji uzmanısın. Metindeki önemli olayları tarih sırasına göre çıkar. "
            "Çıktıyı SADECE şu JSON formatında ver: "
            '[{"date": "YYYY-MM-DD", "event": "Olay açıklaması", "importance": "high/medium/low"}, ...]'
        )
        
        prompt = f"Lütfen şu metindeki olayların zaman çizelgesini çıkar:\n\n{text}"
        
        response = self.ai_handler.generate_response(prompt, system_prompt=system_prompt, use_context=False)
        
        return self._parse_json_response(response)

    def _parse_json_response(self, response):
        """Helper to safely parse JSON from LLM response."""
        if not response:
            return None
            
        try:
            # LLM might wrap JSON in markdown blocks
            clean_json = response.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3].strip()
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3].strip()
                
            return json.loads(clean_json)
        except Exception as e:
            logging.error(f"JSON parsing error: {e}")
            return {"error": "JSON formatına dönüştürülemedi", "raw": response}
