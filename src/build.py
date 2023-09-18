import os
import functools
from typing import List, Tuple, Set
from xml.dom.minidom import getDOMImplementation
from dataclasses import dataclass
from itertools import chain
from contextlib import suppress
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser
from copy import deepcopy
from enum import Enum

from lxml.html import Element, fromstring, tostring as _tostring
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.lexers.shell import BashSessionLexer
from pygments.lexers.configs import TOMLLexer
from pygments.formatters.html import HtmlFormatter
from slugify import slugify
from more_itertools import split_before

import constants as cns
from filters import trailing_slash, to_rfc822, prepend_site_address, update_classes
from utils import (make_header_id, wrap_unwrap_fake_tag, first_h1_text, first_p_text,
                   replace_relative_with_dots, parser_render, extract_path_date)
from summary import summarize, summarize_refine
from thumbnail import create_thumbnail


HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TOC_LOWEST_HEADER = 3  # Meaning <h3>
TocType = List[Tuple[int, str]]

Dom = getDOMImplementation()
env = Environment(loader=FileSystemLoader(cns.TEMPLATES_DIR.as_posix()), trim_blocks=True,
                  autoescape=select_autoescape(['html']))
env.globals['site_address'] = cns.SITE_ADDRESS
env.globals['site_name'] = cns.SITE_NAME
env.globals['analytics_service_token'] = cns.ANALYTICS_SERVICE_TOKEN
env.globals['analytics_service_js'] = cns.ANALYTICS_SERVICE_JS
env.globals['analytics_service_page'] = cns.ANALYTICS_SERVICE_PAGE
env.globals['monitoring_service_page'] = cns.MONITORING_SERVICE_PAGE
env.globals['memocards_service_address'] = cns.MEMOCARDS_SERVICE_ADDRESS
env.globals['statuspage_service_page'] = cns.STATUSPAGE_SERVICE_ADDRESS
env.filters['trailing_slash'] = trailing_slash
env.filters['to_rfc822'] = to_rfc822
env.filters['prepend_site_address'] = prepend_site_address
env.filters['update_classes'] = update_classes
tostring = functools.partial(_tostring, encoding='unicode')


@dataclass
class AttachedImage:
    title: str
    relative_link: Path  # to plug into html
    relative_path: Path


@dataclass
class ArticleData:
    title: str
    relative_link: Path
    paragraph: str
    created_date: datetime  # article unique id
    main_img_relative_link: Path = cns.ARTICLE_IMG_FILE
    images: Tuple[AttachedImage] = ()

    def __post_init__(self):
        self.main_img_relative_link = self.relative_link.joinpath(self.main_img_relative_link)


class IndexViewEnum(str, Enum):
    default = ''
    preview = 'preview'
    summary = 'summary'


@dataclass
class ThumbnailPair:
    source_path: str
    thumbnail_link: str


@functools.lru_cache 
def list_article_md_files(articles_dir: Path, reverse=False) -> list:
    ignore_dirs = set(articles_dir / d for d in cns.AS_DIRS_IGNORE)
    iter_dir = articles_dir.iterdir()

    md_files = []
    for article_source_dir in sorted(iter_dir, reverse=reverse):
        if article_source_dir not in ignore_dirs:
            article_md_file = next(article_source_dir.glob('*.md'))
            md_files.append(article_md_file)

    return md_files


def generate_sitemap(articles_data: List[ArticleData]):
    template = env.get_template(cns.SITEMAP_TEMPLATE_FILE.name)
    xml = template.render(articles_data=articles_data)
    return xml


def generate_rss(articles_data: List[ArticleData]):
    template = env.get_template(cns.RSS_TEMPLATE_FILE.name)
    pub_date = datetime.now()
    xml = template.render(pub_date=pub_date, articles_data=articles_data)
    return xml


