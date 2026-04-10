import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import zipfile
from PIL import Image
from io import BytesIO
import hashlib
from datetime import datetime
from typing import Optional

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────
# CONFIGURATION — edit these values before running
# ─────────────────────────────────────────────────────────────────

# Base URL of the site to scrape
BASE_URL = 'https://www.ssdistribution.co.uk/'

# Path to your local sitemap.xml (relative to this script)
SITEMAP_PATH = 'sitemap.xml'

# Output folder name (relative to this script)
OUTPUT_FOLDER = 'scraped_site'

# Zip output file name
ZIP_OUTPUT = 'scraped_site.zip'

# Delay between page requests in seconds — avoids hammering the server
REQUEST_DELAY = 1.0

# Request timeout in seconds
REQUEST_TIMEOUT = 15

# Convert downloaded images to WebP format as well as saving the original
CONVERT_TO_WEBP = True

# Skip pages whose output folder already exists — allows resuming interrupted runs
SKIP_EXISTING = True

# Download each shared asset (image, file) only once, even if it appears on multiple pages
DEDUPLICATE_ASSETS = True

# Save a Markdown version of each page (page.md) alongside the plain text (text.txt)
SAVE_MARKDOWN = True

# File extensions to download from <a href> links
DOWNLOADABLE_FILE_TYPES = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.ppt', '.pptx', '.txt', '.csv', '.zip',
]

# Video file extensions to download directly from <video>/<source> tags and <a href> links
VIDEO_EXTENSIONS = ['.mp4', '.webm', '.ogg', '.mov', '.avi', '.mkv']

# Browser user-agent sent with every request
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)

# ─────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / OUTPUT_FOLDER
ASSETS_DIR = OUTPUT_DIR / '_assets'
ERROR_LOG   = SCRIPT_DIR / 'errors.log'

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': USER_AGENT})

# Tracks MD5 hashes of downloaded assets to avoid duplicates
_asset_registry: dict[str, Path] = {}

# Summary counters
stats = {
    'pages_scraped':     0,
    'pages_skipped':     0,
    'images':            0,
    'videos_downloaded': 0,
    'videos_logged':     0,
    'files':             0,
    'errors':            0,
}


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def log_error(message: str):
    stats['errors'] += 1
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {message}\n')
    print(f'  ❌ {message}')


def slugify(url: str) -> str:
    """Turn a URL into a safe folder name."""
    path = urlparse(url).path.strip('/')
    return path if path else 'home'


def fetch(url: str) -> Optional[requests.Response]:
    """Fetch a URL, returning the response or None on failure."""
    try:
        response = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response
    except Exception as e:
        log_error(f'Failed to fetch {url}: {e}')
        return None


def save_asset(data: bytes, filename: str, page_dir: Path, subdir: str) -> Optional[Path]:
    """
    Write binary data to disk.
    With DEDUPLICATE_ASSETS enabled, identical files (by MD5) are stored once
    in _assets/ and shared across pages rather than saved multiple times.
    """
    if DEDUPLICATE_ASSETS:
        h = hashlib.md5(data).hexdigest()
        if h in _asset_registry:
            return _asset_registry[h]
        dest_dir = ASSETS_DIR / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        dest_path.write_bytes(data)
        _asset_registry[h] = dest_path
        return dest_path
    else:
        dest_dir = page_dir / subdir
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        dest_path.write_bytes(data)
        return dest_path


# ─────────────────────────────────────────────────────────────────
# SITEMAP
# ─────────────────────────────────────────────────────────────────

def extract_urls_from_local_sitemap(file_path: Path) -> list[str]:
    print(f'📂 Reading sitemap: {file_path}')
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f'❌ Could not read sitemap: {e}')
        return []

    soup = BeautifulSoup(content, 'lxml-xml')
    urls = [
        loc.text.strip()
        for loc in soup.find_all('loc')
        if loc.text.strip().startswith(BASE_URL)
    ]
    print(f'✅ Found {len(urls)} URLs.\n')
    return urls


# ─────────────────────────────────────────────────────────────────
# IMAGES
# ─────────────────────────────────────────────────────────────────

