# /usr/bin/python3

import re
from datetime import datetime, timedelta
from models import Token_common, Token_squid, Token_combined, Uurl, Session, get_or_create
import settings
from sqlalchemy import or_
from PyQt4 import QtCore
import logging


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
        regex_squid = re.compile(settings.SQUID_LOG_RE)
        regex_common = re.compile(settings.APACHE_COMMON_LOG_RE)
        regex_combined = re.compile(settings.APACHE_COMBINED_LOG_RE)
        if regex_squid.match(line):
            # Move cursor back to original
            self.file.seek(orig)
            logging.info("File type SQUID detected")
            return settings.SQUID
        elif regex_common.match(line):
            self.file.seek(orig)
            logging.info("File type APACHE COMMON detected")
            return settings.APACHE_COMMON
        elif regex_combined.match(line):
            self.file.seek(orig)
            logging.info("File type APACHE COMBINED detected")
            return settings.APACHE_COMBINED
        else:
            raise ValueError("Unrecognized file format.\nWe currently support "
                             "only Apache Web Server Log file and Squid Proxy "
                             "Server Log file.")


class TokenizationThread(LogFile, QtCore.QThread):
    """docstring for TokenizationThread"""
    line_count_signal = QtCore.pyqtSignal(int)
    update_progress_signal = QtCore.pyqtSignal(list)

    def __init__(self, file_path, f_type):
        super(TokenizationThread, self).__init__(file_path)
        self.number_of_lines = self._count_lines()
        if self.file_type != f_type:
            logging.error("Incorrect file type. Detected type: %d, selected "
                          "type: %d" % (self.file_type, f_type))
            raise TypeError

    def _count_lines(self):
        count = sum(1 for _ in self.file)
        # Move file pointer to the start of the file
        self.file.seek(0, 0)
        return count

    def run(self):
        """
        Break the log file into tokens and insert them into the database
        """
        # Send number of lines to the GUI
        self.line_count_signal.emit(self.number_of_lines)
        logging.info("Total number of lines in file %d" % self.number_of_lines)
        if self.file_type == settings.APACHE_COMMON:
            token_array = []
            self.update_progress_signal.emit(
                [-1, settings.APACHE_COMMON_HEADING])
            for i, line in enumerate(self.file):
                item = line.split(" ")
                # Remove '[' from date
                datetime_string = item[3].replace('[', '')
                # Remove ']' from timezone
                timezone_string = item[4].replace(']', '')

                # Remove '"' from request method
                method_string = item[5].replace('"', '')

                # Remove DUST
                resource_requested = item[6].split('?')[0]

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
                    resource_requested=resource_requested,
                    request_ext=request_ext, protocol=protocol_string,
                    status_code=status_code,
                    size_of_object=bytes_transferred)
                token_array.append(token_object)
                self.send_result_signal(i, token_object)

        elif self.file_type == settings.APACHE_COMBINED:
            token_array = []
            self.update_progress_signal.emit(
                [-1, settings.APACHE_COMBINED_HEADING])
            for i, line in enumerate(self.file):
                item = line.split(" ")
                # Remove '[' from date
                datetime_string = item[3].replace('[', '')
                # Remove ']' from timezone
                timezone_string = item[4].replace(']', '')

                # Remove '"' from request method
                method_string = item[5].replace('"', '')

                # Remove DUST
                resource_requested = item[6].split('?')[0]

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
                token_object = Token_combined(
                    ip_address=item[0], user_identifier=item[1],
                    user_id=item[2], date_time=date_time,
                    time_zone=timezone_string, method=method_string,
                    resource_requested=resource_requested,
                    request_ext=request_ext, protocol=protocol_string,
                    status_code=status_code,
                    size_of_object=bytes_transferred, referrer=item[11], user_agent=item[12])
                token_array.append(token_object)
                self.send_result_signal(i, token_object)

        elif self.file_type == settings.SQUID:
            token_array = []
            self.update_progress_signal.emit([-1, settings.SQUID_HEADING])
            for i, line in enumerate(self.file):
                item = re.match(settings.SQUID_LOG_RE, line)

                # The timestamp string contains milliseconds which cannot be
                # directly removed. So the string is converted to float and
                # then to an int
                date_time = datetime.fromtimestamp(int(float(item.group(1))))
                duration = int(item.group(2))
                status_code = item.group(4).split("/")[-1]
                bytes_delivered = int(item.group(5))
                request_url = item.group(7).split("?")[0]
                request_ext = request_url.split(".")[-1]
                token_object = Token_squid(
                    date_time=date_time, duration=duration,
                    ip_address=item.group(3), status_code=status_code,
                    bytes_delivered=bytes_delivered, method=item.group(6),
                    url=request_url, user=item.group(8),
                    hierarchy_code=item.group(9),
                    type_content=item.group(10), request_ext=request_ext
                )
                token_array.append(token_object)
                self.send_result_signal(i, token_object)
        self.session.bulk_save_objects(token_array)
        self.session.commit()
        logging.info("All tokens inserted into database")
        settings.Session.remove()

    def send_result_signal(self, i, token_obj):
        """
        Send current status of the tokenization to the GUI.
        :param i: Current tokenization count
        :param token_obj: Token_common object
        """

        if self.file_type == settings.APACHE_COMMON:
            text = [i + 1, token_obj.ip_address, token_obj.user_identifier,
                    token_obj.user_id, str(token_obj.date_time),
                    token_obj.time_zone, token_obj.method,
                    token_obj.status_code, token_obj.size_of_object,
                    token_obj.protocol, token_obj.resource_requested]

            msg = [i, settings.APACHE_COMMON_OUTPUT_FORMAT.format(*text)]

        elif self.file_type == settings.APACHE_COMBINED:
            text = [i + 1, token_obj.ip_address, token_obj.user_identifier,
                    token_obj.user_id, str(token_obj.date_time),
                    token_obj.time_zone, token_obj.method,
                    token_obj.status_code, token_obj.size_of_object,
                    token_obj.protocol, token_obj.resource_requested,
                    token_obj.referrer, token_obj.user_agent]

            msg = [i, settings.APACHE_COMBINED_OUTPUT_FORMAT.format(*text)]

        elif self.file_type == settings.SQUID:
            text = [i + 1, str(token_obj.date_time), token_obj.duration,
                    token_obj.ip_address,
                    token_obj.status_code, token_obj.bytes_delivered,
                    token_obj.user, token_obj.hierarchy_code,
                    token_obj.type_content, token_obj.method, token_obj.url]

            # *text is used to expand list in place
            msg = [i, settings.SQUID_OUTPUT_FORMAT.format(*text)]
        # Send status to GUI
        self.update_progress_signal.emit(msg)


