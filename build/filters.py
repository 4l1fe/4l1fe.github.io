from datetime import datetime
from pathlib import Path
from typing import Union

from constants import SITE_ADDRESS


def trailing_slash(link: Union[Path, str]) -> str:
    if isinstance(link, Path):
        link = link.as_posix()
    return link + '/'


def to_rfc822(dt: datetime) -> str:
    return dt.strftime('%d %b %Y 00:00:00 +0000').lstrip('0')


def prepend_site_address(link: Union[Path, str]) -> str:
    if isinstance(link ,Path):
        link = link.as_posix()
    link = link.lstrip('/')
    return SITE_ADDRESS + '/' + link