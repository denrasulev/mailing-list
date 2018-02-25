from urllib.request import urlopen
from bs4 import BeautifulSoup as bs

# get list of all mailing lists in opendaylight project
lists_page = 'https://lists.opendaylight.org/mailman/listinfo'

page = urlopen(lists_page)
soup = bs(page, 'html.parser')

all_lists = []
for row in soup.find_all('a'):
    all_lists.append(row.get('href').partition('/')[2])

with open('lists.txt', 'w') as f:
    f.write(all_lists)

# get texts for every list
base = 'https://lists.opendaylight.org/pipermail/'

# scrape list page and get month-year for latest archive on page
# check if we have all files in some cache directory
# download all missing files
