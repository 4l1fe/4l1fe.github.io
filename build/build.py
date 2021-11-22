import os
import functools
import markdown_it

from typing import List, Tuple, Set
from xml.dom.minidom import getDOMImplementation
from dataclasses import dataclass, InitVar
from itertools import islice, chain
from contextlib import suppress
from pathlib import Path
from lxml.html import Element, fromstring, tostring as _tostring
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from constants import (DOCS_DIR, ARTICLES_SOURCE_DIR, ARTICLES_DOCS_DIR, TEMPLATES_DIR, ARTICLE_TEMPLATE_FILE,
                       INDEX_TEMPLATE_FILE, INDEX_FILE, ARTICLE_MD_FILE, AS_DIRS_IGNORE, GOOGLE_VERF_TOKEN,
                       SITEMAP_TEMPLATE_FILE, SITEMAP_FILE, SITE_ADDR, RSS_FILE, RSS_TEMPLATE_FILE)


HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TOC_LOWEST_HEADER = 3  # эквивалент <h3>
TocType = List[Tuple[int, str]]


def trailing_slash(link: Path) -> str:
    return link.as_posix() + '/'


def to_rfc822(dt: datetime) -> str:
    return dt.strftime('%d %b %Y 00:00:00 +0000').lstrip('0')


Dom = getDOMImplementation()
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR.as_posix()), trim_blocks=True,
                  autoescape=select_autoescape(['html']))
env.globals['google_verification_token'] = GOOGLE_VERF_TOKEN
env.globals['site_addr'] = SITE_ADDR
env.filters['trailing_slash'] = trailing_slash
env.filters['to_rfc822'] = to_rfc822
tostring = functools.partial(_tostring, encoding='unicode')


@dataclass
class Image:
    title: str
    relative_link: Path
    article_relative_link: InitVar[Path]

    def __post_init__(self, article_relative_link):
        self.relative_link = article_relative_link.joinpath(self.relative_link)


@dataclass
class ArticleData:
    title: str
    relative_link: Path
    paragraph: str
    created_date: datetime
    img_relative_link: Path = None
    images: Tuple[Image] = ()


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
            header_text = el.text.strip()
            toc.append((header_level, header_text))

    return toc


def generate_toc_html(toc: TocType, lowest_header_lvl=TOC_LOWEST_HEADER) -> str:
    doc = Dom.createDocument(None, "ol", None)
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
        if header_level > lowest_header_lvl:
            continue

        if header_level > prev_header_level:
            # создаем вложенный ol
            parent_li = parent_element.childNodes[-1]
            ol = doc.createElement('ol')
            parent_li.appendChild(ol)
            parent_element = ol
            _create_li_element(parent_element, header_text)
            pass
        elif header_level == prev_header_level:
            # добавляем в текущий ol
            _create_li_element(parent_element, header_text)
        elif header_level < prev_header_level:
            # откатываемся к ранее созданному ol
            steps = prev_header_level - header_level
            while steps:
                parent_element = parent_element.parentNode
                if parent_element.nodeName == 'ol':
                    steps -= 1
            _create_li_element(parent_element, header_text)
        prev_header_level = header_level

    return doc.documentElement.toxml()


def generate_index_html(articles_data: List[ArticleData]):
    template = env.get_template(INDEX_TEMPLATE_FILE.name)
    html = template.render(articles_data=articles_data)
    return html


def retrieve_attached_files_paths(html) -> Tuple[Set[str], dict]:
    element = fromstring(html)
    files, images = set(), dict()
    for el in element.findall('.//a'):
        if el.attrib.get('href', '').startswith('files/'):
            files.add(el.attrib['href'])
    for el in element.findall('.//img'):
        if el.attrib.get('src', '').startswith('files/'):
            title = el.attrib.get('title', '')
            images[el.attrib['src']] = title

    return files, images


def generate_sitemap(articles_data: List[ArticleData]):
    template = env.get_template(SITEMAP_TEMPLATE_FILE.name)
    xml = template.render(articles_data=articles_data)
    return xml


def generate_rss(articles_data: List[ArticleData]):
    template = env.get_template(RSS_TEMPLATE_FILE.name)
    pub_date = datetime.now()
    xml = template.render(pub_date=pub_date, articles_data=articles_data)
    return xml


