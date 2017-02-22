# /usr/bin/python3

import re
import argparse
import os
from sqlalchemy import create_engine, orm
import db

DB_NAME = "yast.db"

engine = create_engine('sqlite:///./' + DB_NAME)
Session = orm.sessionmaker(bind=engine)
session = Session()

def _utf8len(string):
    """
    Return length of string in bytes
    :return: String length in bytes
    """
    return len(string.encode('utf-8'))

class LogFile(object):
    """ Represents raw log file """
    squid_log_re = '\d+\.\d+\s+\d+\s+([0-9\.]+)\s\w{1,8}\/\d{3}\s\d+.+'
    apache_common_log_re = '([0-9\.]+)([\w\. \-]+)\s(\[.+])\s".+"\s\d{3}.+'

    def __init__(self, file_path):
        super(LogFile, self).__init__()
        self.path = file_path
        try:
            self.file = open(file_path, "r")
        except FileNotFoundError:
            print("No such file or directory: ", file_path)
            exit(0)

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
        if self.file_type == "APACHE_COMMON":
            for line in self.file:
                item = line.split(" ")
                # Remove '[' from date
                item[4].replace('[', '')

                # Remove ']' from timezone
                item[5].replace(']', '')

                # Remove '"' from request method
                item[6].replace('"', '')

                # Remove '"' from request URL
                item[7].replace('"', '')
                token = db.Token_common(
                    ip_address=item[0], user_identifier=item[1],
                    user_id=item[2], date_time=item[3], time_zone=item[4],
                    method=item[5], resource_requested=item[6],
                    protocol=item[7], status_code=item[8],
                    size_of_object=item[9])
                session.add(token)
            session.commit()

    @property
    def file_type(self):
        """
        Returns log file type.
        :return: File type. Possible values "APACHE_COMMON" and "SQUID"
        """
        # Save original position
        orig = self.file.tell()
        line = self.file.readline()
        file_type = None
        regex = re.compile(LogFile.squid_log_re)
        if regex.match(line):
            file_type = 'SQUID'
        regex = re.compile(LogFile.apache_common_log_re)
        if regex.match(line):
            file_type = 'APACHE_COMMON'
        # Move cursor back to original
        self.file.seek(orig)
        if not file_type:
            raise ValueError("Unrecognized file format.\nWe currently support "
                             "only Apache Web Server Log file and Squid Proxy "
                             "Server Log file.")
        return file_type

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
    
    def create_tables(self, log_file):
        if log_file.file_type == "APACHE_COMMON":
            db.Token_common.__table__.create(engine)
        elif log_file.file_type == "SQUID":
            db.Token_squid.__table__.create(engine)
    
    def run(self):
        parser = argparse.ArgumentParser(usage='%(prog)s INPUT [-h] [options]',
                                         description='Sessionizes the given file.')
        parser.add_argument('--output', help='Output file name')
        parser.add_argument('--type', help='Output file type')
        parser.add_argument('INPUT_FILE', help='File to be processed')
        args = parser.parse_args()

        log_file = LogFile(args.INPUT_FILE)
        self.create_tables(log_file)
        log_file.tokenize()

if __name__ == '__main__':
    y = Yast()
    y.run()