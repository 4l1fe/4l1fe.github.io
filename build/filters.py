from datetime import datetime
from pathlib import Path


def trailing_slash(link: Path) -> str:
    return link.as_posix() + '/'


def to_rfc822(dt: datetime) -> str:
    return dt.strftime('%d %b %Y 00:00:00 +0000').lstrip('0')