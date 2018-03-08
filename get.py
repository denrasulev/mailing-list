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

# set base parameters
lists_index_page_url = 'https://lists.opendaylight.org/mailman/listinfo'
files_pages_base_url = 'https://lists.opendaylight.org/pipermail/'
lindex = 'data/lists_index.txt'
period = 30  # in days

# if lists index file doesn't exist or size is 0 or is older than period
if not os.path.exists(lindex) or os.path.getsize(lindex) == 0 or \
   days_last_modified(lindex) > period:

    # then create it or update it
    lists_index = get_lists_names(lists_index_page_url)

    # and save it to disk
    with open(lindex, 'w') as f:
        f.write('\n'.join(lists_index))

# read mailing lists index file
f = open(lindex, 'r')
lists_index = f.readlines()
lists_index = [s.rstrip() for s in lists_index]

# for every mailing list get list of archived text files in it
for i in range(len(lists_index)):

    # construct name for individual list of files for every mailing list
    name = 'data/indexes/files_in_' + lists_index[i] + '.txt'

    # if this list of files does not exist or it is older than required:
    if not os.path.exists(name) or days_last_modified(name) > period:

        # get or update it
        ml_files = get_files_names(files_pages_base_url, lists_index[i])

        # and save it to disk
        with open(name, 'w') as f:
            f.write('\n'.join(ml_files))

# close index file
f.close()

# inform user on how long did it take
print(f"Done in {(time.time() - start_time):1.2f} second(s).")
