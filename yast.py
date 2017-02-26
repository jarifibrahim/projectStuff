# /usr/bin/python3

import re
import os
from datetime import datetime
from models import Token_common
import settings
import atexit
from sqlalchemy import or_

log_file = None


class LogFile(object):
    """ Represents the input log file """

    def __init__(self, file_path):
        super(LogFile, self).__init__()
        self.path = file_path
        try:
            self.file = open(file_path, "r")
        except (OSError, IOError):
            raise
        self.file_type = self._file_type()
        self.file_size = os.stat(self.path).st_size
        self._number_of_lines = self._number_of_lines
        self.file_name = self._file_name

    def filter_file(self, ignore_list):
        """
        Removes unnecessary entries from the log file based on the list of
        file formats in items list
        :param ignore_list: List of file extensions to be removed
        :return: Number of rows deleted
        """

        # Ignore criteria
        status_code = settings.ignore_criteria['status_code']
        # Request method
        method = settings.ignore_criteria['method']
        min_size = settings.ignore_criteria['size_of_object']

        if self.file_type == settings.APACHE_COMMON:
            del_count = settings.session.query(Token_common).filter(
                or_(Token_common.status_code != status_code,
                    ~Token_common.method.in_(method),
                    Token_common.request_ext.in_(ignore_list),
                    Token_common.size_of_object <= min_size)
            ).delete(synchronize_session='fetch')
            settings.session.commit()
            return del_count

        elif self.file_type == settings.SQUID:
            pass

    def tokenize(self):
        """
        Break the log file into tokens and insert them into the database
        :return: Number of rows inserted
        """
        if self.file_type == settings.APACHE_COMMON:
            for line in self.file:
                item = line.split(" ")
                # modelsemove '[' from date
                datetime_string = item[3].replace('[', '')
                # Remove ']' from timezone
                timezone_string = item[4].replace(']', '')

                # Remove '"' from request method
                method_string = item[5].replace('"', '')

                # Requested URL extension
                request_ext = item[6].split(".")[-1]

                # Remove '"' from protocol
                protocol_string = item[7].replace('"', '')

                date_time = datetime.strptime(
                    datetime_string, settings.DATETIME_FORMAT)

                # Try to convert bytes transferred to int
                try:
                    bytes_transferred = int(item[9])
                except ValueError:
                    bytes_transferred = 0

                try:
                    status_code = int(item[8])
                except ValueError:
                    status_code = 0
                token = Token_common(
                    ip_address=item[0], user_identifier=item[1],
                    user_id=item[2], date_time=date_time,
                    time_zone=timezone_string, method=method_string,
                    resource_requested=item[6], request_ext=request_ext,
                    protocol=protocol_string, status_code=status_code,
                    size_of_object=bytes_transferred)
                settings.session.add(token)
            settings.session.commit()
            return settings.session.query(Token_common).count()

    def get_all_tokens(self):
        """
        Return all tokens in the database
        """
        if self.file_type == settings.APACHE_COMMON:
            return settings.session.query(Token_common).all()

    def _file_type(self):
        """
        Returns log file type.
        :return: File type. Possible values APACHE_COMMON and SQUID
        """
        # Save original position
        orig = self.file.tell()
        line = self.file.readline()
        file_type = None
        regex = re.compile(settings.SQUID_LOG_RE)
        if regex.match(line):
            file_type = settings.SQUID
        regex = re.compile(settings.APACHE_COMMON_LOG_RE)
        if regex.match(line):
            file_type = settings.APACHE_COMMON
        # Move cursor back to original
        self.file.seek(orig)
        if not file_type:
            raise ValueError("Unrecognized file format.\nWe currently support "
                             "only Apache Web Server Log file and Squid Proxy "
                             "Server Log file.")
        return file_type

    def _file_name(self):
        try:
            return self.path.split("/")[-1]
        except IndexError:
            return self.path

    def _number_of_lines(self):
        count = sum(1 for _ in self.file)
        # Move file pointer to the start of the file
        self.file.seek(0, 0)
        return count


class Utility:
    @classmethod
    def remove_db(cls):
        try:
            os.remove(settings.DB_NAME)
        except FileNotFoundError:
            pass


atexit.register(Utility.remove_db)
