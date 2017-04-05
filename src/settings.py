from sqlalchemy import create_engine, orm
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base
import tempfile

DATABASE_NAME = tempfile.gettempdir() + "/yast.db"
# Format of the datetime string in the log file
DATETIME_FORMAT = '%d/%b/%Y:%H:%M:%S'
# Create in-memory database with support for concurrent access by threads
engine = create_engine('sqlite:///' + DATABASE_NAME,
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Session_Factory = orm.sessionmaker(bind=engine)
# Required for threading
Session = orm.scoped_session(Session_Factory)
session = Session()
Base = declarative_base()

RESULT_SIGNAL_SIZE = 1000

APACHE_COMMON = 0
# Used while printing output
APACHE_COMMON_OUTPUT_FORMAT = ("{0: >5}\t{1: <15}\t{2: <30}\t{3: <30}"
                               "\t{4: <20}\t{5: <20}\t{6: <20}\t"
                               "{7: <20}\t{8: <20}\t{9: <20}\t{10:<}")
# Header for output
APACHE_COMMON_HEADING = APACHE_COMMON_OUTPUT_FORMAT.format(
    "ID", "IP Address", "User Identifier", "User ID", "Date Time",
    "Time zone", "Method", "Status Code", "Size of Object", "Protocol",
    "Resource Requested")
APACHE_COMMON_LOG_RE = r'^([0-9\.]+)\s((?:\w+|-))\s([\w\d_-]*)\s\[([\d\/\w:]*'\
    r')\s((?:\-|\+)\d+)\]\s\"(\w+)\s(\S+)\s([\w\d\/\.]*)\"\s(\d{3})\s((?:\d+|'\
    r'\-))$'

apache_ignore_criteria = {
    # Entries with status code other than 200 will be ignored
    'status_code': 200,
    # Entries with request method other than following will be ignored
    'method': ["GET", "POST"],
    # Entries with size of object less than following value will be ignored
    'size_of_object': 0
}


APACHE_COMBINED = 1

APACHE_COMBINED_OUTPUT_FORMAT = APACHE_COMMON_OUTPUT_FORMAT
APACHE_COMBINED_HEADING = APACHE_COMMON_HEADING
APACHE_COMBINED_LOG_RE = r'^([0-9\.]+)\s((?:\w+|-))\s([\w\d_\-\"\"]*)\s\[([\d'\
    r'\/\w:]*)\s((?:\-|\+)\d+)\]\s\"(\w+)\s(\S+)?\s([\w\d\/\.]*)\"\s(\d{3})\s'\
    r'((?:\d+|-)) (\".*\") (\".*\")$'

apache_ignore_criteria = {
    # Entries with status code other than 200 will be ignored
    'status_code': 200,
    # Entries with request method other than following will be ignored
    'method': ["GET", "POST"],
    # Entries with size of object less than following value will be ignored
    'size_of_object': 0
}

SQUID = 2
SQUID_OUTPUT_FORMAT = ("{0: <5}\t{3: <15}\t{1: <20}\t{2: ^10}\t"
                       "{5: <20} \t {4: <17} \t {6: <20} \t"
                       "{7: <40}\t{9: <30}\t{10:<}")

SQUID_HEADING = SQUID_OUTPUT_FORMAT.format(
    "ID", "Time", "Duration", "IP Address", "Result Code", "Bytes Delivered",
    "User", "Hierarchy Code", "Type Content", "Method", "URL")

SQUID_LOG_RE = r"^(\d+\.\d+)\s+(\d+)\s+([0-9\.]+)\s(\w+\/\d{3})\s(\d+)\s(\w+)"\
    r"\s(\S+)\s(\S+)\s(\w+\/\S+)\s(\S+)$"

squid_ignore_criteria = {
    # Entries with status code other than 200 will be ignored
    'status_code': 200,
    # Entries with request method other than following will be ignored
    'method': ["GET", "POST"],
    # Entries with size of object less than following value willbe ignored
    'size_of_object': 0
}

URL_OUTPUT_FORMAT = "{:>5}\t{:<}"
URL_OUTPUT_HEADING = URL_OUTPUT_FORMAT.format("URL_ID", "URL")

SESSION_OUTPUT_FORMAT = "{:>5}\t{: <20}\t{: <20}\t{:>}"
SESSION_OUTPUT_HEADING = SESSION_OUTPUT_FORMAT.format(
    "ID", "IP Address", "Session Time", "URL IDs")
