import re

# A basic list of explicit/inappropriate words to block.
# Expand this list as necessary.
BANNED_WORDS = [
    r"nigg[e|a|e]rs?",
    r"sexx?",
    r"porn",
    r"ass(hole|hat)?s?",
    r"tits?",
    r"fuck",
    r"shit",
    r"bitch",
    r"cunt",
    r"dick",
    r"pussy",
    r"whore",
    r"slut",
    r"fag(got)?s?",
    r"kill\s+yourself",
    r"kys",
    r"rape"
]

# Compile a single regex that checks for word boundaries (\b) 
# around any of the banned words to prevent false positives (e.g. "assassin" or "class")
_PROFANITY_REGEX = re.compile(
    r'\b(' + '|'.join(BANNED_WORDS) + r')\b',
    re.IGNORECASE
)

def contains_profanity(text: str) -> bool:
    """
    Returns True if the text contains any word from the banned list.
    """
    if not text:
        return False
    return bool(_PROFANITY_REGEX.search(text))