class BlogGen:
    EXTERNAL_LINK_ICON_CLASS = 'bx:bx-link-external'
    ANCHOR_LINK_ICON_CLASS = 'majesticons:hashtag-line'
    EXTENSIONS_ICON_CLASSES_MAP = {'png': 'bi:file-earmark-image',
                                   'jpg': 'bi:file-earmark-image',
                                   'jpeg': 'bi:file-earmark-image',
                                   'txt': 'bi:file-earmark-text',
                                   'md': 'bi:markdown',
                                   'py': 'teenyicons:python-outline',
                                   'gz': 'icomoon-free:file-zip',
                                   'sql': 'bi:file-earmark-code'}

    @staticmethod
    def iter_articles_source_dir(reverse=False):
        iter_dir = ARTICLES_SOURCE_DIR.iterdir()

        for article_source_dir in sorted(iter_dir, reverse=reverse):
            if article_source_dir not in AS_DIRS_IGNORE:
                yield article_source_dir

    @staticmethod
    def apply_font_icons(html):
        root = fromstring(_wrap_unwrap_fake_tag(html))
        for element in root.iter('a'):
            resource = element.attrib.get('href')
            if not (resource and element.text):  # .text empty in anchors <a>
                continue

            # External link
            if resource.startswith('http'):
                icon_class = BlogGen.EXTERNAL_LINK_ICON_CLASS
            # Anchor
            elif resource.startswith('#'):
                icon_class = BlogGen.ANCHOR_LINK_ICON_CLASS
            # File
            elif any(map(resource.endswith, BlogGen.EXTENSIONS_ICON_CLASSES_MAP.keys())):
                extension = resource.rsplit('.', 1)[-1]
                icon_class = BlogGen.EXTENSIONS_ICON_CLASSES_MAP[extension]
            else:
                print('Unknown icon resource ', resource)
                continue

            # Element prototype
            span_element = Element('span', attrib={'class': 'iconify', 'data-icon': icon_class})
            span_element.tail = ' ' + element.text
            element.text = None
            element.insert(0, span_element)
        html = tostring(root)
        html = _wrap_unwrap_fake_tag(html, wrap=False)
        return html

    @staticmethod
    def generate_article_html(md_text, font_icons=False):
        parser = markdown_it.MarkdownIt().enable('table')
        html = parser.render(md_text)

        content_html = BlogGen.add_headers_anchors(html)

        toc = extract_toc(content_html)
        toc_html = generate_toc_html(toc)
        template = env.get_template(ARTICLE_TEMPLATE_FILE.name)
        content_html = BlogGen.apply_font_icons(content_html) if font_icons else content_html
        html = template.render(content=content_html, toc=toc_html)

        return html, toc_html

    @staticmethod
    def add_headers_anchors(html: str) -> str:
        root_element = fromstring(_wrap_unwrap_fake_tag(html))
        for element in root_element:
            if element.tag in HEADERS:
                id_ = _make_header_id(element.text)
                a_element = Element('a', {'id': id_, 'href': f'#{id_}'})
                span_element = Element('span', attrib={'class': 'iconify',
                                                       'data-icon': BlogGen.ANCHOR_LINK_ICON_CLASS})
                a_element.append(span_element)
                element.text += ' '
                element.insert(0, a_element)
        html = tostring(root_element)
        html = _wrap_unwrap_fake_tag(html, wrap=False)
        return html


def main(font_icons=True):
    articles_data = []
    for article_source_dir in BlogGen.iter_articles_source_dir(reverse=True):
        # Генерация обновленной страницы
        article_md_file = article_source_dir / ARTICLE_MD_FILE
        md_text = article_md_file.read_text()
        article_html, toc_html = BlogGen.generate_article_html(md_text, font_icons=font_icons)
        article_dir = ARTICLES_DOCS_DIR / article_source_dir.name
        article_index_file = article_dir / INDEX_FILE.name
        article_index_file.parent.mkdir(parents=True, exist_ok=True)
        article_index_file.write_text(article_html)

        # Создание ссылок на прикрепляемые файлы
        files_paths, images = retrieve_attached_files_paths(article_html)
        for path in chain(files_paths, images.keys()):
            # Жесткие ссылки на исходные файлы
            target = article_source_dir / path
            hardlink_file = article_index_file.parent / path
            hardlink_file.parent.mkdir(parents=True, exist_ok=True)
            with suppress(FileExistsError):
                os.link(target, hardlink_file)

        # Создание класса данных по статье для индекса блога
        root_element = fromstring(article_html)
        first_h1_text = root_element.find('.//h1').text
        first_p_text = list(islice(root_element.iterfind('.//p'), 2))[1].text
        article_relative_link = article_index_file.relative_to(DOCS_DIR).parent
        created_date = datetime.strptime(article_source_dir.name, '%Y-%m-%d')
        images = tuple(Image(title, path, article_relative_link) for path, title in images.items() if title)
        adata = ArticleData(title=first_h1_text, relative_link=article_relative_link, paragraph=first_p_text,
                            created_date=created_date, images=images)
        articles_data.append(adata)

    index_html = generate_index_html(articles_data)
    INDEX_FILE.write_text(index_html)
    sitemap_xml = generate_sitemap(articles_data)
    SITEMAP_FILE.write_text(sitemap_xml)
    rss_xml = generate_rss(articles_data)
    RSS_FILE.write_text(rss_xml)


if __name__ == '__main__':
    main()
