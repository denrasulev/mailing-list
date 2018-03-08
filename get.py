import re
import time
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

    # mailing list names are in links with the following format:
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


def get_files_names(url, ml_name):
    """Parse archived file names from specific mailing list"""

    # get requested url
    ml_page = requests.get((url + ml_name))

    # parse html content
    ml_soup = BeautifulSoup(ml_page.content, 'html.parser')

    # init list for files in mailing list
    ml_files = []

    # mailing list files are in links with the following format:
    # <a href="2018-March.txt.gz">[ Gzip'd Text 3 KB ]</a>
    # so we will get all links containing key word '.txt'
    for row in ml_soup.find_all('a', href=re.compile(".txt")):
        ml_files.append(row.get('href'))

    # return list of files in mailing list
    return ml_files


def days_last_modified(file):
    """Return number of days since file was last modified"""

    # get today
    today    = datetime.datetime.today()

    # get time when file was last modified
    mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(file))

    # find difference
    duration = today - mod_date

    # return number of days
    return duration.days


# start
start_time = time.time()

lists_index_page_url = 'https://lists.opendaylight.org/mailman/listinfo'
files_pages_base_url = 'https://lists.opendaylight.org/pipermail/'
update_interval      = 30  # in days

# if lists index file does not exist then create it
if not os.path.exists('data/lists_index.txt'):
    lists_index = get_lists_names(lists_index_page_url)

# if lists index file is older than one month then update it
if days_last_modified('data/lists_index.txt') > 30:
    lists_index = get_lists_names(lists_index_page_url)

# and save lists index file to disk
with open('data/lists_index.txt', 'w') as f:
    f.write('\n'.join(lists_index))

# get list of archived text files for every mailing list
for i in range(len(lists_index)):

    # construct name for individual list of files for every mailing list
    name = 'data/indexes/files_in_' + lists_index[i] + '.txt'

    # if this list of files does not exist or it is older than required:
    if not os.path.exists(name) or days_last_modified(name) > update_interval:

        # get or update it
        ml_files = get_files_names(files_pages_base_url, lists_index[i])

        # and save it to disk
        with open(name, 'w') as f:
            f.write('\n'.join(ml_files))

# inform user on how log did it take
print(f"Done in {(time.time() - start_time)} seconds.")
