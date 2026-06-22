import re
import bs4
from markdownify import markdownify

def html_to_markdown(html: str) -> str:
    """Convert an HTML string to Markdown, stripping out nav and ad components."""
    soup = bs4.BeautifulSoup(html, "html.parser")
    
    ignore_tags = {"nav", "aside", "script", "style", "noscript", "iframe", "form"}
    ignore_keywords = {"nav", "navigation", "ad", "ads", "advertisement", "promo", "sidebar", "menu"}
    
    for element in soup.find_all(True):
        if element.name in ignore_tags:
            element.decompose()
            continue
            
        classes = element.get("class", [])
        if isinstance(classes, str):
            classes = [classes]
        
        parsed_classes = []
        for c in classes:
            parsed_classes.extend(c.lower().replace("-", " ").replace("_", " ").split())

        element_id = element.get("id", "")
        if isinstance(element_id, list):
            element_id = " ".join(element_id)
        parsed_ids = element_id.lower().replace("-", " ").replace("_", " ").split()

        if any(w in ignore_keywords for w in parsed_classes + parsed_ids):
            element.decompose()

    raw = markdownify(str(soup), heading_style="ATX")
    
    # Collapse excessive blank lines
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    
    return raw.strip() + "\n"
