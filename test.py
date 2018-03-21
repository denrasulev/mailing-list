# OpenDaylight mailing lists processor.
# Scrapes, parses and analyzes info.
# https://lists.opendaylight.org
# (c) 2018 Denis Rasulev
# Bratislava, Slovakia

import re
import gzip
import time
import os.path
import requests
import datetime
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch


def get_lists_from_url(url):
    """Parse mailing lists names from provided URL."""
    try:
        r = requests.get(url, timeout=3)
    except requests.exceptions.RequestException as e:
        print(e)

    # parse html content
    soup = BeautifulSoup(r.content, 'html.parser')

    # list for the names of mailing lists
    mailing_lists = []

    # mailing list names have the following format in html:
    # <a href="listinfo/aaa-dev"><strong>aaa-dev</strong></a>
    # so we will get all links containing key word 'listinfo'
    for row in soup.find_all('a', href=re.compile("listinfo")):

        # split acquired string by symbol '/' and get last part (name)
        text = row.get('href').partition('/')[2]

        # check that it's not empty and append it to the list of lists
        if len(text) > 0:
            mailing_lists.append(text)

    # return list of mailing lists names
    return mailing_lists


def get_files_from_list(url, list_name):
    """Parse archived file names from a specific mailing list."""
    try:
        r = requests.get((url + list_name))
    except requests.exceptions.RequestException as e:
        print(e)

    # parse html content
    soup = BeautifulSoup(r.content, 'html.parser')

    # list for files in a mailing list
    mlist_files = []

    # mailing list file names have the following format:
    # <a href="2018-March.txt.gz">[ Gzip'd Text 3 KB ]</a>
    # so we will get all links containing key word '.txt'
    for row in soup.find_all('a', href=re.compile(".txt")):
        mlist_files.append(row.get('href'))

    # return list of files in mailing list
    return mlist_files


def days_last_modified(file_name):
    """Return number of days since file was last modified."""
    today = datetime.datetime.today()

    # get time when file was last modified
    mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_name))

    # find difference
    duration = today - mod_date

    # return number of days
    return duration.days


def clean(text):
    """Clean text from anything but words"""

    # regex for any non-word character
    rx_clean = re.compile(r'\W+_*')

    cleaned = []

    # for every element in text
    for each in text:

        # replace non-word char with space and strip \n\r from the end
        each = rx_clean.sub(' ', each).strip()

        # if result is not empty, i.e. '' then append it to list
        if len(each) > 0:
            cleaned.append(each)
        else:
            continue

    # return list of words only
    return cleaned


# TODO - parse must only do parsing!
# TODO - no walking by directories
# TODO - no saving to elasticsearch
def parse(file_name, list_name):
    """Parse unstructured text information"""
    es = Elasticsearch()
    data = []

    sndr = ''
    date = ''
    subj = ''
    repl = ''

    # regexes to search for required elements
    rx_mark = re.compile(r'From ')
    rx_from = re.compile(r'From: (.*)')
    rx_date = re.compile(r'Date: (.*)')
    rx_subj = re.compile(r'Subject: (.*)')
    rx_repl = re.compile(r'In-Reply-To: (.*)')
    rx_m_id = re.compile(r'Message-ID: (.*)')

    # get file extension
    ext = os.path.splitext(file_name)[1]

    # use appropriate method, gzip.open for .gz files, open for .txt
    with (gzip.open if ext == ".gz" else open)(file_name, 'rt',
                                               encoding='utf-8') as f:

        line = next(f)

        while line:

            if rx_from.match(line):
                sndr = rx_from.match(line).group(1)

            if rx_date.match(line):
                date = rx_date.match(line).group(1)

            if rx_subj.match(line):
                subj = rx_subj.match(line).group(1)

            if rx_repl.match(line):
                repl = rx_repl.match(line).group(1)

            if rx_m_id.match(line):
                m_id = rx_m_id.match(line).group(1)

                text = []
                while not rx_mark.match(line):
                    if line is None:
                        break
                    text.append(line)
                    line = next(f, None)

                # text cleaning
                text = clean(text)

                message = {
                    'List': list_name,
                    'From': sndr,
                    'Date': date,
                    'Subj': subj,
                    'Rply': repl,
                    'M_id': m_id,
                    'Text': text
                }

                # TODO - check how to index fields with processing?
                es.index(index="mails", doc_type='message',
                         id=m_id, body=message)

                data.append(message)

            line = next(f, None)

        f.close()

        data = pd.DataFrame(data)

    # return pandas data frame with sctructured information
    return data


# start
start_time = time.time()


# set base parameters
lists_names_url = 'https://lists.opendaylight.org/mailman/listinfo'
lists_files_url = 'https://lists.opendaylight.org/pipermail/'
lindex = 'data/lists_names.txt'
f_path = 'data/texts/'
period = 30  # in days


# if lists index file doesn't exist or size is 0 or is older than period
if not os.path.exists(lindex) or os.path.getsize(lindex) == 0 or \
   days_last_modified(lindex) > period:

    # then create it or update it
    lists_names = get_lists_from_url(lists_names_url)

    # and save it to disk
    with open(lindex, 'w') as f:
        f.write('\n'.join(lists_names))


# if lists index file is ok (exists, size > 0, fresh) then read it
f = open(lindex, 'r')
lists_names = f.readlines()
lists_names = [s.rstrip() for s in lists_names]

# for every mailing list name get list of archived text files in it
for list_name in lists_names:

    # construct name for individual list of files in every mailing list
    name = 'data/indexes/' + list_name + '.txt'

    # if this list of files does not exist or is older than period:
    if not os.path.exists(name) or days_last_modified(name) > period:

        # then get it or update it
        mlist_files = get_files_from_list(lists_files_url, list_name)

        # and save it to disk
        with open(name, 'w') as f:
            f.write('\n'.join(mlist_files))

    # if list of files in a mailing list is ok then read it
    f = open(name, 'r')
    mlist_files = f.readlines()
    mlist_files = [s.rstrip() for s in mlist_files]

    # construct directory name for a certain mailing list
    mlist_dir = f_path + list_name + '/'

    # if directory does not exist, then create it
    if not os.path.exists(os.path.dirname(mlist_dir)):
        os.makedirs(os.path.dirname(mlist_dir))

    # for every file name in this list
    for mlist_file in mlist_files:

        # if this file does not exist already, then download and save it
        if not os.path.exists(mlist_dir + mlist_file):
            url = lists_files_url + list_name + '/' + mlist_file
            urllib.request.urlretrieve(url, (mlist_dir + mlist_file))

# close index file
f.close()


print('Start processing all files...')


# init data frame for all mails
all_mails = pd.DataFrame(columns=['List', 'Date', 'From', 'M_id',
                                  'Rply', 'Subj', 'Text'])

# parse every file in the directories
for root, dirs, files in os.walk('data/texts'):
    for file in files:
        print('Processing file:', os.path.join(root, file))

        # get file extension to process only required files
        ext = os.path.splitext(file)[1]

        if ext == '.gz' or ext == '.txt':
            # get list name to pass and add to structured list
            list_name = root.split('/')[2]

            message = parse(os.path.join(root, file), list_name)
            all_mails = all_mails.append(message)

        else:
            continue

print('All files processed. Saving result to file...')

# save to file(s)
all_mails.to_csv('mails.tsv', sep='\t', encoding='utf-8')


# show how long did it take
diff = time.time() - start_time
m, s = divmod(diff, 60)
h, m = divmod(m, 60)
print(f'All tasks completed in {int(h):02d}h {int(m):02d}m {s:05.2f}s.')
