from datetime import datetime
from pathlib import Path
from typing import Union

from lxml.html import fromstring, tostring

from constants import SITE_ADDRESS
from utils import wrap_unwrap_fake_tag


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


def update_classes(html: str, selector: str , classes: str) -> str:
    doc = fromstring(wrap_unwrap_fake_tag(html))
    classes = classes.split(' ')
    for t in doc.cssselect(selector):
        t.classes.update(classes)

    html = tostring(doc, encoding='unicode')
    html = wrap_unwrap_fake_tag(html, wrap=False)
    return html


def replace_thumbnail_link(relative_link: Path):
    return relative_link.as_posix().replace('files/', 'thumbnails/')