from typing import Optional

def build_full_name(first: str, last: str, middle: Optional[str] = None) -> str:
    """Compose a display name from split name parts."""
    if middle:
        return f"{first} {middle[0].upper()}. {last}"
    return f"{first} {last}"
