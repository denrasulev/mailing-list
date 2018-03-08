import re
import time
import random
import os.path
import requests
import datetime
from bs4 import BeautifulSoup


def get_lists_names(url):
    """Parse mailing lists names from URL"""

    # get requested url
    page = requests.get(url)

    # parse html content
    soup = BeautifulSoup(page.content, 'html.parser')

    # init list for names of mailing lists
    mailing_lists = []

    # mailing list names are in links with following format:
    # <a href="listinfo/aaa-dev"><strong>aaa-dev</strong></a>
    # so we will get all links containing key word 'listinfo'
    for row in soup.find_all('a', href=re.compile("listinfo")):

        # split acquired string by symbol '/' and return only last part
        text = row.get('href').partition('/')[2]

        # check that it's not empty and then add it to our list of lists
        if len(text) > 0:
            mailing_lists.append(text)

    # return list of mailing lists names
    return mailing_lists


def days_last_modified(file):
    """Get number of days when file was last modified"""
    today    = datetime.datetime.today()
    mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(file))
    duration = today - mod_date
    return duration.days


lists_index_page = 'https://lists.opendaylight.org/mailman/listinfo'

# if lists index file does not exist then create it
if not os.path.exists('data/lists_index.txt'):
    lists_index = get_lists_names(lists_index_page)

# if lists index file is older than one month then update it
if days_last_modified('data/lists_index.txt') > 30:
    lists_index = get_lists_names(lists_index_page)

# save lists index file to disk
with open('data/lists_index.txt', 'w') as f:
    f.write('\n'.join(lists_index))


# get texts for every list
base = 'https://lists.opendaylight.org/pipermail/'

for i in range(0, len(lists_index)):
    ml_index_page = base + lists_index[i]
    ml_page = requests.get(ml_index_page)
    ml_soup = BeautifulSoup(ml_page.content, 'html.parser')

    ml_files = []
    for row in ml_soup.find_all('a', href=re.compile(".txt")):
        ml_files.append(row.get('href'))

    # save them to disk
    name = 'data/indexes/files_in_' + lists_index[i] + '.txt'
    with open(name, 'w') as f:
        f.write('\n'.join(ml_files))

    time.sleep(random.randrange(5, 15))