class HTMLGen:
    """Convert markdown to html. Operations on generating, extracting, formating html"""
    
    EXTERNAL_LINK_ICON_CLASS = 'la:external-link-alt'
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
                                   'sh': 'bi:terminal',
                                   'json': 'bi:filetype-json',
                                   'bz2': 'icomoon-free:file-zip'}
    HIGHLIGHTING_STYLE_MAP = {'language-python': 'friendly',
                              'language-shell': 'friendly',
                              'language-toml': 'friendly'}
    LEXER_MAP = {'language-python': PythonLexer,
                 'language-shell': BashSessionLexer,
                 'language-toml': TOMLLexer}

    @staticmethod
    def generate_index_html(articles_data: List[ArticleData], view: IndexViewEnum, view_data=None):
        template = env.get_template(cns.INDEX_TEMPLATE_FILE.name)
        html = template.render(articles_data=articles_data, selected_view=view,
                               IndexViewEnum=IndexViewEnum, view_data=view_data)
        return html

    @staticmethod
    def generate_article_html(md_file,  article_index_file, article_source_dir,
                              font_icons: bool = False, highlight: bool = False,
                              track_analytics: bool = cns.TRACK_ANALYTICS):
        """Article is two big blocks `toc`, `content`"""
        html = parser_render(md_file)

        content_html = HTMLGen._apply_headers_anchors(html)

        toc = HTMLGen._extract_toc(content_html)
        toc_html = HTMLGen._generate_toc_html(toc)  # search the anchors
        content_html = HTMLGen._apply_responsive_table(content_html)
        content_html = HTMLGen._apply_font_icons(content_html) if font_icons else content_html
        content_html = HTMLGen._apply_highlighting(content_html) if highlight else content_html
        content_html = HTMLGen._apply_analytics_event_type(content_html) if track_analytics else content_html
        root_element = fromstring(content_html)
        files_paths, images = HTMLGen.retrieve_attached_files_paths(html)
        article_data = HTMLGen._make_article_data(content_html, article_index_file, article_source_dir, images)

        template = env.get_template(cns.ARTICLE_TEMPLATE_FILE.name)
        title = first_h1_text(root_element)
        description = first_p_text(root_element)
        
        html = template.render(content=content_html, toc=toc_html, title=title,
                               description=description, article_data=article_data)

        return html, toc_html, article_data, files_paths, images

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
            element.text +=  ' '  # space before an icon
            element.append(span_element)
        html = tostring(root)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html

    @staticmethod
    def _apply_headers_anchors(html: str) -> str:
        root_element = fromstring(wrap_unwrap_fake_tag(html))
        for element in root_element:
            if element.tag in HEADERS:
                id_ = make_header_id(element.text)
                a_element = Element('a', attrib={'id': id_,
                                                 'href': f'#{id_}',
                                                 'class': 'header-anchor'})
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
    def _apply_responsive_table(html: str):
        replacing = []
        root_element = fromstring(wrap_unwrap_fake_tag(html))

        for table_el in root_element.iterfind('.//table'):
            div_el = Element('div', attrib={'class': 'table-responsive'})
            div_el.append(deepcopy(table_el))
            parent_el = table_el.getparent()
            replacing.append((parent_el, table_el, div_el))

        for parent_el, old_el, new_el in replacing:
            parent_el.replace(old_el, new_el)

        html = tostring(root_element)
        html = wrap_unwrap_fake_tag(html, wrap=False)
        return html

    @staticmethod
    def _make_article_data(html: str, article_index_file, article_source_dir, images) -> ArticleData:
        root_element = fromstring(html)
        symlink_name = slugify(first_h1_text(root_element))
        article_relative_symlink = cns.DOCS_ARTICLES_DIR.joinpath(symlink_name).relative_to(cns.DOCS_DIR)
        created_date = extract_path_date(article_source_dir.name)

        images = tuple(AttachedImage(title=im_title,
                                     relative_link=article_relative_symlink.joinpath(im_path),
                                     relative_path=im_path)
                       for im_path, im_title in images.items() if im_title)

        adata = ArticleData(title=first_h1_text(root_element),
                            relative_link=article_relative_symlink,
                            paragraph=first_p_text(root_element),
                            created_date=created_date,
                            images=images)

        return adata

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


