import os


class CacheManager:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get(self, url):
        filename = self._get_filename(url)
        if os.path.exists(filename):
            return filename
        return None

    def set(self, url, image_path):
        filename = self._get_filename(url)
        os.rename(image_path, filename)

    def _get_filename(self, url):
        return os.path.join(
            self.cache_dir, f"{url.replace('://', '_').replace('/', '_')}.png"
        )
