import os
import functools
from typing import List, Tuple, Set
from xml.dom.minidom import getDOMImplementation
from dataclasses import dataclass, InitVar
from itertools import chain
from contextlib import suppress
from pathlib import Path
from datetime import datetime

import markdown_it
from lxml.html import Element, fromstring, tostring as _tostring
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters.html import HtmlFormatter
from slugify import slugify
from constants import (DOCS_DIR, ARTICLES_SOURCE_DIR, ARTICLES_DOCS_DIR, TEMPLATES_DIR, ARTICLE_TEMPLATE_FILE,
                       INDEX_TEMPLATE_FILE, INDEX_FILE, ARTICLE_MD_FILE, AS_DIRS_IGNORE, GOOGLE_VERF_TOKEN,
                       SITEMAP_TEMPLATE_FILE, SITEMAP_FILE, SITE_ADDRESS, RSS_FILE, RSS_TEMPLATE_FILE, ARTICLE_IMG_FILE,
                       SITE_NAME)
from filters import trailing_slash, to_rfc822, prepend_site_address
from utils import make_header_id, wrap_unwrap_fake_tag, first_h1_text, first_p_text

HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TOC_LOWEST_HEADER = 3  # эквивалент <h3>
TocType = List[Tuple[int, str]]

Dom = getDOMImplementation()
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR.as_posix()), trim_blocks=True,
                  autoescape=select_autoescape(['html']))
env.globals['google_verification_token'] = GOOGLE_VERF_TOKEN
env.globals['site_address'] = SITE_ADDRESS
env.globals['site_name'] = SITE_NAME
env.filters['trailing_slash'] = trailing_slash
env.filters['to_rfc822'] = to_rfc822
env.filters['prepend_site_address'] = prepend_site_address
tostring = functools.partial(_tostring, encoding='unicode')


@dataclass
class AttachedImage:
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
    img_relative_link: Path = ARTICLE_IMG_FILE
    images: Tuple[AttachedImage] = ()

    def __post_init__(self):
        self.img_relative_link = self.relative_link.joinpath(self.img_relative_link)


def iter_articles_source_dir(reverse=False):
    iter_dir = ARTICLES_SOURCE_DIR.iterdir()

    for article_source_dir in sorted(iter_dir, reverse=reverse):
        if article_source_dir not in AS_DIRS_IGNORE:
            yield article_source_dir


def generate_sitemap(articles_data: List[ArticleData]):
    template = env.get_template(SITEMAP_TEMPLATE_FILE.name)
    xml = template.render(articles_data=articles_data)
    return xml


def generate_rss(articles_data: List[ArticleData]):
    template = env.get_template(RSS_TEMPLATE_FILE.name)
    pub_date = datetime.now()
    xml = template.render(pub_date=pub_date, articles_data=articles_data)
    return xml


