# OpenDaylight mailing lists processor.
# Scrapes, parses and analyzes info.
# https://lists.opendaylight.org
# (c) 2018 Denis Rasulev
# Bratislava, Slovakia

import re
import os
import gzip
import time
import requests
import datetime
import pandas as pd
import urllib.request
from bs4 import BeautifulSoup
from requests import Response


def get_lists_from_url(url):
    """Parse mailing lists names from provided URL."""
    # try:
    #     r: Response = requests.get(url, timeout=3)
    # except requests.exceptions.RequestException as e:
    #     print(e)

    r: Response = requests.get(url, timeout=3)

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


def get_files_from_list(list_name_with_url):
    # """Parse file names from a specific mailing list."""

    # try:
    #     r: Response = requests.get(list_name_with_url, timeout=3)
    # except requests.exceptions.RequestException as e:
    #     print(e)

    r: Response = requests.get(list_name_with_url, timeout=3)

    # parse html content
    soup = BeautifulSoup(r.content, 'html.parser')

    # init list for files in mailing list
    list_files = []

    # mailing list file names are in the following format:
    # <a href="2018-March.txt.gz">[ Gzip'd Text 3 KB ]</a>
    # so we will get all links containing key word '.txt'
    for row in soup.find_all('a', href=re.compile(".txt")):
        list_files.append(row.get('href'))

    # return list of files in mailing list
    return list_files


def days_last_modified(f_name):
    """Return number of days since file was last modified."""
    today = datetime.datetime.today()

    # get time when file was last modified
    mod_date = datetime.datetime.fromtimestamp(os.path.getmtime(f_name))

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


def parse(fnme, lnme):
    """Parse unstructured text information"""

    data = []

    sndr = ''
    date = ''
    subj = ''
    repl = ''

    # regexes to search for required elements in texts
    rx_mark = re.compile(r'From ')
    rx_from = re.compile(r'From: (.*)')
    rx_date = re.compile(r'Date: (.*)')
    rx_subj = re.compile(r'Subject: (.*)')
    rx_repl = re.compile(r'In-Reply-To: (.*)')
    rx_m_id = re.compile(r'Message-ID: (.*)')

    # get file extension
    fext = os.path.splitext(fnme)[1]

    # use appropriate method, gzip.open for .gz files, open for .txt
    with (gzip.open if fext == ".gz" else open)(fnme, 'rt',
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
                while not rx_mark.match(str(line)):
                    if line is None:
                        break
                    text.append(line)
                    line = next(f, None)

                # text cleaning
                text = clean(text)

                message = {
                    'List': lnme,
                    'From': sndr,
                    'Date': date,
                    'Subj': subj,
                    'Rply': repl,
                    'M_id': m_id,
                    'Text': text
                }

                data.append(message)

            line = next(f, None)

        f.close()

        # data = pd.DataFrame(data)

    # return pandas data frame with structured information
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
    with open(lindex, 'w') as f_lindex_out:
        f_lindex_out.write('\n'.join(lists_names))


# if lists index file is ok (exists, size > 0, fresh) then read it
f_lindex_in = open(lindex, 'r')
lists_names = f_lindex_in.readlines()
lists_names = [s.rstrip() for s in lists_names]

# for every mailing list name get list of archived text files in it
for list_name in lists_names:

    # construct name for individual list of files in every mailing list
    name = 'data/indexes/' + list_name + '.txt'

    # if this list of files does not exist or is older than period:
    if not os.path.exists(name) or days_last_modified(name) > period:

        # then get it or update it
        mlist_files = get_files_from_list(lists_files_url + list_name)

        # and save it to disk
        with open(name, 'w') as f_out:
            f_out.write('\n'.join(mlist_files))

    # if list of files in a mailing list is ok then read it
    f_in = open(name, 'r')
    mlist_files = f_in.readlines()
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
            file_url = lists_files_url + list_name + '/' + mlist_file
            urllib.request.urlretrieve(file_url, (mlist_dir + mlist_file))

    f_in.close()

# close index file
f_lindex_in.close()


print('Start processing all files...')


# init data frame for all mails
all_mails = pd.DataFrame(columns=['List', 'Date', 'From', 'M_id',
                                  'Rply', 'Subj', 'Text'])

# TODO: save log of processed files. If file is there, do not reprocess!
# parse every file in the directories
for root, dirs, files in os.walk('data/texts'):
    for file in files:
        print('Processing file:', os.path.join(root, file))

        # get file extension to process only appropriate files
        ext = os.path.splitext(file)[1]

        if ext == '.gz' or ext == '.txt':
            # get list name to pass and add to structured list
            list_name = root.split('/')[2]

            parsed_message = parse(os.path.join(root, file), list_name)
            all_mails = all_mails.append(parsed_message)

        else:
            continue

print('All files processed. Saving result to file...')

# save to file(s)
all_mails.to_csv('mails.tsv', sep='\t', encoding='utf-8')

# save to elasticsearch index
df_as_json = all_mails.to_json(orient='records', lines=True)


# show how long did it take
diff = time.time() - start_time
m, s = divmod(diff, 60)
h, m = divmod(m, 60)
print(f'All tasks completed in {int(h):02d}h {int(m):02d}m {s:05.2f}s.')

# from elasticsearch import Elasticsearch
# es = Elasticsearch()
# es.index(index="mails", doc_type='message', id=m_id, body=message)