class FilteringThread(LogFile, QtCore.QThread):
    """ Filters data in the database according to ignore criteria"""

    line_count_signal = QtCore.pyqtSignal(int)
    result_item_signal = QtCore.pyqtSignal(list)
    update_progress_signal = QtCore.pyqtSignal(list)

    def __init__(self, file_path, ignore_list):
        super(FilteringThread, self).__init__(file_path)
        self.ignore_list = ignore_list

    def run(self):
        """
        Removes unnecessary entries from the log file based on the list of
        file formats in items list
        """
        # Strip whitespaces from every element of the ignore_list
        ignore_list = [x.strip(' ') for x in self.ignore_list]
        logging.info("File type to remove: %s" % str(ignore_list))
        if self.file_type == settings.APACHE_COMMON:
            # Ignore criteria
            status_code = settings.apache_ignore_criteria['status_code']
            # Request method
            method = settings.apache_ignore_criteria['method']
            min_size = settings.apache_ignore_criteria['size_of_object']

            self.session.query(Token_common).filter(
                or_(Token_common.status_code != status_code,
                    ~Token_common.method.in_(method),
                    Token_common.request_ext.in_(ignore_list),
                    Token_common.size_of_object <= min_size)).delete(
                synchronize_session='fetch')

        elif self.file_type == settings.APACHE_COMBINED:
            # Ignore criteria
            status_code = settings.apache_ignore_criteria['status_code']
            # Request method
            method = settings.apache_ignore_criteria['method']
            min_size = settings.apache_ignore_criteria['size_of_object']

            self.session.query(Token_combined).filter(
                or_(Token_combined.status_code != status_code,
                    ~Token_combined.method.in_(method),
                    Token_combined.request_ext.in_(ignore_list),
                    Token_combined.size_of_object <= min_size)).delete(
                synchronize_session='fetch')

        elif self.file_type == settings.SQUID:
            # Ignore criteria
            status_code = settings.squid_ignore_criteria['status_code']
            # Request method
            method = settings.squid_ignore_criteria['method']
            min_size = settings.squid_ignore_criteria['size_of_object']

            self.session.query(Token_squid).filter(
                or_(Token_squid.status_code != status_code,
                    ~Token_squid.method.in_(method),
                    Token_squid.request_ext.in_(ignore_list),
                    Token_squid.bytes_delivered <= min_size)).delete(
                synchronize_session='fetch')

        self.session.commit()
        self.send_all_data()
        settings.Session.remove()

    def send_all_data(self):
        """
        Send filtered data to GUI
        """
        if self.file_type == settings.APACHE_COMMON:
            self.update_progress_signal.emit(
                [-1, settings.APACHE_COMMON_HEADING])
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

        elif self.file_type == settings.APACHE_COMBINED:
            self.update_progress_signal.emit(
                [-1, settings.APACHE_COMBINED_HEADING])
            # Send result to GUI
            self.line_count_signal.emit(
                self.session.query(Token_combined).count())

            for i, token_obj in enumerate(self.session.query(
                    Token_combined).all()):
                text = [i + 1, token_obj.ip_address,
                        token_obj.user_identifier, token_obj.user_id,
                        str(token_obj.date_time), token_obj.time_zone,
                        token_obj.method, token_obj.status_code,
                        token_obj.size_of_object, token_obj.protocol,
                        token_obj.resource_requested, token_obj.referrer,
                        token_obj.user_agent]
                # *text is used to expand list in place
                msg = [i, settings.APACHE_COMBINED_OUTPUT_FORMAT.format(*text)]
                self.result_item_signal.emit(msg)

        elif self.file_type == settings.SQUID:
            self.update_progress_signal.emit(
                [-1, settings.SQUID_HEADING])
            self.line_count_signal.emit(
                self.session.query(Token_squid).count())

            for i, token_obj in enumerate(self.session.query(
                    Token_squid).all()):
                text = [i + 1, str(token_obj.date_time), token_obj.duration,
                        token_obj.ip_address, token_obj.status_code,
                        token_obj.bytes_delivered, token_obj.user,
                        token_obj.hierarchy_code, token_obj.type_content,
                        token_obj.method, token_obj.url]
                # *text is used to expand list in place
                msg = [i, settings.SQUID_OUTPUT_FORMAT.format(*text)]
                self.result_item_signal.emit(msg)


