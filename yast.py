# /usr/bin/python3

import re
import os
from datetime.datetime import strptime
import models
from yast.settings import DATETIME_FORMAT, engine, session


class LogFile(object):
    """ Represents the input log file """
    squid_log_re = '\d+\.\d+\s+\d+\s+([0-9\.]+)\s\w{1,8}\/\d{3}\s\d+.+'
    apache_common_log_re = '([0-9\.]+)([\w\. \-]+)\s(\[.+])\s".+"\s\d{3}.+'

    def __init__(self, file_path):
        super(LogFile, self).__init__()
        self.path = file_path
        try:
            self.file = open(file_path, "r")
        except (OSError, IOError):
            print("No such file or directory: ", file_path)
            exit(0)
        self.number_of_lines = 0

    def filter_file(self, ignore_list):
        """
        Removes unnecessary entries from the log file
        based on the list of file formats in items list
        :param ignore_list: List of file extensions to be removed
        """

        # Create new temporary file to store results
        if self.type == 'APACHE':
            pass
        elif self.type == 'SQUID':
            pass

    def tokenize(self):
        """
        Break the log file into tokens and insert them into the database
        """
        if self.file_type == "APACHE_COMMON":
            for line in self.file:
                item = line.split(" ")
                # modelsemove '[' from date
                datetime_string = item[3].replace('[', '')
                # Remove ']' from timezone
                timezone_string = item[4].replace(']', '')

                # Remove '"' from request method
                method_string = item[5].replace('"', '')

                # Remove '"' from protocol
                protocol_string = item[7].replace('"', '')

                date_time = strptime(
                    datetime_string, DATETIME_FORMAT)

                # Try to convert bytes transferred to int
                try:
                    bytes_transferred = int(item[9])
                except ValueError:
                    bytes_transferred = 0

                try:
                    status_code = int(item[8])
                except ValueError:
                    status_code = 0
                token = models.Token_common(
                    ip_address=item[0], user_identifier=item[1],
                    user_id=item[2], date_time=date_time,
                    time_zone=timezone_string, method=method_string,
                    resource_requested=item[6], protocol=protocol_string,
                    status_code=status_code, size_of_object=bytes_transferred)
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
    def file_name(self):
        try:
            return self.path.split("/")[-1]
        except IndexError:
            return self.path


class Yast:
    def create_tables(log_file):
        if log_file.file_type == "APACHE_COMMON":
            models.Token_common.__table__.create(engine)
        elif log_file.file_type == "SQUID":
            models.Token_squid.__table__.create(engine)

    def start_tokenization(file_path):
        log_file = LogFile(file_path)
        Yast.create_tables(log_file)
        log_file.tokenize()
