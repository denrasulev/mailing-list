import re
import gzip
import time
import os.path
import pandas as pd


def clean(text):
    """Clean text from anything but words"""

    # regex for any non-word character
    rx_clean = re.compile('\W+_*')

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


def parse(file_name, list_name):
    """Parse unstructured text information"""
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
                    line = next(f, None)
                    if line is None:
                        break
                    text.append(line)

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

                data.append(message)

            line = next(f, None)

        f.close()

        data = pd.DataFrame(data)

    # return pandas data frame with sctructured information
    return data


# start
print('Start processing all files...')
start_time = time.time()


# init dataframe for all mails
all_mails = pd.DataFrame(columns=['List', 'Date', 'From', 'M_id',
                                  'Rply', 'Subj', 'Text'])


# parse every file in the directories
for root, dirs, files in os.walk('data/texts'):
    for file in files:
        print('Processing file:', os.path.join(root, file))

        # get file extension to process only required files
        ext = os.path.splitext(file)[1]

        # get list name to pass and add to structured list
        list_name = root.split('/')[2]

        if ext == '.gz' or ext == '.txt':
            message = parse(os.path.join(root, file), list_name)
            all_mails = all_mails.append(message)
        else:
            continue


# save to file(s)
print('Saving results to file...')
all_mails.to_csv('mails.tsv', sep='\t', encoding='utf-8')


# show how long did it take
diff = time.time() - start_time
m, s = divmod(diff, 60)
h, m = divmod(m, 60)
print(f'All files processed in {int(h):02d}h {int(m):02d}m {s:05.2f}s.')
