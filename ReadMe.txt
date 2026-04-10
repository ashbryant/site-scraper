README - Running scrape_site.py on Mac

Step 1 - Open Terminal
- Use Spotlight (Cmd + Space) and type 'Terminal'.
- Hit Enter.

Step 2 - Check Python Installation
Run:
python3 --version
You should see something like 'Python 3.x.x'.
If you don’t, you need to install Python from https://www.python.org/downloads/

Step 3 - Go to Script’s Location
Navigate to the folder where you saved 'scrape_site_markdown.py'. For example:
cd /path/to/your/script
Tip: You can drag and drop the folder into the terminal to fill in the path automatically.

Step 4 - Run the Script
Run:
python3 scrape_site.py

Step 5 - Install Missing Modules (If Needed)
If you see an error like:
ModuleNotFoundError: No module named 'requests'
Install the missing package:
pip3 install requests
Then re-run the script.