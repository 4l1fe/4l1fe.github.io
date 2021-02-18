import commonmark

from typing import List, Tuple
from xml.dom.minidom import getDOMImplementation
from string import Template
from pathlib import Path
from lxml.etree import Element, tostring
from lxml.html import fromstring


BUILD_DIR = Path(__file__).parent
DOCS_DIR = BUILD_DIR.parent / 'docs'
ARTICLES_DIR = BUILD_DIR.parent / 'articles'
BLOG_INDEX_FILE = DOCS_DIR / 'index.html'
ARTICLE_TEMPLATE_FILE = BUILD_DIR / 'article-base.html'
INDEX_TEMPLATE_FILE = BUILD_DIR / 'index-base.html'
ARTICLE_TEXT_FILE = 'README.md'
ARTICLE_IMG_FILE = 'files/main-section.png'
HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TocType = List[Tuple[int, str]]


def _make_header_id(tag_text):
    return tag_text.lower().replace(' ', '-')


def _wrap_unwrap_fake_tag(text, wrap=True):
    TAG_OPEN = '<FAKETAG>'
    TAG_CLOSE = '</FAKETAG>'

    if wrap:
        text = TAG_OPEN + text + TAG_CLOSE
    else:
        text = text[len(TAG_OPEN):][:-len(TAG_CLOSE)]
    return text


def extract_toc(html: str) -> TocType:
    toc = []

    root_element = fromstring(_wrap_unwrap_fake_tag(html))
    for el in root_element:
        if any(el.tag == tag for tag in TOC_HEADERS):
            header_level = int(el.tag[1])
            header_text = el.text
            toc.append((header_level, header_text))

    return toc


def generate_toc_html(toc: TocType) -> str:
    dom = getDOMImplementation()
    doc = dom.createDocument(None, "ul", None)
    parent_element = doc.documentElement
    prev_header_level = 2

    def _create_li_element(parent_element, header_text):
        li = doc.createElement('li')
        a = doc.createElement('a')
        text = doc.createTextNode(header_text)
        href = '#' + _make_header_id(header_text)
        a.appendChild(text)
        a.setAttribute('href', href)
        li.appendChild(a)
        parent_element.appendChild(li)

    for header_level, header_text in toc:
        if header_level > prev_header_level:
            # создаем вложенный ul
            parent_li = parent_element.childNodes[-1]
            ul = doc.createElement('ul')
            parent_li.appendChild(ul)
            parent_element = ul
            _create_li_element(parent_element, header_text)
            pass
        elif header_level == prev_header_level:
            # добавляем в текущий ul
            _create_li_element(parent_element, header_text)
        elif header_level < prev_header_level:
            # откатываемся к ранее созданному ul
            steps = prev_header_level - header_level
            while steps:
                parent_element = parent_element.parentNode
                if parent_element.nodeName == 'ul':
                    steps -= 1
            _create_li_element(parent_element, header_text)
        prev_header_level = header_level

    return doc.documentElement.toxml()


def update_headers_id_attribute(html: str) -> str:
    root_element = fromstring(_wrap_unwrap_fake_tag(html))
    for el in root_element:
        if el.tag in HEADERS:
            id_ = _make_header_id(el.text)
            el.insert(0, Element('a', {'id': id_}))
    html = tostring(root_element, method='html', encoding="utf8").decode()
    html = _wrap_unwrap_fake_tag(html, wrap=False)
    return html


def generate_article_html(file_path):
    with open(file_path) as file:
        text = file.read()
    html = commonmark.commonmark(text)
    # print(html)

    content_html = update_headers_id_attribute(html)
    # print(content_html)

    toc = extract_toc(content_html)
    # print(toc)
    toc_html = generate_toc_html(toc)
    # print(toc_html)

    with open(ARTICLE_TEMPLATE_FILE.as_posix()) as file:
        template_text = file.read()
    html = Template(template_text).substitute({'content': content_html, 'toc': toc_html})
    # print(html)

    with open(BLOG_INDEX_FILE.as_posix(), 'w') as file:
        file.write(html)


def generate_index_html():
    # сканирование
    pass


if __name__ == '__main__':
    import sys
    file_path = sys.argv[1]
    generate_article_html(file_path)
