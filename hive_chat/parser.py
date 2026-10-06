import json
import re
from typing import Dict, Optional

class FallbackParser:
    def __init__(self):
        self.vocabulary = {
            "fire extinguisher": ["fire extinguisher", "aag bujhane", "aag bujhane wala", "fire"],
            "toolbox": ["toolbox", "tools", "auzaar"],
            "pallet": ["pallet", "wooden pallet"],
            "first_aid_kit": ["first aid", "medical", "doctor", "first_aid_kit", "first aid kit"],
            "gas_cylinder": ["gas", "cylinder", "gas_cylinder"],
        }
        
    def parse(self, user_input: str) -> Dict:
        user_input = user_input.lower()
        
        # Determine intent
        action = "find"
        if "where" in user_input or "kahan" in user_input or "kidhar" in user_input or "last seen" in user_input:
            action = "last_seen"
        elif "verify" in user_input or "check" in user_input or "dekho" in user_input:
            action = "verify"
            
        # Match label
        matched_label = None
        for label, synonyms in self.vocabulary.items():
            for syn in synonyms:
                if syn in user_input:
                    matched_label = label
                    break
            if matched_label:
                break
                
        if not matched_label:
            return {"error": "Could not understand the object name."}
            
        return {
            "action": action,
            "label": matched_label,
            "mode": "nearest"
        }