def handle_images(soup: BeautifulSoup, page_url: str, page_dir: Path):
    for img in soup.find_all('img'):
        # Support lazy-loaded images via common data attributes
        src = (
            img.get('src') or
            img.get('data-src') or
            img.get('data-lazy-src') or
            img.get('data-original')
        )
        if not src or src.startswith('data:'):
            continue

        img_url  = urljoin(page_url, src)
        img_name = os.path.basename(urlparse(img_url).path)
        if not img_name or '.' not in img_name:
            continue

        response = fetch(img_url)
        if not response:
            continue

        saved_path = save_asset(response.content, img_name, page_dir, 'images')
        if not saved_path:
            continue

        stats['images'] += 1

        if CONVERT_TO_WEBP:
            try:
                image = Image.open(BytesIO(response.content))
                # Preserve transparency for PNG/GIF; convert everything else to RGB
                mode = 'RGBA' if image.mode in ('RGBA', 'P', 'LA') else 'RGB'
                image = image.convert(mode)
                webp_name = Path(img_name).stem + '.webp'
                if DEDUPLICATE_ASSETS:
                    webp_dir = ASSETS_DIR / 'images' / 'webp'
                else:
                    webp_dir = page_dir / 'images' / 'webp'
                webp_dir.mkdir(parents=True, exist_ok=True)
                image.save(webp_dir / webp_name, 'WEBP')
            except Exception as e:
                log_error(f'WebP conversion failed for {img_url}: {e}')


# ─────────────────────────────────────────────────────────────────
# VIDEOS
# ─────────────────────────────────────────────────────────────────

def handle_videos(soup: BeautifulSoup, page_url: str, page_dir: Path):
    video_log_entries = []

    # Download directly hosted video files from <video src> and <source src>
    for tag in soup.find_all(['video', 'source']):
        src = tag.get('src')
        if not src:
            continue
        video_url = urljoin(page_url, src)
        ext = Path(urlparse(video_url).path).suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            continue

        video_name = os.path.basename(urlparse(video_url).path)
        if not video_name:
            continue

        print(f'  🎬 Downloading video: {video_name}')
        response = fetch(video_url)
        if not response:
            continue

        saved_path = save_asset(response.content, video_name, page_dir, 'videos')
        if saved_path:
            stats['videos_downloaded'] += 1

    # Download video files linked via <a href>
    for link in soup.find_all('a', href=True):
        href = link['href']
        ext = Path(urlparse(href).path).suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            continue

        video_url  = urljoin(page_url, href)
        video_name = os.path.basename(urlparse(video_url).path)
        if not video_name:
            continue

        print(f'  🎬 Downloading linked video: {video_name}')
        response = fetch(video_url)
        if not response:
            continue

        saved_path = save_asset(response.content, video_name, page_dir, 'videos')
        if saved_path:
            stats['videos_downloaded'] += 1

    # Log YouTube and Vimeo embeds (cannot be downloaded directly)
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if 'youtube.com' in src or 'youtu.be' in src:
            video_log_entries.append(f'YouTube: {src}')
            stats['videos_logged'] += 1
        elif 'vimeo.com' in src:
            video_log_entries.append(f'Vimeo: {src}')
            stats['videos_logged'] += 1

    if video_log_entries:
        log_path = page_dir / 'video_links.txt'
        log_path.write_text('\n'.join(video_log_entries), encoding='utf-8')
        print(f'  📋 Logged {len(video_log_entries)} embedded video URL(s) → video_links.txt')


# ─────────────────────────────────────────────────────────────────
# DOWNLOADABLE FILES
# ─────────────────────────────────────────────────────────────────

def handle_files(soup: BeautifulSoup, page_url: str, page_dir: Path):
    for link in soup.find_all('a', href=True):
        href = link['href']
        ext  = Path(urlparse(href).path).suffix.lower()
        if ext not in DOWNLOADABLE_FILE_TYPES:
            continue

        file_url  = urljoin(page_url, href)
        file_name = os.path.basename(urlparse(file_url).path)
        if not file_name:
            continue

        response = fetch(file_url)
        if not response:
            continue

        saved_path = save_asset(response.content, file_name, page_dir, 'files')
        if saved_path:
            stats['files'] += 1
            print(f'  📥 Downloaded file: {file_name}')


# ─────────────────────────────────────────────────────────────────
# MARKDOWN EXPORT
# ─────────────────────────────────────────────────────────────────

