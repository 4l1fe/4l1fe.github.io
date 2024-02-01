import os
from pathlib import Path

SITE_NAME = 'ТехнологоблогЪ'
SITE_ADDRESS = 'https://www.kvdm.dev'

PROJ_DIR = Path(__file__).parent.parent
BUILD_DIR = PROJ_DIR / 'src'
DOCS_DIR = PROJ_DIR / 'docs'
DOCS_ARTICLES_DIR = DOCS_DIR / 'articles'
DOCS_FILES_DIR = DOCS_DIR / 'files'
VIEWS_DIR = DOCS_DIR / 'views'
TEMPLATES_DIR = BUILD_DIR / 'templates'
THUMBNAILS_DIR = Path('thumbnails')
ARTICLE_FILES_DIR = Path('files')
DISK_CACHE_DIR = PROJ_DIR / '.cache'
ARTICLE_TEMPLATE_FILE = TEMPLATES_DIR / 'article.jinja'
INDEX_TEMPLATE_FILE = TEMPLATES_DIR / 'index.jinja'
SITEMAP_TEMPLATE_FILE = TEMPLATES_DIR / 'sitemap.jinja'
RSS_TEMPLATE_FILE = TEMPLATES_DIR / 'rss.jinja'
DOCS_INDEX_FILE = DOCS_DIR / 'index.html'
SITEMAP_FILE = DOCS_DIR / 'sitemap.xml'
RSS_FILE = DOCS_DIR / 'rss.xml'
ARTICLE_IMG_FILE = ARTICLE_FILES_DIR / 'main-section.png'
AS_DIRS_IGNORE = ('drafts', )

TRACK_ANALYTICS = False
ANALYTICS_ENABLED_DEFAULT = False
ANALYTICS_SERVICE_ADDRESS = os.environ.get("ANALYTICS_SERVICE_ADDRESS", "")
ANALYTICS_SERVICE_TOKEN = os.environ.get("ANALYTICS_SERVICE_TOKEN", "")
ANALYTICS_SERVICE_JS = ANALYTICS_SERVICE_ADDRESS + "/umami.js"
ANALYTICS_SERVICE_PAGE = ANALYTICS_SERVICE_ADDRESS + os.environ.get("ANALYTICS_SERVICE_PAGE", "")

MONITORING_ENABLED_DEFAULT = False
MONITORING_SERVICE_ADDRESS = os.environ.get("MONITORING_SERVICE_ADDRESS", "")
MONITORING_SERVICE_PAGE = MONITORING_SERVICE_ADDRESS + os.environ.get("MONITORING_SERVICE_PAGE", "")

MEMOCARDS_ENABLED_DEFAULT = False
MEMOCARDS_SERVICE_ADDRESS = os.environ.get("MEMOCARDS_SERVICE_ADDRESS", "")

ENGQA_ENABLED_DEFAULT = False
ENGQA_SERVICE_ADDRESS = os.environ.get("ENGQA_SERVICE_ADDRESS", "")

STATUSPAGE_ENABLED_DEFAULT = False
STATUSPAGE_SERVICE_ADDRESS = os.environ.get("STATUSPAGE_SERVICE_ADDRESS", "")

OPENAI_KEY_FILE = os.environ.get('OPENAI_KEY_FILE')
HUGGINGFACE_KEY_FILE = os.environ.get('HUGGINGFACE_KEY_FILE')