class ViewBase:

    def __init__(self, is_enabled=False):
        self.is_enabled = is_enabled

    def create(self, *args, **kwargs):
        if not self.is_enabled:
            return

        self._create(*args, **kwargs)

    def _create_index(self, view: IndexViewEnum, articles_data, view_data=None) -> Path:
        index_html = HTMLGen.generate_index_html(articles_data, view, view_data)
        index_dir = cns.VIEWS_DIR / view.value
        index_file = index_dir / cns.DOCS_INDEX_FILE.name
        index_file.parent.mkdir(parents=True, exist_ok=True)
        index_file.write_text(index_html)

        return index_dir

    def _create_symlinks(self, view_dir):
        """Symlinks to the original articles and files dirs."""

        articles_dir_symlink = view_dir / cns.DOCS_ARTICLES_DIR.name
        relative_target_path = replace_relative_with_dots(articles_dir_symlink, cns.DOCS_DIR)
        if not articles_dir_symlink.is_symlink():
            articles_dir_symlink.symlink_to(relative_target_path, target_is_directory=True)

        files_dir_symlink = view_dir / cns.DOCS_FILES_DIR.name
        relative_target_path = replace_relative_with_dots(files_dir_symlink, cns.DOCS_DIR)
        if not files_dir_symlink.is_symlink():
            files_dir_symlink.symlink_to(relative_target_path, target_is_directory=True)


class PreviewView(ViewBase):

    def _create(self, articles_dir, articles_data):
        view_data = {}
        thumbnail_pairs = []
        date_adata = {adata.created_date: adata for adata in articles_data}
        
        for article_md_file in list_article_md_files(articles_dir, reverse=True):
            created_date = extract_path_date(article_md_file.parent.name)
            view_data[created_date] = {'thumbnails': [],
                                       'main_thumbnail': ''}
            
            for image in date_adata[created_date].images:
                source_path = article_md_file.parent / image.relative_path
                thumbnail_link = self._make_thumbnail_link(created_date, image.relative_path)
                thumbnail_pairs.append(ThumbnailPair(source_path=source_path,
                                                     thumbnail_link=thumbnail_link))
                view_data[created_date]['thumbnails'].append(thumbnail_link)

            source_path = article_md_file.parent / cns.ARTICLE_IMG_FILE
            thumbnail_link = self._make_thumbnail_link(created_date, cns.ARTICLE_IMG_FILE)
            thumbnail_pairs.append(ThumbnailPair(source_path=source_path,
                                                 thumbnail_link=thumbnail_link))
            view_data[created_date]['main_thumbnail'] = thumbnail_link

        index_dir = self._create_index(IndexViewEnum.preview, articles_data, view_data=view_data)
        self._create_symlinks(index_dir)

        for tpair in thumbnail_pairs:
            thumbnail_path = index_dir / tpair.thumbnail_link
            create_thumbnail(tpair.source_path, thumbnail_path)
 
    def _make_thumbnail_link(self, date, link):
        return cns.THUMBNAILS_DIR / date.strftime('%Y-%m-%d') / link


class SummaryView(ViewBase):

    def _create(self, articles_dir, articles_data):
        view_data = {}
        for article_md_file in list_article_md_files(articles_dir, reverse=True):
            summary = self._summarize(article_md_file)
            created_date = extract_path_date(article_md_file.parent.name)
            view_data[created_date] = summary
        
        index_dir = self._create_index(IndexViewEnum.summary, articles_data, view_data)
        self._create_symlinks(index_dir)

    def _summarize(self, md_file: Path):
        clean_element = self._clean_text(md_file)
        text_chunks = list(self._split_text_iter(clean_element))
        # result = summarize(text_chunks)
        result = summarize_refine(text_chunks)
        return result

    def _clean_text(self, md_file: Path) -> Element:
        """Remove code blocks, images, and tables from an article's source text"""   

        html = parser_render(md_file)
        doc = fromstring(html)
        remove_exprs = ['.//pre[code]', './/table', './/img']
        findall = lambda doc, xpath_list: chain(*(doc.findall(xpath) for xpath in xpath_list))
        
        remove_elements = findall(doc, remove_exprs)
        for element in remove_elements:
            try:
                doc.remove(element)
            except ValueError as e:
                # error `Element is not a child of this node` more likely refers to an already removed element.
                print(e)

        return doc

    def _split_text_iter(self, element):        
        """Split on the `h2` header"""

        wrapper_el = Element('div')
        for sub_elements in split_before(element.iterchildren(), lambda el: el.tag == 'h2'):
            
            wrapper_el.extend(sub_elements)
            yield str(wrapper_el.text_content())  # convert lxml.etree._ElementUnicodeResult
            wrapper_el.clear()
            

