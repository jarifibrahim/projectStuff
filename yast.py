# /usr/bin/python3

import re
import argparse
import os


def _utf8len(string):
    """
    Return length of string in bytes
    :return: String length in bytes
    """
    return len(string.encode('utf-8'))


class LogFile(object):
    """ Represents raw log file """
    squid_log_re = '\d+\.\d+\s+\d+\s+([0-9\.]+)\s\w{1,8}\/\d{3}\s\d+.+'
    apache_log_re = '([0-9\.]+)([\w\. \-]+)\s(\[.+])\s".+"\s\d{3}.+'

    def _get_file_type(self):
        """
        Returns log file type.
        :return: File type. Possible values "APACHE" and "SQUID"
        """
        # Save original position
        orig = self.file.tell()
        line = self.file.readline()
        file_type = None
        regex = re.compile(LogFile.squid_log_re)
        if regex.match(line):
            file_type = 'SQUID'
        regex = re.compile(LogFile.apache_log_re)
        if regex.match(line):
            file_type = 'APACHE'
        # Move cursor back to original
        self.file.seek(orig)
        if not file_type:
            raise ValueError("Unrecognized file format.\nWe currently support "
                             "only Apache Web Server Log file and Squid Proxy "
                             "Server Log file.")
        return file_type

    def __init__(self, file_path):
        super(LogFile, self).__init__()
        self.path = file_path
        try:
            self.file = open(file_path, "r")
        except FileNotFoundError:
            print("No such file or directory:", file_path)
            exit(0)
        self.type = self._get_file_type()

    def filter_file(self, ignore_list):
        """
        Removes unnecessary entries from the log file
        based on the list of file formats in items list
        :param ignore_list: List of file extensions to be removed
        :return: Log file without specified entries
        """

        # Create new temporary file to store results
        clean_file = open("Clean_file.log", "w")

        if self.type == 'APACHE':
            for log_line in self.file:
                part = log_line.split(" ")[:9]

                # Skip requests for the following type of files
                if part[6].split('.')[-1].lower() in ignore_list:
                    continue

                # Skip files without a "GET" or "POST" type request
                elif part[5] == '"-"':
                    continue
                clean_file.write(log_line)
        elif self.type == 'SQUID':
            pass

    def tokenize(self):
        """
        Transform the log file into tokens for further processing
        :return:
        """
        pass

    @property
    def file_size(self):
        return os.stat(self.path).st_size

    @property
    def number_of_lines(self):
        """
        Approximate number of lines using the formula
        Number of lines = Total size / Size of one line
        :return:
        """
        orig = self.file.tell()
        single_line_size = _utf8len(self.file.readline())
        self.file.seek(orig)
        return self.file_size // single_line_size

    @property
    def file_name(self):
        try:
            return self.path.split("/")[-1]
        except IndexError:
            return self.path


class CleanLogFile(LogFile):
    pass


class Session(object):
    pass


class SessionFile(object):
    pass


class Yast:
    def run(self):
        parser = argparse.ArgumentParser(usage='%(prog)s INPUT [-h] [options]',
                                         description='Sessionizes the given file.')
        parser.add_argument('--output', help='Output file name')
        parser.add_argument('--type', help='Output file type')
        parser.add_argument('INPUT_FILE', help='File to be processed')
        args = parser.parse_args()

        log_file = LogFile(args.INPUT_FILE)
        #items = ['jpg', 'ico', 'cgi', 'gif', 'png', 'js', 'css', 'txt']
        #log_file.filter_file(items)
        #print(log_file.file_name)

if __name__ == '__main__':
    y = Yast()
    y.run()
