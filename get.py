import re
import time
import random
import requests
from bs4 import BeautifulSoup

# TODO: if no lists.txt or size is 0, get all mailing lists names
# TODO: if lists.txt is older than one month - refresh list names

# get list of all mailing lists in opendaylight project
lists_index_page = 'https://lists.opendaylight.org/mailman/listinfo'

# get list of all mailing lists available
page = requests.get(lists_index_page)

# parse page content
soup = BeautifulSoup(page.content, 'html.parser')

# get only names of mailing lists
all_lists = []
for row in soup.find_all('a'):
    text = row.get('href').partition('/')[2]
    if len(text) > 0:
        all_lists.append(text)

# save them to disk
with open('lists.txt', 'w') as f:
    f.write('\n'.join(all_lists))

# get texts for every list
base = 'https://lists.opendaylight.org/pipermail/'

for i in range(0, len(all_lists)):
    ml_index_page = base + all_lists[i]
    ml_page = requests.get(ml_index_page)
    ml_soup = BeautifulSoup(ml_page.content, 'html.parser')

    ml_files = []
    for row in ml_soup.find_all('a', href=re.compile(".txt")):
        text = row.get('href')
        if len(text) > 0:
            ml_files.append(text)

    # save them to disk
    name = 'files_for_' + all_lists[i] + '.txt'
    with open(name, 'w') as f:
        f.write('\n'.join(ml_files))

    time.sleep(random.randrange(2, 5))

# scrape list page and get month-year for latest archive on page
# check if we have all files in some cache directory
# download all missing files
