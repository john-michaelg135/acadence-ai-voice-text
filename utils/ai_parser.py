import json
import re
from utils.logger import logger

def parse_voice_command(text, command_type='subject'):
    """
    Safely parses natural language voice transcripts into structured dictionary data.
    Uses g4f (GPT4Free) LLM if online, falls back to rule-based parsing offline.
    
    Prevents prompt injection by sanitizing user input before LLM call.
    """
    if not text or len(text) > 500:
        logger.warning(f"Invalid input length: {len(text) if text else 0}")
        return fallback_parse(text or "", command_type)
    
    # Sanitize user input: detect and reject potential prompt injection attempts
    dangerous_patterns = [
        r'ignore.*(?:previous|before|all).*instruction',
        r'forget.*(?:everything|all).*before',
        r'(?:system|hidden|secret).*prompt',
        r'jailbreak',
        r'bypass',
        r'override',
        r'execute.*code',
        r'sql.*injection',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Potential prompt injection detected in text: {text[:50]}")
            return fallback_parse(text, command_type)
    
    try:
        import g4f
    except ImportError:
        logger.debug("g4f not installed, using fallback parsing")
        return fallback_parse(text, command_type)

    # Build safe prompt using templates instead of f-string injection
    if command_type == 'subject':
        system_prompt = """Extract subject information from user text and return ONLY a valid JSON object.
Keys: "name", "code", "description".
NAME: Title Case, keep small words (to, from, and, of, the) lowercase except at start.
NUMBERS: Convert spelled-out numbers ('one' → '1', 'forty five' → '45').
DESCRIPTION: Rich, professional, 1-2 sentences. If missing, invent based on name.
CODE: Format as UPPERCASE-DIGITS (e.g. 'CS-101'). If missing, guess reasonable value.
Return ONLY valid JSON."""
        user_text_template = "Extract: [TEXT_HERE]"
    else:
        system_prompt = """Extract task information from user text and return ONLY a valid JSON object.
Keys: "name", "description", "priority".
NAME: Must be SHORT — only the task/activity name itself (2-5 words max). Do NOT include descriptions, details, or elaboration in the name.
DESCRIPTION: All details, specifics, and elaboration go here. Rich, actionable, 1-2 sentences. If user provides details after the task name, put them here.
PRIORITY: Must be 'High', 'Medium', or 'Low'. Default to 'Medium'.
NUMBERS: Convert spelled-out numbers.
Title Case the name, keep small words lowercase except at start.

Examples:
- Input: "performance task description is showcase presentation" → {"name": "Performance Task", "description": "Prepare and deliver a showcase presentation.", "priority": "Medium"}
- Input: "essay about climate change high priority" → {"name": "Essay", "description": "Write an essay about climate change.", "priority": "High"}
- Input: "study chapter 5 math" → {"name": "Study Chapter 5", "description": "Review and study Chapter 5 of the math textbook.", "priority": "Medium"}
Return ONLY valid JSON."""
        user_text_template = "Extract: [TEXT_HERE]"
    
    # Safely combine user text into template
    user_message = user_text_template.replace("[TEXT_HERE]", text[:300])  # Limit text length

    import socket
    def is_online():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            return True
        except OSError:
            return False

    if is_online():
        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                timeout=10
            )
            
            # Clean up possible markdown formatting like ```json ... ```
            response_text = response.strip() if response else ""
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Validate JSON structure before returning
            data = json.loads(response_text)
            
            # Validate required keys
            if command_type == 'subject':
                required = {'name', 'code', 'description'}
            else:
                required = {'name', 'description', 'priority'}
            
            if not all(k in data for k in required):
                logger.warning(f"Invalid response structure missing keys: {required - set(data.keys())}")
                return fallback_parse(text, command_type)
            
            logger.debug(f"AI parsing successful for {command_type}")
            return data
            
        except json.JSONDecodeError as e:
            logger.warning(f"AI response JSON parsing failed: {e}")
            return fallback_parse(text, command_type)
        except Exception as e:
            logger.warning(f"AI Parsing failed: {e}")
            return fallback_parse(text, command_type)
    else:
        # Instantly run fallback if offline to prevent g4f version checks and timeouts
        logger.debug("Offline - using fallback parsing")
        return fallback_parse(text, command_type)

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

