import re
import pandas as pd


def parse(file_name):

    data = []

    rx_mark = re.compile(r'From ')
    rx_from = re.compile(r'From: (.*)')
    rx_date = re.compile(r'Date: (.*)')
    rx_subj = re.compile(r'Subject: (.*)')
    rx_repl = re.compile(r'In-Reply-To: (.*)')
    rx_m_id = re.compile(r'Message-ID: (.*)')

    with open(file_name, 'r') as f:

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
