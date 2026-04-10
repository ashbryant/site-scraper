import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import zipfile
from PIL import Image
from io import BytesIO

# Change this to your base site
BASE_URL = 'https://www.ssdistribution.co.uk/'

def slugify(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    return path if path else 'home'

def extract_urls_from_local_sitemap(file_path):
    print(f"📂 Reading local sitemap: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Failed to read sitemap file: {e}")
        return []

    soup = BeautifulSoup(content, 'lxml-xml')
    urls = [loc.text.strip() for loc in soup.find_all('loc') if loc.text.startswith(BASE_URL)]
    print(f"✅ Found {len(urls)} URLs in sitemap.")
    return urls

def save_text_and_images(url, base_dir):
    print(f"🛰️ Scraping: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    folder_name = slugify(url)
    page_dir = os.path.join(base_dir, folder_name)
    os.makedirs(page_dir, exist_ok=True)

    # Save readable text content
    texts = soup.stripped_strings
    text_content = '\n'.join(texts)
    with open(os.path.join(page_dir, 'text.txt'), 'w', encoding='utf-8') as f:
        f.write(text_content)

    # Handle image downloading and WebP conversion
    img_dir = os.path.join(page_dir, 'images')
    os.makedirs(img_dir, exist_ok=True)
    webp_dir = os.path.join(img_dir, 'webp')
    os.makedirs(webp_dir, exist_ok=True)

    for img in soup.find_all('img'):
        src = img.get('src')
        if not src:
            continue
        img_url = urljoin(url, src)
        img_name = os.path.basename(urlparse(img_url).path)
        if not img_name:
            continue

        img_path = os.path.join(img_dir, img_name)

        try:
            img_data = requests.get(img_url, timeout=10).content
            # Save original
            with open(img_path, 'wb') as f:
                f.write(img_data)
            # Convert to WebP
            image = Image.open(BytesIO(img_data)).convert('RGB')
            webp_name = os.path.splitext(img_name)[0] + '.webp'
            webp_path = os.path.join(webp_dir, webp_name)
            image.save(webp_path, 'webp')
            print(f"✅ Converted {img_name} → webp/{webp_name}")
        except Exception as e:
            print(f"❌ Failed to handle image {img_url}: {e}")

    # Download linked files (PDFs, Word docs, etc.)
    file_types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
    file_dir = os.path.join(page_dir, 'files')
    os.makedirs(file_dir, exist_ok=True)

    for link in soup.find_all('a', href=True):
        href = link['href']
        if any(href.lower().endswith(ext) for ext in file_types):
            file_url = urljoin(url, href)
            file_name = os.path.basename(urlparse(file_url).path)
            file_path = os.path.join(file_dir, file_name)

            try:
                file_data = requests.get(file_url, timeout=10).content
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                print(f"📥 Downloaded file: {file_name}")
            except Exception as e:
                print(f"❌ Failed to download file {file_url}: {e}")

def zip_dir(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, folder_path)
                zipf.write(full_path, arcname)

if __name__ == "__main__":
    output_folder = "scraped_site"
    Path(output_folder).mkdir(exist_ok=True)

    # Set this to the local path of your sitemap.xml file
    local_sitemap_path = "sitemap.xml"  # change if needed

    pages = extract_urls_from_local_sitemap(local_sitemap_path)

    if not pages:
        print("⚠️ No pages found. Check your sitemap path and content.")
    else:
        for page in pages:
            save_text_and_images(page, output_folder)

        zip_dir(output_folder, 'scraped_site.zip')
        print("\n🎉 All done! Your zipped treasure is ready: scraped_site.zip")