def html_to_markdown(soup: BeautifulSoup, page_url: str) -> str:
    """
    Produce a clean, readable Markdown version of the page.
    Preserves headings, paragraphs, lists, and links.
    """
    lines = []

    title = soup.find('title')
    if title:
        lines.append(f'# {title.get_text(strip=True)}\n')

    lines.append(f'**URL:** {page_url}\n')
    lines.append('---\n')

    heading_map = {'h1': '#', 'h2': '##', 'h3': '###', 'h4': '####', 'h5': '#####', 'h6': '######'}

    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
        text = tag.get_text(strip=True)
        if not text:
            continue

        if tag.name in heading_map:
            lines.append(f'\n{heading_map[tag.name]} {text}\n')
        elif tag.name == 'p':
            lines.append(f'\n{text}\n')
        elif tag.name == 'li':
            lines.append(f'- {text}')

    # Collect all unique links at the bottom
    links = []
    for a in soup.find_all('a', href=True):
        text = a.get_text(strip=True)
        href = urljoin(page_url, a['href'])
        if text and href.startswith('http'):
            links.append(f'- [{text}]({href})')

    if links:
        lines.append('\n---\n')
        lines.append('## Links\n')
        lines.extend(dict.fromkeys(links))  # deduplicate while preserving order

    return '\n'.join(lines)


# ─────────────────────────────────────────────────────────────────
# PAGE SCRAPER
# ─────────────────────────────────────────────────────────────────

def scrape_page(url: str):
    page_dir = OUTPUT_DIR / slugify(url)

    if SKIP_EXISTING and page_dir.exists():
        print(f'  ⏭️  Skipping (already scraped): {url}')
        stats['pages_skipped'] += 1
        return

    print(f'🛰️  Scraping: {url}')
    response = fetch(url)
    if not response:
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    page_dir.mkdir(parents=True, exist_ok=True)

    # Plain text dump
    text_content = '\n'.join(soup.stripped_strings)
    (page_dir / 'text.txt').write_text(text_content, encoding='utf-8')

    # Markdown version
    if SAVE_MARKDOWN:
        md_content = html_to_markdown(soup, url)
        (page_dir / 'page.md').write_text(md_content, encoding='utf-8')

    handle_images(soup, url, page_dir)
    handle_videos(soup, url, page_dir)
    handle_files(soup, url, page_dir)

    stats['pages_scraped'] += 1


# ─────────────────────────────────────────────────────────────────
# ZIP + SUMMARY
# ─────────────────────────────────────────────────────────────────

def zip_dir(folder_path: Path, output_path: Path):
    print(f'\n📦 Zipping output → {output_path.name} ...')
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = Path(root) / file
                arcname   = full_path.relative_to(folder_path)
                zipf.write(full_path, arcname)


def print_summary():
    print('\n' + '─' * 50)
    print('✅  Scrape complete!')
    print(f'    Pages scraped:       {stats["pages_scraped"]}')
    print(f'    Pages skipped:       {stats["pages_skipped"]}')
    print(f'    Images saved:        {stats["images"]}')
    print(f'    Videos downloaded:   {stats["videos_downloaded"]}')
    print(f'    Video URLs logged:   {stats["videos_logged"]}')
    print(f'    Files downloaded:    {stats["files"]}')
    print(f'    Errors:              {stats["errors"]}')
    if stats['errors'] > 0:
        print(f'    → See errors.log for details')
    print('─' * 50 + '\n')


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    OUTPUT_DIR.mkdir(exist_ok=True)
    if DEDUPLICATE_ASSETS:
        ASSETS_DIR.mkdir(exist_ok=True)

    sitemap_file = SCRIPT_DIR / SITEMAP_PATH
    pages = extract_urls_from_local_sitemap(sitemap_file)

    if not pages:
        print('⚠️  No pages found. Check SITEMAP_PATH and BASE_URL in the config section.')
    else:
        iterator = tqdm(pages, desc='Scraping pages', unit='page') if TQDM_AVAILABLE else pages
        for page_url in iterator:
            scrape_page(page_url)
            time.sleep(REQUEST_DELAY)

        zip_dir(OUTPUT_DIR, SCRIPT_DIR / ZIP_OUTPUT)
        print_summary()
