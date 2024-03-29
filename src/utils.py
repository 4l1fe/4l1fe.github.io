import unicodedata
import re
from itertools import islice
from functools import lru_cache
from pathlib import Path
from datetime import datetime

import markdown_it


def make_header_id(tag_text):
    return tag_text.lower().replace(' ', '-')


def wrap_unwrap_fake_tag(text, wrap=True): # todo use lxml.html
    """To avoid side effect of automatic wrapping with extra tags"""

    TAG_OPEN = '<FAKETAG>'
    TAG_CLOSE = '</FAKETAG>'

    if wrap:
        text = TAG_OPEN + text + TAG_CLOSE
    else:
        text = text[len(TAG_OPEN):][:-len(TAG_CLOSE)]
    return text


def slugify(title):
    value = str(title)
    value = unicodedata.normalize('NFKC', value)
    value = re.sub(r'[^\w\s-]', '', value.lower())
    value = re.sub(r'[-\s]+', '-', value).strip('-_') 
    return value


@lru_cache
def first_h1_text(element):
    return element.find('.//h1').text


@lru_cache
def first_p_text(element):
    """0th element has to be an article image"""
    return list(islice(element.iterfind('.//p'), 2))[1].text_content()


def replace_relative_with_dots(path: Path, dots_to) -> Path:
    parts = path.relative_to(dots_to).parts
    dot_path = Path('')
    self = parts[-1]
    
    for part in parts:
        if part != self:
            dot_path = dot_path.joinpath('..')
        else:
            dot_path = dot_path.joinpath(part)

    return dot_path


@lru_cache
def parser_render(md_file: Path) -> str:
    parser = markdown_it.MarkdownIt().enable('table')
    md_text = Path(md_file).read_text()
    html = parser.render(md_text)
    return html


@lru_cache
def extract_path_date(dir_name: str) -> datetime:
    created_date = datetime.strptime(dir_name, '%Y-%m-%d')
    return created_date
