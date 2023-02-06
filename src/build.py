import os
import functools
from typing import List, Tuple, Set
from xml.dom.minidom import getDOMImplementation
from dataclasses import dataclass, InitVar
from itertools import chain
from contextlib import suppress
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser

import markdown_it
from lxml.html import Element, fromstring, tostring as _tostring
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.lexers.shell import BashSessionLexer
from pygments.lexers.configs import TOMLLexer
from pygments.formatters.html import HtmlFormatter
from slugify import slugify

from constants import (DOCS_DIR, ARTICLES_DOCS_DIR, TEMPLATES_DIR, ARTICLE_TEMPLATE_FILE,
                       INDEX_TEMPLATE_FILE, INDEX_FILE, AS_DIRS_IGNORE,
                       SITEMAP_TEMPLATE_FILE, SITEMAP_FILE, SITE_ADDRESS, RSS_FILE, RSS_TEMPLATE_FILE, ARTICLE_IMG_FILE,
                       SITE_NAME, ANALYTICS_SERVICE_TOKEN, ANALYTICS_SERVICE_JS,
                       ANALYTICS_SERVICE_PAGE, ANALYTICS_ENABLED_DEFAULT, MONITORING_ENABLED_DEFAULT,
                       MONITORING_SERVICE_PAGE, STATUSPAGE_ENABLED_DEFAULT, STATUSPAGE_SERVICE_ADDRESS,
                       MEMOCARDS_ENABLED_DEFAULT, MEMOCARDS_SERVICE_ADDRESS)
from filters import trailing_slash, to_rfc822, prepend_site_address, update_classes
from utils import make_header_id, wrap_unwrap_fake_tag, first_h1_text, first_p_text


HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TOC_LOWEST_HEADER = 3  # эквивалент <h3>
TocType = List[Tuple[int, str]]

Dom = getDOMImplementation()
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR.as_posix()), trim_blocks=True,
                  autoescape=select_autoescape(['html']))
env.globals['site_address'] = SITE_ADDRESS
env.globals['site_name'] = SITE_NAME
env.globals['analytics_service_token'] = ANALYTICS_SERVICE_TOKEN
env.globals['analytics_service_js'] = ANALYTICS_SERVICE_JS
env.globals['analytics_service_page'] = ANALYTICS_SERVICE_PAGE
env.globals['monitoring_service_page'] = MONITORING_SERVICE_PAGE
env.globals['memocards_service_address'] = MEMOCARDS_SERVICE_ADDRESS
env.globals['statuspage_service_page'] = STATUSPAGE_SERVICE_ADDRESS
env.filters['trailing_slash'] = trailing_slash
env.filters['to_rfc822'] = to_rfc822
env.filters['prepend_site_address'] = prepend_site_address
env.filters['update_classes'] = update_classes
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


