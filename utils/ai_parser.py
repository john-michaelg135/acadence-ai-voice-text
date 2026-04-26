import json

def parse_voice_command(text, command_type='subject'):
    """
    Uses a free LLM provider via g4f (GPT4Free) to intelligently parse natural language 
    voice transcripts into structured dictionary data.
    
    Make sure you have g4f installed: pip install -U g4f
    """
    try:
        import g4f
    except ImportError:
        print("g4f is not installed. Falling back to basic parsing.")
        return fallback_parse(text, command_type)

    prompt = ""
    if command_type == 'subject':
        prompt = f"""
        Extract the following information from this text: "{text}"
        Return ONLY a valid JSON object with the keys "name", "code", and "description".
        If a piece of info is missing, guess a reasonable value or leave it empty. 
        Example format: {{"name": "Mathematics", "code": "MATH101", "description": "Study of numbers"}}
        """
    else:
        prompt = f"""
        Extract the following information from this text: "{text}"
        Return ONLY a valid JSON object with the keys "name", "description", and "priority".
        Priority must be "High", "Medium", or "Low". If not mentioned, use "Medium".
        Example format: {{"name": "Complete Essay", "description": "Write 500 words on history", "priority": "High"}}
        """

    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[{"role": "user", "content": prompt}],
            timeout=10
        )
        
        # Clean up possible markdown formatting like ```json ... ```
        response_text = response.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        data = json.loads(response_text.strip())
        return data
    except Exception as e:
        print(f"AI Parsing failed: {e}")
        return fallback_parse(text, command_type)

import re

def fallback_parse(text, command_type):
    """Smart rule-based fallback if g4f fails or isn't installed."""
    if command_type == 'subject':
        name = " ".join(text.split()[:3])
        code = ""
        desc = text
        
        # Extract name
        name_match = re.search(r'(called|named|subject is)\s+([^,]+)', text, re.IGNORECASE)
        if name_match:
            name = name_match.group(2).strip()
            
        # Extract code
        code_match = re.search(r'(code is|subject code is|code)\s+([a-zA-Z0-9\s]+)', text, re.IGNORECASE)
        if code_match:
            # e.g., "cs 101" -> "CS101"
            raw_code = code_match.group(2).split("and")[0].strip()
            code = raw_code.replace(" ", "").upper()[:8]
        
        # Extract description
        desc_match = re.search(r'(covers|about|description is)\s+(.+)', text, re.IGNORECASE)
        if desc_match:
            desc = desc_match.group(2).strip()
            
        return {
            'name': name,
            'code': code,
            'description': desc
        }
    else:
        # Task Parsing
        name = " ".join(text.split()[:3])
        desc = text
        priority = "Medium"
        
        name_match = re.search(r'(task is|task called|called)\s+([^,]+)', text, re.IGNORECASE)
        if name_match:
            name = name_match.group(2).strip()
            
        desc_match = re.search(r'(description is|about|to)\s+(.+)', text, re.IGNORECASE)
        if desc_match:
            desc = desc_match.group(2).strip()
            
        if "high priority" in text.lower() or "urgent" in text.lower():
            priority = "High"
        elif "low priority" in text.lower():
            priority = "Low"
            
        return {
            'name': name,
            'description': desc,
            'priority': priority
        }
