import commonmark

from typing import List, Tuple
from xml.dom.minidom import getDOMImplementation
from pathlib import Path
from dataclasses import dataclass
from lxml.html import Element, fromstring, tostring
from jinja2 import Environment, FileSystemLoader, select_autoescape


PROJ_DIR = Path(__file__).parent.parent
BUILD_DIR = PROJ_DIR / 'build'
DOCS_DIR = PROJ_DIR / 'docs'
ARTICLES_SOURCE_DIR = PROJ_DIR / 'articles'
ARTICLES_DOCS_DIR = DOCS_DIR / 'articles'
TEMPLATES_DIR = BUILD_DIR / 'templates'
ARTICLE_TEMPLATE_FILE = TEMPLATES_DIR / 'article.jinja'
INDEX_TEMPLATE_FILE = TEMPLATES_DIR / 'index.jinja'
INDEX_FILE = DOCS_DIR / 'index.html'
ARTICLE_MD_FILE = 'README.md'
ARTICLE_IMG_FILE = 'files/main-section.png'
HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TocType = List[Tuple[int, str]]

Dom = getDOMImplementation()
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR.as_posix()), trim_blocks=True,
                  autoescape=select_autoescape(['html']))


@dataclass
class ArticleData:
    title: str
    relative_link: str
    paragraph: str
    date: str
    img_relative_link: str = None


def _make_header_id(tag_text):
    return tag_text.lower().replace(' ', '-')


def _wrap_unwrap_fake_tag(text, wrap=True): # todo use lxml.html
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
    doc = Dom.createDocument(None, "ul", None)
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
    html = tostring(root_element, encoding='unicode')
    html = _wrap_unwrap_fake_tag(html, wrap=False)
    return html


def generate_article_html(md_text):
    html = commonmark.commonmark(md_text)
    # print(html)

    content_html = update_headers_id_attribute(html)
    # print(content_html)

    toc = extract_toc(content_html)
    # print(toc)
    toc_html = generate_toc_html(toc)
    # print(toc_html)
    template = env.get_template(ARTICLE_TEMPLATE_FILE.name)
    html = template.render(content=content_html, toc=toc_html)
    # print(html)
    return html


def generate_index_html(articles_data: List[ArticleData]):
    template = env.get_template(INDEX_TEMPLATE_FILE.name)
    html = template.render(articles_data=articles_data)
    return html


def main():
    articles_data = []
    for adir in ARTICLES_SOURCE_DIR.iterdir():
        article_md_file = adir / ARTICLE_MD_FILE
        md_text = article_md_file.read_text()
        article_html = generate_article_html(md_text)
        article_index_file = ARTICLES_DOCS_DIR / adir.name / INDEX_FILE.name
        article_index_file.parent.mkdir(parents=True, exist_ok=True)
        article_index_file.write_text(article_html)

        root_element = fromstring(article_html)
        first_h1_text = root_element.find('.//h1').text
        first_p_text = root_element.find('.//p').text
        relative_link = article_index_file.relative_to(DOCS_DIR).parent.as_posix()
        date = adir.name
        adata = ArticleData(title=first_h1_text, relative_link=relative_link, paragraph=first_p_text,
                            date=date)
        articles_data.append(adata)

    index_html = generate_index_html(articles_data)
    INDEX_FILE.write_text(index_html)


if __name__ == '__main__':
    import sys
    file_path = sys.argv[1]
    main()
