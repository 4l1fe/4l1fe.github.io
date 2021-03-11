import os
import functools
import shutil
import commonmark

from typing import List, Tuple, Set
from xml.dom.minidom import getDOMImplementation
from dataclasses import dataclass
from pathlib import Path
from itertools import islice
from contextlib import suppress
from lxml.html import Element, fromstring, tostring as _tostring
from lxml.html.diff import htmldiff
from jinja2 import Environment, FileSystemLoader, select_autoescape
from constants import DOCS_DIR, ARTICLES_SOURCE_DIR, ARTICLES_DOCS_DIR, TEMPLATES_DIR, \
    ARTICLE_TEMPLATE_FILE, INDEX_TEMPLATE_FILE, INDEX_FILE, ARTICLE_MD_FILE, PROJ_DIR, DIFF_DIR_PREFIX
from diff import FileDiff


HEADERS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')
TOC_HEADERS = HEADERS[1:]
TocType = List[Tuple[int, str]]

Dom = getDOMImplementation()
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR.as_posix()), trim_blocks=True,
                  autoescape=select_autoescape(['html']))
tostring = functools.partial(_tostring, encoding='unicode')


@dataclass
class ArticleData:
    title: str
    relative_link: str
    relative_diff_link: str
    paragraph: str
    created_date: str
    updated_date: str
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
    html = tostring(root_element)
    html = _wrap_unwrap_fake_tag(html, wrap=False)
    return html


def generate_article_html(md_text):
    html = commonmark.commonmark(md_text)
    content_html = update_headers_id_attribute(html)

    toc = extract_toc(content_html)
    toc_html = generate_toc_html(toc)
    template = env.get_template(ARTICLE_TEMPLATE_FILE.name)
    html = template.render(content=content_html, toc=toc_html)

    return html, toc_html


def generate_index_html(articles_data: List[ArticleData]):
    template = env.get_template(INDEX_TEMPLATE_FILE.name)
    html = template.render(articles_data=articles_data)
    return html


def retrieve_article_diff_html(current_html, initial_html):
    old_element = fromstring(initial_html).find('.//div[@id="content"]')
    current_element = fromstring(current_html).find('.//div[@id="content"]')
    diff_html = htmldiff(tostring(old_element), tostring(current_element))
    diff_html = diff_html[diff_html.find('>')+1:]
    diff_html = diff_html[:diff_html.rfind('</')]

    return diff_html


def generate_article_diff_html(content_html, toc_html):
    template = env.get_template(ARTICLE_TEMPLATE_FILE.name)
    html = template.render(content=content_html, toc=toc_html, diff=True)

    return html


def retrieve_attached_files_links(html) -> Set[str]:
    element = fromstring(html)
    files = []
    for el in element.findall('.//a'):
        if el.attrib.get('href', '').startswith('files/'):
            files.append(el.attrib['href'])
    for el in element.findall('.//img'):
        if el.attrib.get('src', '').startswith('files/'):
            files.append(el.attrib['src'])

    return set(files)


def main():
    articles_data = []
    for article_source_dir in ARTICLES_SOURCE_DIR.iterdir():
        # Генерация обновленной страницы
        article_md_file = article_source_dir / ARTICLE_MD_FILE
        md_text = article_md_file.read_text()
        article_html, toc_html = generate_article_html(md_text)
        article_dir = ARTICLES_DOCS_DIR / article_source_dir.name
        article_index_file = article_dir / INDEX_FILE.name
        article_index_file.parent.mkdir(parents=True, exist_ok=True)
        article_index_file.write_text(article_html)

        # Генерация каталога разницы
        fdiff = FileDiff(article_index_file.relative_to(PROJ_DIR))
        initial_article_html = fdiff.get_first_version_text()
        diff_html = retrieve_article_diff_html(article_html, initial_article_html)
        article_diff_html = generate_article_diff_html(diff_html, toc_html)
        diff_update_date = fdiff.get_update_date()
        article_diff_index_file = article_dir / Path(DIFF_DIR_PREFIX + diff_update_date) / INDEX_FILE.name
        article_diff_index_file.parent.mkdir(parents=True, exist_ok=True)
        article_diff_index_file.write_text(article_diff_html)

        # Создание ссылок на прикрепляемые файлы
        files_pathes = retrieve_attached_files_links(article_html)
        for fpath in files_pathes:
            # Жесткие ссылки на исходные файлы
            symlink_target = article_source_dir / fpath
            hardlink_file = article_index_file.parent / fpath
            hardlink_file.parent.mkdir(parents=True, exist_ok=True)
            with suppress(FileExistsError):
                os.link(symlink_target, hardlink_file)
            # Мягкие ссылки на жетские ссылки
            diff_symlink_file = article_diff_index_file.parent / fpath
            diff_symlink_file.parent.mkdir(parents=True, exist_ok=True)
            with suppress(FileExistsError):
                diff_symlink_file.symlink_to(os.path.relpath(hardlink_file, start=diff_symlink_file.parent))

        # Очистка файлов устаревшей разницы
        old_diff_dirs = set(article_dir.glob(DIFF_DIR_PREFIX+'*'))
        old_diff_dirs.remove(article_diff_index_file.parent)
        for old_ddir in old_diff_dirs:
            shutil.rmtree(old_ddir)
            print('Removed: ', old_ddir.as_posix())

        # Создание класса данных по статье для индекса блога
        root_element = fromstring(article_html)
        first_h1_text = root_element.find('.//h1').text
        first_p_text = list(islice(root_element.iterfind('.//p'), 2))[1].text
        img_link = root_element.find('.//img').attrib['src']
        relative_link = article_index_file.relative_to(DOCS_DIR).parent
        relative_diff_link = article_diff_index_file.relative_to(DOCS_DIR).parent
        img_relative_link = relative_link / img_link
        date = article_source_dir.name
        adata = ArticleData(title=first_h1_text, relative_link=relative_link, paragraph=first_p_text,
                            created_date=date, relative_diff_link=relative_diff_link,
                            updated_date=diff_update_date, img_relative_link=img_relative_link)
        articles_data.append(adata)

    index_html = generate_index_html(articles_data)
    INDEX_FILE.write_text(index_html)


if __name__ == '__main__':
    main()
