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
        CRITICAL INSTRUCTION FOR NAME: The 'name' must be in Title Case, but keep short conjunctions/prepositions (to, from, and, of, the) lowercase unless they are the first word.
        CRITICAL INSTRUCTION FOR NUMBERS: You MUST aggressively convert ANY spelled-out numbers (e.g. 'one', 'two', 'forty five') into numerical digits ('1', '2', '45') in ALL fields.
        CRITICAL INSTRUCTION FOR DESCRIPTION: You must ALWAYS expand the description to make it rich and professional, BUT KEEP IT CONCISE (maximum 1-2 sentences). 
        If the user did not provide a description in the text, you MUST invent a high-quality academic description based on the subject name.
        CRITICAL INSTRUCTION FOR CODE: The 'code' MUST ALWAYS be formatted with uppercase letters followed by a hyphen (-) and then digits (e.g., 'CS-101', 'DA-001'). 
        If the user says things like "D A zero zero one", "DA double O one", or "D A o o 1", you MUST intelligently parse it as "DA-001".
        If a code is missing, guess a reasonable uppercase value with a hyphen.
        Example format: {{"name": "Introduction to Mathematics 1", "code": "MATH-101", "description": "An advanced exploration of mathematical concepts focusing on calculus and real-world applications."}}
        """
    else:
        prompt = f"""
        Extract the following information from this text: "{text}"
        Return ONLY a valid JSON object with the keys "name", "description", and "priority".
        Priority must be "High", "Medium", or "Low". If not mentioned, use "Medium".
        CRITICAL INSTRUCTION FOR NAME: The 'name' must be in Title Case, but keep short conjunctions/prepositions (to, from, and, of, the) lowercase unless they are the first word.
        CRITICAL INSTRUCTION FOR NUMBERS: You MUST aggressively convert ANY spelled-out numbers (e.g. 'one', 'two', 'forty five') into numerical digits ('1', '2', '45') in ALL fields.
        CRITICAL INSTRUCTION FOR DESCRIPTION: You must ALWAYS expand the description to make it rich and actionable, BUT KEEP IT CONCISE (maximum 1-2 sentences).
        If the user did not provide a description, you MUST invent a helpful and descriptive one based on the task name.
        Example format: {{"name": "Complete Essay 2", "description": "Research and write a 500-word essay on modern history, ensuring proper citations.", "priority": "High"}}
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

def to_title_case(s):
    exceptions = ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in']
    words = s.split()
    if not words: return ""
    result = [words[0].capitalize()]
    for w in words[1:]:
        result.append(w.lower() if w.lower() in exceptions else w.capitalize())
    return " ".join(result)

def convert_numbers(s):
    words = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14", "fifteen": "15",
        "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19",
        "twenty": "20", "thirty": "30", "forty": "40", "fifty": "50", "sixty": "60",
        "double o": "00", "double zero": "00", "triple o": "000"
    }
    for word, digit in words.items():
        s = re.sub(r'\b' + word + r'\b', digit, s, flags=re.IGNORECASE)
    return s

def fallback_parse(text, command_type):
    """Smart rule-based fallback if g4f fails or isn't installed."""
    text = convert_numbers(text)
    
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
            # e.g., "cs 101" -> "CS-101"
            raw_code = code_match.group(2).split("and")[0].strip()
            code = raw_code.replace(" ", "").upper()
            code = re.sub(r'([A-Z]+)(\d+)', r'\1-\2', code)[:10]
        
        # Extract description
        desc_match = re.search(r'(covers|about|description is)\s+(.+)', text, re.IGNORECASE)
        if desc_match:
            desc = desc_match.group(2).strip()
            
        return {
            'name': to_title_case(name),
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
            'name': to_title_case(name),
            'description': desc,
            'priority': priority
        }
