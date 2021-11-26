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
SITE_ADDRESS = 'https://4l1fe.github.io'
