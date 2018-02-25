import requests
from bs4 import BeautifulSoup

# get list of all mailing lists in opendaylight project
lists_page = 'https://lists.opendaylight.org/mailman/listinfo'

page = requests.get(lists_page)
if page.status_code == '200':
    cont = page.content

soup = BeautifulSoup(cont, 'html.parser')

all_lists = []
for row in soup.find_all('a'):
    text = row.get('href').partition('/')[2]
    if len(text) > 0:
        print(text)
        all_lists.append(text)

with open('lists.txt', 'w') as f:
    f.write(all_lists)

# get texts for every list
base = 'https://lists.opendaylight.org/pipermail/'

# scrape list page and get month-year for latest archive on page
# check if we have all files in some cache directory
# download all missing files
