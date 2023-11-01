#
# Simple app to find out what is the latest and greatest released stable Google Chrome web browser.
#
from urllib import request
from bs4 import BeautifulSoup

_chrome_versions_url = "https://googlechromelabs.github.io/chrome-for-testing/#stable"
_chrome_version = "latest"

# Read the web page into memory:
_html=request.urlopen(_chrome_versions_url)
soup=BeautifulSoup(_html, "html.parser")
# Find all "div" elements in the web page that have the "summary" class set.
# This is the rolled up version info table:
section=soup.find('div', attrs={"class": "summary"})
if not section:
    print("Section not found that has the table with stable version information!")
else:
    table=section.find("table")
    table_body=table.find("tbody")
    print(f"Table: {table.contents}")
    # Find all the rows in the table that have the "status-ok" class set.
    # These are the current releases, exluding upcoming versions:
    rows=table_body.findAll('tr', attrs={"class": "status-ok"}, recursive=True)
    print(f"{len(rows)} rows")
    for row in rows:
        print(f"\nrow: {row}")
        if row.find('a').contents[0] == "Stable":
            print("Found it!")
            _chrome_version=row.find('code').contents[0]
            print(f"version: {_chrome_version}")
            break
