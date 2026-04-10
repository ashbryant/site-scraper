README - Running scrape_site.py on Mac

─────────────────────────────────────────
Step 1 - Open Terminal
─────────────────────────────────────────
Use Spotlight (Cmd + Space), type Terminal, hit Enter.


─────────────────────────────────────────
Step 2 - Check Python is installed
─────────────────────────────────────────
Run:
    python3 --version

You should see something like "Python 3.x.x".
If not, download Python from https://www.python.org/downloads/


─────────────────────────────────────────
Step 3 - Navigate to the script folder
─────────────────────────────────────────
Run:
    cd /path/to/your/script

Tip: drag and drop the folder into Terminal to fill in the path automatically.


─────────────────────────────────────────
Step 4 - Install Python dependencies (first time only)
─────────────────────────────────────────
Run:
    pip3 install -r requirements.txt

This installs everything the script needs in one go:
  - requests       (fetches web pages)
  - beautifulsoup4 (parses HTML)
  - lxml           (XML parser for sitemaps)
  - Pillow         (image processing + WebP conversion)
  - tqdm           (progress bar)


─────────────────────────────────────────
Step 4b - Install ffmpeg (for video conversion, first time only)
─────────────────────────────────────────
The script converts downloaded videos to WebM format using ffmpeg.
If you don't have ffmpeg installed, run:

    brew install ffmpeg

If you don't have Homebrew:
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

If you'd rather skip video conversion, open scrape_site.py and set:
    CONVERT_TO_WEBM = False


─────────────────────────────────────────
Step 5 - Add your sitemap
─────────────────────────────────────────
Place your sitemap.xml file in the same folder as the script.
The script will automatically detect the site's domain from it.


─────────────────────────────────────────
Step 6 - Run the script
─────────────────────────────────────────
Run:
    python3 scrape_site.py

Output will be saved to a "scraped_site" folder and zipped
into "scraped_site.zip" when complete.


─────────────────────────────────────────
Troubleshooting
─────────────────────────────────────────
- If you see "ModuleNotFoundError", re-run Step 4.
- If you see "ffmpeg not found", run Step 4b (or set CONVERT_TO_WEBM = False).
- If a page fails to download, check errors.log in the script folder.
- If you stop the script partway through, just run it again —
  it will skip pages already scraped and pick up where it left off.