def iter_articles_source_dir(articles_dir: Path, reverse=False):
    ignore_dirs = set(articles_dir / d for d in AS_DIRS_IGNORE)
    iter_dir = articles_dir.iterdir()

    for article_source_dir in sorted(iter_dir, reverse=reverse):
        if article_source_dir not in ignore_dirs:
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
    ANCHOR_LINK_ICON_CLASS = 'bi:link-45deg'
    EXTENSIONS_ICON_CLASSES_MAP = {'png': 'bi:file-earmark-image',
                                   'jpg': 'bi:file-earmark-image',
                                   'jpeg': 'bi:file-earmark-image',
                                   'txt': 'bi:file-earmark-text',
                                   'md': 'bi:markdown',
                                   'py': 'teenyicons:python-outline',
                                   'gz': 'icomoon-free:file-zip',
                                   'sql': 'bi:file-earmark-code',
                                   'sh': 'bi:terminal'}
    HIGHLIGHTING_STYLE_MAP = {'language-python': 'friendly',
                              'language-shell': 'friendly',
                              'language-toml': 'friendly'}
    LEXER_MAP = {'language-python': PythonLexer,
                 'language-shell': BashSessionLexer,
                 'language-toml': TOMLLexer}

    @staticmethod
    def generate_index_html(articles_data: List[ArticleData]):
        template = env.get_template(INDEX_TEMPLATE_FILE.name)
        html = template.render(articles_data=articles_data)
        return html

    @staticmethod
    def generate_article_html(md_text, font_icons: bool = False, highlight: bool = False, analytics: bool = ANALYTICS_ENABLED_DEFAULT):
        """Article is two big blocks `toc`, `content`"""
        parser = markdown_it.MarkdownIt().enable('table')
        html = parser.render(md_text)

        content_html = HTMLGen._apply_headers_anchors(html)

        toc = HTMLGen._extract_toc(content_html)
        toc_html = HTMLGen._generate_toc_html(toc)  # search the anchors
        content_html = HTMLGen._apply_font_icons(content_html) if font_icons else content_html
        content_html = HTMLGen._apply_highlighting(content_html) if highlight else content_html
        content_html = HTMLGen._apply_analytics_event_type(content_html) if analytics else content_html
        root_element = fromstring(content_html)
        template = env.get_template(ARTICLE_TEMPLATE_FILE.name)
        title = first_h1_text(root_element)
        description = first_p_text(root_element)
        html = template.render(content=content_html, toc=toc_html, title=title, description=description)

        return html, toc_html

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
    def _apply_font_icons(html):
        root = fromstring(wrap_unwrap_fake_tag(html))
        for element in root.iter('a'):
            resource = element.attrib.get('href')
            if not (resource and element.text):  # text is empty in anchors <a>
                continue

            # external link
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
                a_element = Element('a', attrib={'id': id_, 'href': f'#{id_}'})
                span_element = Element('span', attrib={'class': 'iconify',
                                                       'data-icon': HTMLGen.ANCHOR_LINK_ICON_CLASS})
                a_element.append(span_element)
                element.text += ' '
                element.insert(0, a_element)
        html = tostring(root_element)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html
        
    @staticmethod
    def _apply_analytics_event_type(html: str) -> str:
        root_element = fromstring(wrap_unwrap_fake_tag(html))
        elements = (e for e in root_element.iter('a')
                    if e.attrib.has_key('href')
                    and not e.attrib['href'].startswith('#'))  # anchor is ignored

        for element in elements:
            href = element.attrib['href'].split('://', 1)[-1]  # can be splitted into one
            event_type = 'umami--click--' + slugify(href)
            element.classes.add(event_type)
            
        html = tostring(root_element)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html
        
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
                code_sub_elements = highlight(code, Lexer(), HtmlFormatter(noclasses=True, wrapcode=False, nowrap=True, style=style))
                code_sub_elements = fromstring(code_sub_elements)
                code_el.clear()
                code_el.extend(code_sub_elements)
                code_el.text = code_sub_elements.text
                code_el.tail = code_sub_elements.tail

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


def main(articles_dir: Path, font_icons=True, highlight=True,
         analytics=ANALYTICS_ENABLED_DEFAULT,
         monitoring=MONITORING_ENABLED_DEFAULT,
         memocards=MEMOCARDS_ENABLED_DEFAULT,
         statuspage=STATUSPAGE_ENABLED_DEFAULT):
    env.globals['analytics_enabled'] = analytics
    env.globals['monitoring_enabled'] = monitoring
    env.globals['memocards_enabled'] = memocards
    env.globals['statuspage_enabled'] = statuspage
    articles_data = []

    for article_source_dir in iter_articles_source_dir(articles_dir, reverse=True):
        # Генерация страницы и запись в файл
        article_md_file = next(article_source_dir.glob('*.md'))
        md_text = article_md_file.read_text()
        article_html, toc_html = HTMLGen.generate_article_html(md_text, font_icons=font_icons, highlight=highlight, analytics=analytics)
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
        adata = ArticleData(title=first_h1_text(root_element), relative_link=article_relative_symlink,
                            paragraph=first_p_text(root_element), created_date=created_date, images=images)
        articles_data.append(adata)

    index_html = HTMLGen.generate_index_html(articles_data)
    INDEX_FILE.write_text(index_html)

    sitemap_xml = generate_sitemap(articles_data)
    SITEMAP_FILE.write_text(sitemap_xml)

    rss_xml = generate_rss(articles_data)
    RSS_FILE.write_text(rss_xml)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('articlesdir', type=Path, help="Path to an articles folder.")
    parser.add_argument('--enable-analytics', action="store_true", help="Write html tags, add css classes. Substitute values from env file. Enable url.")
    parser.add_argument('--enable-monitoring', action="store_true")
    parser.add_argument('--enable-memocards', action="store_true")
    parser.add_argument('--enable-statuspage', action="store_true")
    args = parser.parse_args()
    
    main(args.articlesdir,
         analytics=args.enable_analytics,
         monitoring=args.enable_monitoring,
         memocards=args.enable_memocards,
         statuspage=args.enable_statuspage)