def main(articles_dir: Path, font_icons=True, highlight=True,
         track_analytics=cns.TRACK_ANALYTICS,
         analytics=cns.ANALYTICS_ENABLED_DEFAULT,
         monitoring=cns.MONITORING_ENABLED_DEFAULT,
         memocards=cns.MEMOCARDS_ENABLED_DEFAULT,
         statuspage=cns.STATUSPAGE_ENABLED_DEFAULT,
         preview_view=False,
         summary_view=False):
    env.globals['track_analytics'] = track_analytics
    env.globals['analytics_enabled'] = analytics
    env.globals['monitoring_enabled'] = monitoring
    env.globals['memocards_enabled'] = memocards
    env.globals['statuspage_enabled'] = statuspage
    articles_data = []

    import sys
    import aspectlib
    import aspectlib.debug
    for article_md_file in list_article_md_files(articles_dir, reverse=True):
        # Generate an article html and write it in a file
        article_source_dir = article_md_file.parent
        article_dir = cns.DOCS_ARTICLES_DIR / article_source_dir.name
        article_index_file = article_dir / cns.DOCS_INDEX_FILE.name
        # with aspectlib.weave(HTMLGen,
        #                      aspectlib.debug.log(print_to=sys.stdout, stacktrace=None),
        #                      lazy=True):
        data = HTMLGen.generate_article_html(article_md_file, article_index_file, article_source_dir,
                                             font_icons=font_icons, highlight=highlight,
                                             track_analytics=track_analytics)
        article_html, toc_html, article_data, files_paths, images = data
        article_index_file.parent.mkdir(parents=True, exist_ok=True)
        article_index_file.write_text(article_html)
        articles_data.append(article_data)

        # Making hardlinks to attached files
        # files_paths, images = HTMLGen.retrieve_attached_files_paths(article_html)
        for file_path in chain(files_paths, images.keys()):
            target_path = article_source_dir / file_path
            hardlink_source_path = article_index_file.parent / file_path
            hardlink_source_path.parent.mkdir(parents=True, exist_ok=True)
            with suppress(FileExistsError):
                os.link(target_path, hardlink_source_path)

        # Symbol links with human-readable name
        article_relative_link = article_index_file.relative_to(cns.DOCS_DIR).parent
        article_relative_symlink_path = Path('..') / cns.DOCS_DIR.name / article_data.relative_link
        if not article_relative_symlink_path.is_symlink():
            os.symlink(article_relative_link.name,
                       article_relative_symlink_path,
                       target_is_directory=True)

    # Generate the original index
    index_html = HTMLGen.generate_index_html(articles_data, IndexViewEnum.default)
    cns.DOCS_INDEX_FILE.write_text(index_html)

    # Views
    pv = PreviewView(is_enabled=preview_view)
    pv.create(articles_dir, articles_data)

    sv = SummaryView(is_enabled=summary_view)
    sv.create(articles_dir, articles_data)

    # Sitemap, RSS
    sitemap_xml = generate_sitemap(articles_data)
    cns.SITEMAP_FILE.write_text(sitemap_xml)

    rss_xml = generate_rss(articles_data)
    cns.RSS_FILE.write_text(rss_xml)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('articlesdir', type=Path, help="Path to an articles folder.")
    parser.add_argument('--track-analytics', action="store_true", help="Activate tracking. Write html tags, add css classes. Substitute values from env file. Enable url.")
    parser.add_argument('--enable-analytics', action="store_true", help="Display a serivice in the list on the index page.")
    parser.add_argument('--enable-monitoring', action="store_true")
    parser.add_argument('--enable-memocards', action="store_true")
    parser.add_argument('--enable-statuspage', action="store_true")
    parser.add_argument('--preview-view', action="store_true")
    parser.add_argument('--summary-view', action="store_true")
    args = parser.parse_args()
    
    main(args.articlesdir,
         track_analytics=args.track_analytics,
         analytics=args.enable_analytics,
         monitoring=args.enable_monitoring,
         memocards=args.enable_memocards,
         statuspage=args.enable_statuspage,
         preview_view=args.preview_view,
         summary_view=args.summary_view)
