README - Running scrape_site_v2.py on Mac

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
Step 4 - Install dependencies (first time only)
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
Step 5 - Add your sitemap
─────────────────────────────────────────
Place your sitemap.xml file in the same folder as the script.
Download it from: https://yoursite.com/sitemap.xml


─────────────────────────────────────────
Step 6 - Set your base URL
─────────────────────────────────────────
Open scrape_site_v2.py in a text editor and update the BASE_URL
at the top of the file to match your site:

    BASE_URL = 'https://www.yoursite.com/'


─────────────────────────────────────────
Step 7 - Run the script
─────────────────────────────────────────
Run:
    python3 scrape_site_v2.py

Output will be saved to a "scraped_site" folder and zipped
into "scraped_site.zip" when complete.


─────────────────────────────────────────
Troubleshooting
─────────────────────────────────────────
- If you see "ModuleNotFoundError", re-run Step 4.
- If a page fails to download, check errors.log in the script folder.
- If you stop the script partway through, just run it again —
  it will skip pages already scraped and pick up where it left off.