class HTMLGen:
    EXTERNAL_LINK_ICON_CLASS = 'bx:bx-link-external'
    EXTERNAL_LINK_GITHUB_ICON_CLASS = 'codicon:github-inverted'
    ANCHOR_LINK_ICON_CLASS = 'majesticons:hashtag-line'
    EXTENSIONS_ICON_CLASSES_MAP = {'png': 'bi:file-earmark-image',
                                   'jpg': 'bi:file-earmark-image',
                                   'jpeg': 'bi:file-earmark-image',
                                   'txt': 'bi:file-earmark-text',
                                   'md': 'bi:markdown',
                                   'py': 'teenyicons:python-outline',
                                   'gz': 'icomoon-free:file-zip',
                                   'sql': 'bi:file-earmark-code'}
    HIGHLIGHTING_STYLE_MAP = {'language-python': 'monokai'}
    LEXER_MAP = {'language-python': PythonLexer}

    @staticmethod
    def generate_index_html(articles_data: List[ArticleData]):
        template = env.get_template(INDEX_TEMPLATE_FILE.name)
        html = template.render(articles_data=articles_data)
        return html

    @staticmethod
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

    @staticmethod
    def generate_article_html(md_text, font_icons=False, highlight=False):
        parser = markdown_it.MarkdownIt().enable('table')
        html = parser.render(md_text)

        content_html = HTMLGen._apply_headers_anchors(html)

        toc = HTMLGen._extract_toc(content_html)
        toc_html = HTMLGen._generate_toc_html(toc)
        content_html = HTMLGen._apply_font_icons(content_html) if font_icons else content_html
        content_html = HTMLGen._apply_highlighting(content_html) if highlight else content_html
        root_element = fromstring(content_html)
        template = env.get_template(ARTICLE_TEMPLATE_FILE.name)
        html = template.render(content=content_html, toc=toc_html, title=first_h1_text(root_element), description=first_p_text(root_element))

        return html, toc_html

    @staticmethod
    def _apply_font_icons(html):
        root = fromstring(wrap_unwrap_fake_tag(html))
        for element in root.iter('a'):
            resource = element.attrib.get('href')
            if not (resource and element.text):  # .text empty in anchors <a>
                continue

            # External link
            if resource.startswith('https://github.com'):
                icon_class = HTMLGen.EXTERNAL_LINK_GITHUB_ICON_CLASS
            elif resource.startswith('http'):
                icon_class = HTMLGen.EXTERNAL_LINK_ICON_CLASS
            # Anchor
            elif resource.startswith('#'):
                icon_class = HTMLGen.ANCHOR_LINK_ICON_CLASS
            # File
            elif any(map(resource.endswith, HTMLGen.EXTENSIONS_ICON_CLASSES_MAP.keys())):
                extension = resource.rsplit('.', 1)[-1]
                icon_class = HTMLGen.EXTENSIONS_ICON_CLASSES_MAP[extension]
            else:
                print('Unknown icon resource ', resource)
                continue

            # Element prototype
            span_element = Element('span', attrib={'class': 'iconify', 'data-icon': icon_class})
            span_element.tail = ' ' + element.text
            element.text = None
            element.insert(0, span_element)
        html = tostring(root)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html

    @staticmethod
    def _apply_headers_anchors(html: str) -> str:
        root_element = fromstring(wrap_unwrap_fake_tag(html))
        for element in root_element:
            if element.tag in HEADERS:
                id_ = make_header_id(element.text)
                a_element = Element('a', {'id': id_, 'href': f'#{id_}'})
                span_element = Element('span', attrib={'class': 'iconify',
                                                       'data-icon': HTMLGen.ANCHOR_LINK_ICON_CLASS})
                a_element.append(span_element)
                element.text += ' '
                element.insert(0, a_element)
        html = tostring(root_element)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html

    @staticmethod
    def _extract_toc(html: str) -> TocType:
        toc = []

        root_element = fromstring(wrap_unwrap_fake_tag(html))
        for el in root_element:
            if any(el.tag == tag for tag in TOC_HEADERS):
                header_level = int(el.tag[1])
                header_text = el.text.strip()
                toc.append((header_level, header_text))

        return toc

    @staticmethod
    def _generate_toc_html(toc: TocType, lowest_header_lvl=TOC_LOWEST_HEADER) -> str:
        doc = Dom.createDocument(None, "ol", None)
        parent_element = doc.documentElement
        prev_header_level = 2

        def _create_li_element(parent_element, header_text):
            li = doc.createElement('li')
            a = doc.createElement('a')
            text = doc.createTextNode(header_text)
            href = '#' + make_header_id(header_text)
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

    @staticmethod
    def _apply_highlighting(html: str):
        root_element = fromstring(wrap_unwrap_fake_tag(html))

        for pre_el in root_element.iterfind('.//pre'):
            for code_el in pre_el.iter('code'):
                language = code_el.attrib.get('class')
                style = HTMLGen.HIGHLIGHTING_STYLE_MAP.get(language)
                Lexer = HTMLGen.LEXER_MAP.get(language)
                if not language or not style or not Lexer:
                    continue

                code = code_el.text
                code_elements = highlight(code, Lexer(), HtmlFormatter(noclasses=True, wrapcode=False, nowrap=True, style=style))
                code_elements = fromstring(code_elements)
                code_el.clear()
                code_el.extend(code_elements)

        html = tostring(root_element)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html


def main(font_icons=True):
    articles_data = []

    for article_source_dir in iter_articles_source_dir(reverse=True):
        # Генерация страницы и запись в файл
        article_md_file = article_source_dir / ARTICLE_MD_FILE
        md_text = article_md_file.read_text()
        article_html, toc_html = HTMLGen.generate_article_html(md_text, font_icons=font_icons, highlight=True)
        article_dir = ARTICLES_DOCS_DIR / article_source_dir.name
        article_index_file = article_dir / INDEX_FILE.name
        article_index_file.parent.mkdir(parents=True, exist_ok=True)
        article_index_file.write_text(article_html)

        # Создание ссылок на прикрепляемые файлы
        files_paths, images = HTMLGen.retrieve_attached_files_paths(article_html)
        for path in chain(files_paths, images.keys()):
            # Жесткие ссылки на исходные файлы
            target = article_source_dir / path
            hardlink_file = article_index_file.parent / path
            hardlink_file.parent.mkdir(parents=True, exist_ok=True)
            with suppress(FileExistsError):
                os.link(target, hardlink_file)

        # Создание класса данных по статье для индекса блога
        root_element = fromstring(article_html)
        symlink_name = slugify(first_h1_text(root_element))
        article_relative_link = article_index_file.relative_to(DOCS_DIR).parent
        article_relative_symlink = ARTICLES_DOCS_DIR.joinpath(symlink_name).relative_to(DOCS_DIR)
        article_relative_symlink_path = Path('..') / DOCS_DIR.name / article_relative_symlink
        if not article_relative_symlink_path.is_symlink():
            # Для файловой системы путь не совпадает, но ссылка по тому же узлу
            os.symlink(article_relative_link.name,
                       article_relative_symlink_path,
                       target_is_directory=True)
        created_date = datetime.strptime(article_source_dir.name, '%Y-%m-%d')
        images = tuple(AttachedImage(title, path, article_relative_symlink) for path, title in images.items() if title)
        adata = ArticleData(title=first_h1_text(root_element), relative_link=article_relative_symlink, paragraph=first_p_text(root_element),
                            created_date=created_date, images=images)
        articles_data.append(adata)

    index_html = HTMLGen.generate_index_html(articles_data)
    INDEX_FILE.write_text(index_html)

    sitemap_xml = generate_sitemap(articles_data)
    SITEMAP_FILE.write_text(sitemap_xml)

    rss_xml = generate_rss(articles_data)
    RSS_FILE.write_text(rss_xml)


if __name__ == '__main__':
    main()