class SessionThread(LogFile, QtCore.QThread):
    """ The thread that performs sessionization of the data in the database """
    total_count_signal = QtCore.pyqtSignal(int)
    update_progress_signal = QtCore.pyqtSignal(list)
    result_signal = QtCore.pyqtSignal(str)
    # To be sent after each step is completed
    step_completed_signal = QtCore.pyqtSignal(int)
    number_of_sessions_signal = QtCore.pyqtSignal(int)

    def __init__(self, file_path, session_timer):
        super(SessionThread, self).__init__(file_path)
        self.session_timer = timedelta(minutes=session_timer)
        logging.info("Session timer: %s" % str(self.session_timer))

    def run(self):
        self.init_tables()
        Token_type = None

        if self.file_type == settings.APACHE_COMMON:
            Token_type = Token_common
        elif self.file_type == settings.SQUID:
            Token_type = Token_squid
        elif self.file_type == settings.APACHE_COMBINED:
            Token_type = Token_combined
        # Get all distinct ip addresses
        all_entries = self.session.query(Token_type.ip_address).order_by(
            'ip_address').distinct().all()

        self.total_count_signal.emit(len(all_entries))

        # Create sessions for each IP address
        for i, entry in enumerate(all_entries):

            # Get all entries for an ip address
            same_ip_entries = self.session.query(Token_type).filter(
                Token_type.ip_address == entry.ip_address).order_by(
                Token_type.date_time).all()

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
        logging.info("All sessions created. Sending result to the GUI")
        self.session.commit()
        self.send_results()
        settings.Session.remove()

    def init_tables(self):
        """ Drop sessions and url tables and create new tables.
        This is done to clear all the previous sessions.
        """

        settings.Base.metadata.tables[
            'session_master'].drop(bind=settings.engine)
        settings.Base.metadata.tables['uurl'].drop(bind=settings.engine)

        settings.Base.metadata.tables[
            'session_master'].create(bind=settings.engine)
        settings.Base.metadata.tables['uurl'].create(bind=settings.engine)

        logging.info("Sessionization Tables created")

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
        if self.file_type == settings.APACHE_COMMON:
            url_obj = get_or_create(
                self.session, Uurl, url=token_object.resource_requested)
        elif self.file_type == settings.APACHE_COMBINED:
            url_obj = get_or_create(
                self.session, Uurl, url=token_object.resource_requested)
        elif self.file_type == settings.SQUID:
            url_obj = get_or_create(
                self.session, Uurl, url=token_object.url)

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

    def send_results(self):
        """ Send sessionized data to the GUI """
        # Send total records count for the progress bar
        total_records = self.session.query(Uurl).count() + \
            self.session.query(Session).count()
        self.total_count_signal.emit(total_records)

        url_query = self.session.query(Uurl).all()
        for q in url_query:
            self.update_progress_signal.emit([q.id, str(q)])
        logging.info("All urls sent to the GUI")
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
        logging.info("All sessions sent to the GUI")
        # Printing sessions completed
        self.step_completed_signal.emit(3)

        self.number_of_sessions_signal.emit(
            self.session.query(Session).count())
