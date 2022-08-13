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
GOOGLE_VERF_TOKEN = 'utO5yk8RwIXZ-_rnxq_xpMndgtw0MU_VqtE61lNmjsY'
SITE_NAME = 'ТехнологоблогЪ'
SITE_ADDRESS = 'https://www.4l1fe.dev'
ANALYTICS_SERVICE_ADDRESS = "https://analytics.4l1fe.dev:23387"
ANALYTICS_SERVICE_TOKEN = "216025c7-b209-4e65-83f5-35be37d0604b"
ANALYTICS_SERVICE_JS = ANALYTICS_SERVICE_ADDRESS + "/umami.js"
ANALYTICS_SERVICE_PAGE = ANALYTICS_SERVICE_ADDRESS + "/share/MwnSQ7JH/4l1fe-dev"

