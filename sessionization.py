# Sample script to parse squid proxy server log and apache web server log

import re
import datetime as dt
import argparse

squidProxyLogFileRegex = '\d+\.\d+\s+\d+\s+([0-9\.]+)\s\w{1,8}\/\d{3}\s\d+.+'
apacheWebServerLogFileRegex = '([0-9\.]+)([\w\. \-]+)\s(\[.+])\s".+"\s\d{3}.+'


def get_file_type(line):
    regex = re.compile(squidProxyLogFileRegex)
    if regex.match(line):
        return "SQUID"
    regex = re.compile(apacheWebServerLogFileRegex)
    if regex.match(line):
        return "APACHE"
    return None


# calculate session time for each ip
def calc_session_time(times):
    total_time = []
    diff = [[]]
    if len(times) < 2:
        return
    for i, j in zip(times[:-1], times[1:]):
        if j - i > dt.timedelta(minutes=10) and diff[0]:
            diff.append([j - i])
        else:
            diff[-1].append(j - i)
    for di in diff:
        total = dt.timedelta(0)
        for d in di:
            total += d
        total_time.append(str((total.seconds // 60) % 60) +
                          'm ' + str(total.seconds % 60) + 's')
    return total_time


def filter_file(infile):
    line = []
    for log_line in infile:
        items = []
        part = log_line.split(" ")[:9]

        # Skip requests for the following type of files
        if part[6].split('.')[-1] in \
                ['jpg', 'ico', 'cgi', 'gif', 'png', 'js', 'css', 'txt']:
            continue

        # Skip files without a "GET" or "POST" type request
        elif part[5] == '"-"':
            continue
        elif len(part[0]) > 16:
            continue
        items.append(part[0])  # IP address
        date_object = dt.datetime.strptime(
            part[3][1:], '%d/%b/%Y:%H:%M:%S')  # Time stamp
        items.append(date_object)
        items.append(part[6])  # Requested url
        line.append(items)
    return line


def main():
    parser = argparse.ArgumentParser(usage='%(prog)s INPUT [-h] [options]',
                                     description='Sessionizes the given file.')
    parser.add_argument('--output', help='Output file name')
    parser.add_argument('--type', help='Output file type')
    parser.add_argument('INPUT', help='File to be processed')
    args = parser.parse_args()

    infile = open(args.INPUT, 'r')
    print(get_file_type(infile.readline()))

'''
def first():
    for l in line:
        key = l[0]
        item = dict()
        if key in sessions.keys():  # IP already exists
            item = sessions[key]
            item['datetime'].append(l[1])  # Add datetime
            item['urls'].append(l[2])       # Add urls
            item['total_session_time'] = calc_session_time(item['datetime'])
        else:   # IP does not exists
            item['datetime'] = [l[1]]
            item['urls'] = [l[2]]
            item['total_session_time'] = '0s'
            sessions[key] = item
'''
if __name__ == '__main__':
    main()
