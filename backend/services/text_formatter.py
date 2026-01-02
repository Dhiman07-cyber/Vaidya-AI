"""
Text Formatter Service
Cleans and formats AI-generated text for display
"""
import re


def clean_markdown(text: str) -> str:
    """
    Remove markdown formatting from text for clean display
    
    Args:
        text: Text with markdown formatting
        
    Returns:
        Clean text without markdown symbols
    """
    if not text:
        return text
    
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove headers (# ## ### etc)
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove inline code (`code`)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Remove code blocks (```code```)
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove links [text](url)
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    # Remove images ![alt](url)
    text = re.sub(r'!\[.+?\]\(.+?\)', '', text)
    
    # Remove horizontal rules (--- or ***)
    text = re.sub(r'^[\-\*]{3,}$', '', text, flags=re.MULTILINE)
    
    # Remove blockquotes (> text)
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def format_for_display(text: str, preserve_structure: bool = True) -> str:
    """
    Format text for display with optional structure preservation
    
    Args:
        text: Raw text from AI
        preserve_structure: If True, keep line breaks and basic structure
        
    Returns:
        Formatted text ready for display
    """
    if not text:
        return text
    
    if preserve_structure:
        # Keep structure but clean markdown
        return clean_markdown(text)
    else:
        # Remove all formatting and collapse to single paragraph
        cleaned = clean_markdown(text)
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()
