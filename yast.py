# /usr/bin/python3

import re
from datetime import datetime, timedelta
from models import Token_common, Token_squid, Uurl, Session, get_or_create
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
        

        if self.file_type == settings.APACHE_COMMON:
            token_array = []
            self.update_progress_signal.emit([-1, settings.APACHE_COMMON_HEADING])
            for i, line in enumerate(self.file):
                item = line.split(" ")
                # modelremove '[' from date
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
            settings.Session.remove()

        elif self.file_type == settings.SQUID:

            token_array = []
            self.update_progress_signal.emit([-1, settings.SQUID_HEADING])

            for i, line in enumerate(self.file):
                item = line.split(" ")
                                
                token_object = Token_squid(time = item[0], duration = item[1],
                    ip_address = item[2], result_code = item[3],
                    bytes_delivered = item[4], method = item[5],
                    url = item[6], user = item[7], hierarchy_code = item[8],
                    type_content = item[9]
                )
                token_array.append(token_object)
                self.send_result_signal(i, token_object)
            self.session.bulk_save_objects(token_array)
            self.session.commit()
            settings.Session.remove()

    def send_result_signal(self, i, token_obj):
        """
        Send current status of the tokenization to the GUI.
        :param i: Current tokenization count
        :param token_obj: Token_common object
        """

        if self.file_type == settings.APACHE_COMMON:
            text = [i, token_obj.ip_address, token_obj.user_identifier,
                    token_obj.user_id, str(token_obj.date_time),
                    token_obj.time_zone, token_obj.method, token_obj.status_code,
                    token_obj.size_of_object, token_obj.protocol,
                    token_obj.resource_requested]
            
            msg = [i, settings.APACHE_COMMON_OUTPUT_FORMAT.format(*text)]

        elif self.file_type == settings.SQUID:
            text = [i, token_obj.time, token_obj.duration,
                    token_obj.ip_address,
                    token_obj.result_code, token_obj.bytes_delivered, token_obj.method,
                    token_obj.url, token_obj.user,
                    token_obj.hierarchy_code, token_obj.type_content]
            
            # *text is used to expand list in place
            msg = [i, settings.SQUID_OUTPUT_FORMAT.format(*text)]
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
        settings.Session.remove()

    def send_all_data(self, del_count):
        """
        Send filtered data to GUI
        :param del_count: Number of rows deleted
        """
        if self.file_type == settings.APACHE_COMMON:
            # Send result to GUI
            self.line_count_signal.emit(
                self.session.query(Token_common).count())

            for i, token_obj in enumerate(self.session.query(
                    Token_common).all()):
                text = [i + 1, token_obj.ip_address,
                        token_obj.user_identifier, token_obj.user_id,
                        str(token_obj.date_time), token_obj.time_zone,
                        token_obj.method, token_obj.status_code,
                        token_obj.size_of_object, token_obj.protocol,
                        token_obj.resource_requested]
                # *text is used to expand list in place
                msg = [i, settings.APACHE_COMMON_OUTPUT_FORMAT.format(*text)]
                self.result_item_signal.emit(msg)


class SessionThread(LogFile, QtCore.QThread):
    """ The thread that performs sessionization of the data in the database """
    total_count_signal = QtCore.pyqtSignal(int)
    update_progress_signal = QtCore.pyqtSignal(list)
    result_signal = QtCore.pyqtSignal(str)
    # To be sent after each step is completed
    step_completed_signal = QtCore.pyqtSignal(int)

    def __init__(self, file_path, session_timer):
        super(SessionThread, self).__init__(file_path)
        self.session_timer = timedelta(minutes=session_timer)

    def run(self):

        if self.file_type == settings.APACHE_COMMON:
            # Get all distinct ip addresses
            all_entries = self.session.query(Token_common.ip_address).order_by(
                'ip_address').distinct().all()

            self.total_count_signal.emit(len(all_entries))

            # Create sessions for each IP address
            for i, entry in enumerate(all_entries):

                # Get all entries for an ip address
                same_ip_entries = self.session.query(Token_common).filter(
                    Token_common.ip_address == entry.ip_address).order_by(
                    Token_common.date_time).all()

                total_session_time = timedelta(0)

                first_entry = same_ip_entries.pop(0)
                # Add the first entry to sessions.
                self.insert_item(first_entry, True)
                # Last entry time is the datetime of the last entry processed
                last_entry_time = first_entry.date_time

                for e in same_ip_entries:
                    # Calculate new session time
                    s_time = e.date_time - last_entry_time
                    # If new session time is greater than threshold
                    if s_time + total_session_time > self.session_timer:
                        # Create new session
                        self.insert_item(e, True)
                        total_session_time = timedelta(0)
                    # If new session time is not greater than threshold
                    else:
                        total_session_time = s_time + total_session_time
                        self.insert_item(e, False, total_session_time)
                    last_entry_time = e.date_time
                self.update_progress_signal.emit([i, None])
                # Generating sessions completed
                self.step_completed_signal.emit(1)

        self.send_results()
        settings.Session.remove()

    def insert_item(self, token_object,
                    new_session, session_time=timedelta(0)):
        """
        Create new session or update existing session object
        :param token_object:    Token that has to be converted into session
        :param new_session:     Boolean that denotes if this is a new session.
                                A new session will be created if this value
                                is True
        :param session_time:    If an existing session is to be updated,
                                session_time contains the new value of total
                                session time
        """
        url_obj = get_or_create(
            self.session, Uurl, url=token_object.resource_requested)
        # If this is a new session
        if new_session:
            # Create session object
            session_obj = Session(
                ip=token_object.ip_address, session_time=session_time)
            # Set start and end time
            session_obj.start_time = token_object.date_time
            session_obj.end_time = token_object.date_time
        # If new_session is False, new session may or may not be created
        # (depending upon the session_time)
        else:
            # Try to get session object
            session_obj = get_or_create(
                self.session, Session, ip=token_object.ip_address)
            # If the object is a new session
            if session_obj.session_time is timedelta(0):
                session_obj.start_time = token_object.date_time

            session_obj.session_time = session_time
            session_obj.end_time = token_object.date_time

        # Add url to session
        session_obj.session_urls.append(url_obj)
        self.session.add(session_obj)
        self.session.commit()

    def send_results(self):
        """ Send sessionized data to the GUI """
        # Send total records count for the progress bar
        total_records = self.session.query(Uurl).count() + \
            self.session.query(Session).count()
        self.total_count_signal.emit(total_records)

        url_query = self.session.query(Uurl).all()
        for q in url_query:
            self.update_progress_signal.emit([q.id, str(q)])

        # Printing urls completed
        self.step_completed_signal.emit(2)

        # Id of the last element inserted. It is used to calculate progressbar
        # value
        last_id = self.session.query(Uurl.id).order_by(
            Uurl.id.desc()).first()[0]

        self.update_progress_signal.emit([last_id, "\n"])
        self.update_progress_signal.emit([last_id, "\n"])

        msg = settings.SESSION_OUTPUT_HEADING
        self.update_progress_signal.emit([last_id, msg])

        # Send all sessions back to GUI
        session_query = self.session.query(Session).all()
        for s in session_query:
            self.update_progress_signal.emit([last_id + s.id - 1, str(s)])

        # Printing sessions completed
        self.step_completed_signal.emit(3)