def enrich_subject_offline(name, current_desc):
    """Provides a pseudo-AI enriched academic description based on keywords."""
    if len(current_desc) > 20 and current_desc.lower() not in name.lower() and name.lower() not in current_desc.lower():
        return current_desc.capitalize()
        
    name_lower = name.lower()
    if "database" in name_lower or "data" in name_lower:
        return f"An in-depth exploration of {name.lower()}, covering core principles, architecture, and practical applications."
    elif "math" in name_lower or "calculus" in name_lower or "algebra" in name_lower:
        return f"A comprehensive study of {name.lower()}, focusing on analytical problem solving and theoretical frameworks."
    elif "program" in name_lower or "comput" in name_lower or "software" in name_lower or "web" in name_lower:
        return f"An essential study covering fundamental {name.lower()} concepts, logic design, and modern development practices."
    elif "art" in name_lower or "design" in name_lower or "draw" in name_lower:
        return f"A creative exploration of {name.lower()}, emphasizing aesthetics, principles of design, and visual expression."
    elif "history" in name_lower or "social" in name_lower or "politic" in name_lower:
        return f"An analytical review of {name.lower()}, evaluating historical contexts, societal impacts, and key theories."
    elif "science" in name_lower or "physic" in name_lower or "biolog" in name_lower or "chemist" in name_lower:
        return f"A rigorous scientific investigation into {name.lower()}, featuring theoretical study and practical methodology."
    elif "business" in name_lower or "manage" in name_lower or "market" in name_lower:
        return f"A strategic overview of {name.lower()}, focusing on industry practices, organizational behavior, and economic trends."
    else:
        return f"A structured academic course covering the fundamental concepts, theories, and practical applications of {name.lower()}."

def enrich_task_offline(name, current_desc):
    """Provides a pseudo-AI enriched task description based on keywords."""
    if len(current_desc) > 15 and current_desc.lower() not in name.lower() and name.lower() not in current_desc.lower():
        return current_desc.capitalize()
        
    name_lower = name.lower()
    if "read" in name_lower or "study" in name_lower or "review" in name_lower:
        return f"Thoroughly review and study the provided materials for {name.lower()} to ensure complete understanding."
    elif "write" in name_lower or "essay" in name_lower or "paper" in name_lower:
        return f"Draft, refine, and finalize the written requirements for {name.lower()}, ensuring proper formatting and clarity."
    elif "code" in name_lower or "program" in name_lower or "build" in name_lower:
        return f"Implement the necessary code and test the functionality for {name.lower()} to meet project requirements."
    elif "project" in name_lower or "presentation" in name_lower:
        return f"Organize, prepare, and deliver the final deliverables for the {name.lower()}."
    else:
        return f"Complete all necessary steps and requirements to successfully finalize the {name.lower()}."

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
            'description': enrich_subject_offline(name, desc)
        }
    else:
        # Task Parsing
        name = ""
        desc = text
        priority = "Medium"
        
        # Try to extract name: capture text before any description/detail keywords
        name_match = re.search(r'(task is|task called|called)\s+([^,]+)', text, re.IGNORECASE)
        if name_match:
            raw_name = name_match.group(2).strip()
        else:
            raw_name = text
        
        # Split name from description at keywords like "description is", "about", etc.
        # This prevents description content from leaking into the task name.
        desc_split = re.split(r'\s+(?:description is|described as|details are|about)\s+', raw_name, maxsplit=1, flags=re.IGNORECASE)
        if len(desc_split) > 1:
            name = desc_split[0].strip()
            desc = desc_split[1].strip()
        else:
            # No explicit description keyword found — use first few words as name
            words = raw_name.split()
            name = " ".join(words[:4])  # Max 4 words for the name
            if len(words) > 4:
                desc = " ".join(words[4:])
            else:
                desc = raw_name
        
        # Also check for description after the full text for cases not caught above
        desc_match = re.search(r'(?:description is|described as|details are)\s+(.+)', text, re.IGNORECASE)
        if desc_match:
            desc = desc_match.group(1).strip()
        
        if "high priority" in text.lower() or "urgent" in text.lower():
            priority = "High"
        elif "low priority" in text.lower():
            priority = "Low"
            
        # Clean priority keywords from name
        name = re.sub(r'\s*(high|low|medium)\s+priority\s*', '', name, flags=re.IGNORECASE).strip()
        name = re.sub(r'\s*urgent\s*', '', name, flags=re.IGNORECASE).strip()
            
        return {
            'name': to_title_case(name) if name else to_title_case(" ".join(text.split()[:3])),
            'description': enrich_task_offline(name, desc),
            'priority': priority
        }
