from pathlib import Path


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