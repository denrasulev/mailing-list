# Script to scrape, parse and save all information from e-mails in the
# OpenDaylight mailing lists: https://lists.opendaylight.org
# (c) 2018 Denis Rasulev
# Bratislava, Slovakia

import re
# import pdb
import gzip
import time
import os.path
import requests
import datetime
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup


def get_lists_names(url):
    """Parse mailing lists names from provided URL."""

    # get requested url
    try:
        r = requests.get(url, timeout=3)
    except requests.exceptions.RequestException as e:
        print(e)

    # parse html content
    soup = BeautifulSoup(r.content, 'html.parser')

    # init list for the names of mailing lists
    mailing_lists = []

    # mailing list names have the following format in links:
    # <a href="listinfo/aaa-dev"><strong>aaa-dev</strong></a>
    # so we will get all links containing key word 'listinfo'
    for row in soup.find_all('a', href=re.compile("listinfo")):

        # split acquired string by symbol '/' and return only last part
        text = row.get('href').partition('/')[2]

        # check it's not empty and append it to the list of lists
        if len(text) > 0:
            mailing_lists.append(text)

    # return list of mailing lists names
    return mailing_lists


def get_files_names(url, list_name):
    """Parse archived file names from a specific mailing list."""

    # get requested url
    try:
        r = requests.get((url + list_name))
    except requests.exceptions.RequestException as e:
        print(e)

    # parse html content
    soup = BeautifulSoup(r.content, 'html.parser')

    # init list for files in a mailing list
    mlist_files = []

    # mailing list file names have the following format in links:
    # <a href="2018-March.txt.gz">[ Gzip'd Text 3 KB ]</a>
    # so we will get all links containing key word '.txt'
    for row in soup.find_all('a', href=re.compile(".txt")):
        mlist_files.append(row.get('href'))

    # return list of files in mailing list
    return mlist_files


def days_last_modified(file_name):
    """Return number of days since file was last modified."""

    # get today
    today    = datetime.datetime.today()

    # get time when file was last modified
    mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_name))

    # find difference
    duration = today - mod_date

    # return number of days
    return duration.days


def parse_txt(file_name):

    data = []

    sndr = ''
    date = ''
    subj = ''
    repl = ''
    m_id = ''
    text = ''

    rx_mark = re.compile(r'From ')
    rx_from = re.compile(r'From: (.*)')
    rx_date = re.compile(r'Date: (.*)')
    rx_subj = re.compile(r'Subject: (.*)')
    rx_repl = re.compile(r'In-Reply-To: (.*)')
    rx_m_id = re.compile(r'Message-ID: (.*)')

    with open(file_name, 'r', encoding='utf-8') as f:

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
                    line = next(f, None)
                    if line is None:
                        break
                    text.append(line)

                message = {
                    'From': sndr,
                    'Date': date,
                    'Subj': subj,
                    'Rply': repl,
                    'M_id': m_id,
                    'Text': text
                }

                data.append(message)

            line = next(f, None)

        data = pd.DataFrame(data)

    return data


def parse_gz(file_name):

    data = []

    sndr = ''
    date = ''
    subj = ''
    repl = ''
    m_id = ''
    text = ''

    rx_mark = re.compile(r'From ')
    rx_from = re.compile(r'From: (.*)')
    rx_date = re.compile(r'Date: (.*)')
    rx_subj = re.compile(r'Subject: (.*)')
    rx_repl = re.compile(r'In-Reply-To: (.*)')
    rx_m_id = re.compile(r'Message-ID: (.*)')

    with gzip.open(file_name, 'rt', encoding='utf-8') as f:

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
                    line = next(f, None)
                    if line is None:
                        break
                    text.append(line)

                message = {
                    'From': sndr,
                    'Date': date,
                    'Subj': subj,
                    'Rply': repl,
                    'M_id': m_id,
                    'Text': text
                }

                data.append(message)

            line = next(f, None)

        data = pd.DataFrame(data)

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
    lists_names = get_lists_names(lists_names_url)

    # and save it to disk
    with open(lindex, 'w') as f:
        f.write('\n'.join(lists_names))


# if lists index file is ok (exists, size > 0, fresh) then read it
f = open(lindex, 'r')
lists_names = f.readlines()
lists_names = [s.rstrip() for s in lists_names]

# for every mailing list name get list of archived text files in it
for i in range(len(lists_names)):

    # construct name for individual list of files in every mailing list
    name = 'data/indexes/' + lists_names[i] + '.txt'

    # if this list of files does not exist or is older than period:
    if not os.path.exists(name) or days_last_modified(name) > period:

        # then get it or update it
        mlist_files = get_files_names(lists_files_url, lists_names[i])

        # and save it to disk
        with open(name, 'w') as f:
            f.write('\n'.join(mlist_files))

    # if list of files in a mailing list is ok then read it
    f = open(name, 'r')
    mlist_files = f.readlines()
    mlist_files = [s.rstrip() for s in mlist_files]

    # construct directory name for a certain mailing list
    mlist_directory = f_path + lists_names[i] + '/'

    # if directory does not exist, then create it
    if not os.path.exists(os.path.dirname(mlist_directory)):
        os.makedirs(os.path.dirname(mlist_directory))

    # for every file name in this list
    for j in range(len(mlist_files)):

        # construct file path
        file_name = mlist_directory + mlist_files[j]

        # if this file does not exist already, then download and save it
        if not os.path.exists(file_name):
            url = lists_files_url + lists_names[i] + '/' + mlist_files[j]
            urllib.request.urlretrieve(url, file_name)

# close index file
f.close()


print('Start processing all files...')

# init dataframe for all mails
all_mails = pd.DataFrame(columns=['Date', 'From', 'M_id',
                                  'Rply', 'Subj', 'Text'])

# parse every file in the directories
for root, dirs, files in os.walk('data/texts'):
    for file in files:
        print('Processing file: ', file)
        # pdb.set_trace()
        ext = os.path.splitext(file)[1]
        if ext == '.gz':
            t = parse_gz(os.path.join(root, file))
            all_mails = all_mails.append(t)
        elif ext == '.txt':
            t = parse_txt(os.path.join(root, file))
            all_mails = all_mails.append(t)
        else:
            continue

print('Done... Saving to file.')

# save to file
all_mails.to_csv('mails.tsv', sep='\t', encoding='utf-8')


# show how long did it take
diff = time.time() - start_time
m, s = divmod(diff, 60)
h, m = divmod(m, 60)
print(f'Done in {int(h):02d}h {int(m):02d}m {s:05.2f}s.')
