# /usr/bin/python3

import re
from datetime import datetime
from models import Token_common
import settings
from sqlalchemy import or_
from PyQt4 import QtCore


class LogFile(object):
    """ Represents the input log file """

    def __init__(self, file_path):
        super(LogFile, self).__init__()

        self.path = file_path
        try:
            self.file = open(file_path, "r", encoding="latin-1")
        except (OSError, IOError):
            raise
        self.file_type = self.get_file_type()
        self.session = settings.Session()

    def get_file_type(self):
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


class TokenizationThread(LogFile, QtCore.QThread):
    """docstring for TokenizationThread"""
    line_count_signal = QtCore.pyqtSignal(int)
    update_progress_signal = QtCore.pyqtSignal(list)

    def __init__(self, file_path):
        super(TokenizationThread, self).__init__(file_path)

    def run(self):
        number_of_lines = self._count_lines()
        # Send number of lines to the GUI
        self.line_count_signal.emit(number_of_lines)
        self.tokenize()

    def _count_lines(self):
        count = sum(1 for _ in self.file)
        # Move file pointer to the start of the file
        self.file.seek(0, 0)
        return count

    def tokenize(self):
        """
        Break the log file into tokens and insert them into the database
        """
        # Create new scoped_session. All threads need independent sessions

        if self.file_type == settings.APACHE_COMMON:
            token_array = []
            for i, line in enumerate(self.file):
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
                token_object = Token_common(
                    ip_address=item[0], user_identifier=item[1],
                    user_id=item[2], date_time=date_time,
                    time_zone=timezone_string, method=method_string,
                    resource_requested=item[6], request_ext=request_ext,
                    protocol=protocol_string, status_code=status_code,
                    size_of_object=bytes_transferred)
                token_array.append(token_object)
                self.send_result_signal(i, token_object)
            self.session.bulk_save_objects(token_array)
            self.session.commit()

    def send_result_signal(self, i, token_obj):
        """
        Send current status of the tokenization to the GUI.
        :param i: Current tokenization count
        :param token_obj: Token_common object
        """
        text = [i, token_obj.ip_address, token_obj.user_identifier,
                token_obj.user_id, str(token_obj.date_time),
                token_obj.time_zone, token_obj.method, token_obj.status_code,
                token_obj.size_of_object, token_obj.protocol,
                token_obj.resource_requested]
        # *text is used to expand list in place
        msg = [i, settings.APACHE_COMMON_OUTPUT_FORMAT.format(*text)]
        # Send status to GUI
        self.update_progress_signal.emit(msg)


class FilteringThread(LogFile, QtCore.QThread):
    """ Filters data in the database according to ignore criteria"""

    line_count_signal = QtCore.pyqtSignal(int)
    result_item_signal = QtCore.pyqtSignal(list)

    def __init__(self, file_path, ignore_list):
        super(FilteringThread, self).__init__(file_path)
        self.ignore_list = ignore_list

    def run(self):
        """
        Removes unnecessary entries from the log file based on the list of
        file formats in items list
        """
        # Ignore criteria
        status_code = settings.ignore_criteria['status_code']
        # Request method
        method = settings.ignore_criteria['method']
        min_size = settings.ignore_criteria['size_of_object']

        # Strip whitespaces from every element of the ignore_list
        ignore_list = [x.strip(' ') for x in self.ignore_list]
        del_count = 0
        if self.file_type == settings.APACHE_COMMON:
            # Entries with these IDs will be removed
            del_count = self.session.query(Token_common).filter(
                or_(Token_common.status_code != status_code,
                    ~Token_common.method.in_(method),
                    Token_common.request_ext.in_(ignore_list),
                    Token_common.size_of_object <= min_size)).delete(
                synchronize_session='fetch')
            self.session.commit()

        elif self.file_type == settings.SQUID:
            pass

        self.send_all_data(del_count)

    def send_all_data(self, del_count):
        """
        Send filtered data to GUI
        :param del_count: Number of rows deleted
        """
        # Send result to GUI
        self.line_count_signal.emit(self.session.query(Token_common).count())

        for i, token_obj in enumerate(self.session.query(Token_common).all()):
            text = [i + 1, token_obj.ip_address,
                    token_obj.user_identifier, token_obj.user_id,
                    str(token_obj.date_time), token_obj.time_zone,
                    token_obj.method, token_obj.status_code,
                    token_obj.size_of_object, token_obj.protocol,
                    token_obj.resource_requested]
            # *text is used to expand list in place
            msg = [i, settings.APACHE_COMMON_OUTPUT_FORMAT.format(*text)]
            self.result_item_signal.emit(msg)
