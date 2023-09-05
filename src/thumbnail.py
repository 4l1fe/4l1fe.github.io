from PIL import Image
from diskcache import Cache

from constants import DISK_CACHE_DIR, ARTICLE_IMG_FILE


cache = Cache(DISK_CACHE_DIR)


@cache.memoize()
def create_thumbnail(source_image_path, thumbnail_path):
    im = Image.open(source_image_path)
    copied = im.copy()
    is_cover = False if source_image_path.name != ARTICLE_IMG_FILE else True
    size = (128, 128) if not is_cover else (256, 256)
    copied.thumbnail(size, Image.LANCZOS)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    copied.save(thumbnail_path, quality=95)

