import os
from pathlib import Path


PROJ_DIR = Path(__file__).parent.parent
BUILD_DIR = PROJ_DIR / 'build'
DOCS_DIR = PROJ_DIR / 'docs'
ARTICLES_SOURCE_DIR = PROJ_DIR / 'articles'
ARTICLES_DOCS_DIR = DOCS_DIR / 'articles'
TEMPLATES_DIR = BUILD_DIR / 'templates'
ARTICLE_TEMPLATE_FILE = TEMPLATES_DIR / 'article.jinja'
INDEX_TEMPLATE_FILE = TEMPLATES_DIR / 'index.jinja'
SITEMAP_TEMPLATE_FILE = TEMPLATES_DIR / 'sitemap.jinja'
RSS_TEMPLATE_FILE = TEMPLATES_DIR / 'rss.jinja'
INDEX_FILE = DOCS_DIR / 'index.html'
SITEMAP_FILE = DOCS_DIR / 'sitemap.xml'
RSS_FILE = DOCS_DIR / 'rss.xml'
AS_DIRS_IGNORE = {ARTICLES_SOURCE_DIR / 'drafts', }
ARTICLE_MD_FILE = 'README.md'
ARTICLE_IMG_FILE = 'files/main-section.png'
SITE_NAME = 'ТехнологоблогЪ'
SITE_ADDRESS = 'https://www.kvdm.dev'

ANALYTICS_ENABLED_DEFAULT = False
ANALYTICS_SERVICE_ADDRESS = os.environ.get("ANALYTICS_SERVICE_ADDRESS", "http://127.0.0.1:3000")
ANALYTICS_SERVICE_TOKEN = os.environ.get("ANALYTICS_SERVICE_TOKEN", "e425b7bc-6ef5-4cb1-af1a-d04b1d7f0844")
ANALYTICS_SERVICE_JS = ANALYTICS_SERVICE_ADDRESS + "/umami.js"
ANALYTICS_SERVICE_PAGE = ANALYTICS_SERVICE_ADDRESS + os.environ.get("ANALYTICS_SERVICE_PAGE", "/share/85mmF7rx/local")

