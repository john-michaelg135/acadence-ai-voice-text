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
Keys: "name", "description", "priority", "deadline", "time".
NAME: Must be SHORT — only the task/activity name itself (2-5 words max). Do NOT include descriptions, details, or elaboration in the name.
DESCRIPTION: All details, specifics, and elaboration go here. Rich, actionable, 1-2 sentences. If user provides details after the task name, put them here.
PRIORITY: Must be 'High', 'Medium', or 'Low'. Default to 'Medium'.
DEADLINE: If user mentions a date (like tomorrow, next week), output it as YYYY-MM-DD. If none, omit.
TIME: If user mentions a time (like 5 PM, noon), output it as HH:MM AM/PM (e.g. "05:00 PM"). If none, omit.
NUMBERS: Convert spelled-out numbers.
Title Case the name, keep small words lowercase except at start.

Examples:
- Input: "performance task description is showcase presentation due tomorrow at 5 PM" → {"name": "Performance Task", "description": "Prepare and deliver a showcase presentation.", "priority": "Medium", "time": "05:00 PM"}
- Input: "essay about climate change high priority" → {"name": "Essay", "description": "Write an essay about climate change.", "priority": "High"}
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


# --- AI Attachment Generation ---

def _check_online():
    """Returns True if an internet connection is available."""
    import socket
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=1.5)
        return True
    except OSError:
        return False

def is_research_task(name, description):
    """Detects if a task is research-related based on keywords in name or description."""
    combined = f"{name} {description}".lower()
    research_keywords = [
        "research", "thesis", "dissertation", "literature review", "case study",
        "journal", "references", "bibliography", "citation", "scholarly",
        "academic paper", "study about", "study on", "analysis of", "investigate",
        "survey on", "review of", "systematic review", "meta-analysis",
        "research paper", "term paper", "white paper", "capstone"
    ]
    return any(kw in combined for kw in research_keywords)


def generate_research_references(task_name, description):
    """
    Uses g4f LLM to generate a list of real research references with working URLs.
    Returns the formatted text content for a .txt file, or None if offline/failed.
    Online-only — returns None if no internet connection.
    """
    if not _check_online():
        logger.info("AI attachment generation skipped: offline")
        return None
    
    try:
        import g4f
    except ImportError:
        logger.warning("g4f not installed, cannot generate research references")
        return None
    
    prompt = f"""You are an academic research assistant. Based on the following task and its scope, generate a list of 8-12 REAL, relevant academic references that would help a student research this topic.

Task: {task_name[:200]}
Scope/Description: {description[:500]}

For each reference, provide:
1. Full citation (Author, Title, Year, Publisher/Journal)
2. A working Google Scholar search link formatted EXACTLY like this: https://scholar.google.com/scholar?q=[Title+of+Paper+with+Plus+Signs+Instead+of+Spaces]

Format the output EXACTLY like this:
---
ACADENCE AI — Research References
Topic: [topic summary]
Generated: [current date]
---

1. [Author(s)] — "[Title]" ([Year])
   Source: [Journal/Publisher]
   URL: https://scholar.google.com/scholar?q=[Title+with+plus+signs]

2. [Author(s)] — "[Title]" ([Year])
   Source: [Journal/Publisher]
   URL: https://scholar.google.com/scholar?q=[Title+with+plus+signs]

... (continue for 8-12 references)

---
Note: These references were AI-generated. Click the URLs to search for the papers on Google Scholar.
---

IMPORTANT: Only provide REAL papers and ALWAYS use the exact Google Scholar search URL format for the URL field. Do NOT fabricate paper titles or authors."""
    
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": "You are a helpful academic research assistant. Generate real, verifiable research references with working URLs."},
                {"role": "user", "content": prompt}
            ],
            timeout=30
        )
        
        result = response.strip() if response else None
        if result and len(result) > 100:
            logger.info(f"Research references generated for task: {task_name[:50]}")
            return result
        else:
            logger.warning("AI returned insufficient research references")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to generate research references: {e}")
        return None


def generate_task_tips(task_name, description):
    """
    Uses g4f LLM to generate tips, guides, and strategies for completing a task.
    Never provides direct answers — only guidance and methodology.
    Returns the formatted text content for a .txt file, or None if offline/failed.
    Online-only — returns None if no internet connection.
    """
    if not _check_online():
        logger.info("AI attachment generation skipped: offline")
        return None
    
    try:
        import g4f
    except ImportError:
        logger.warning("g4f not installed, cannot generate task tips")
        return None
    
    prompt = f"""You are an academic advisor helping a student complete a task. Based on the following task, generate helpful tips, strategies, and guidance.

Task: {task_name[:200]}
Description: {description[:500]}

IMPORTANT RULES:
- NEVER provide direct answers, solutions, or completed work
- ONLY provide tips, strategies, methodology, and guidance
- Suggest approaches, tools, and frameworks the student can use
- Recommend time management strategies specific to this task type
- Include helpful online resources and tools (with URLs when possible)

Format the output EXACTLY like this:
---
ACADENCE AI — Task Guide
Task: [task name]
Generated: [current date]
---

📋 OVERVIEW
[Brief overview of what this task involves and key objectives]

💡 TIPS & STRATEGIES
1. [Tip 1]
2. [Tip 2]
3. [Tip 3]
... (provide 5-8 actionable tips)

🛠️ RECOMMENDED TOOLS & RESOURCES
- [Tool/Resource 1] — [URL if applicable]
- [Tool/Resource 2] — [URL if applicable]
... (provide 3-5 resources)

⏰ TIME MANAGEMENT
[Suggest how to break down and schedule this task]

⚠️ COMMON MISTAKES TO AVOID
1. [Mistake 1]
2. [Mistake 2]
3. [Mistake 3]

---
Note: This guide was AI-generated. Use it as a starting point for your own work.
---"""
    
    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.default,
            messages=[
                {"role": "system", "content": "You are a helpful academic advisor. Provide tips and guidance only — never direct answers or completed work."},
                {"role": "user", "content": prompt}
            ],
            timeout=30
        )
        
        result = response.strip() if response else None
        if result and len(result) > 100:
            logger.info(f"Task tips generated for task: {task_name[:50]}")
            return result
        else:
            logger.warning("AI returned insufficient task tips")
            return None
            
    except Exception as e:
        logger.warning(f"Failed to generate task tips: {e}")
        return None
