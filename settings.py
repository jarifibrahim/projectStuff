from sqlalchemy import create_engine, orm
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base


# Format of the datetime string in the log file
DATETIME_FORMAT = '%d/%b/%Y:%H:%M:%S'
# Create in-memory database with support for concurrent access by threads
engine = create_engine('sqlite://',
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)
Session_Factory = orm.sessionmaker(bind=engine)
# Required for threading
Session = orm.scoped_session(Session_Factory)
session = Session()
Base = declarative_base()

APACHE_COMMON = 1
# Used while printing output
APACHE_COMMON_OUTPUT_FORMAT = ("{: ^5}\t{: ^15}\t{: ^30}\t{: ^30}"
                               "\t{: ^20}\t{: ^20}\t{: ^20}\t"
                               "{: ^20}\t{: ^20}\t{: ^20}\t{:<}")
# Header for output
APACHE_COMMON_HEADING = APACHE_COMMON_OUTPUT_FORMAT.format(
    "ID", "IP Address", "User Identifier", "User ID", "Date Time",
    "Time zone", "Method", "Status Code", "Size of Object", "Protocol",
    "Resource Requested")
APACHE_COMMON_LOG_RE = '([0-9\.]+)([\w\. \-]+)\s(\[.+])\s".+"\s\d{3}.+'


SQUID = 2

SQUID_OUTPUT_FORMAT = ("{: ^5}\t{: ^50}\t{: ^50}\t{: ^50}"
                               "\t{: ^50}\t{: ^50}\t{: ^50}\t"
                               "{: ^50}\t{: ^50}\t{: ^50}\t{:<}")

SQUID_HEADING = SQUID_OUTPUT_FORMAT.format(
    "ID", "Time", "Duration", "IP Address", "Result Code", "Bytes Delivered", 
    "Method", "URL", "User", "Hierarchy Code", "Type Content")

SQUID_LOG_RE = '\d+\.\d+\s+\d+\s+([0-9\.]+)\s\w{1,8}\/\d{3}\s\d+.+'


ignore_criteria = {
    # Entries with status code other than 200 will be ignored
    'status_code': 200,
    # Entries with request method other than following will be ignored
    'method': ["GET", "POST"],
    # Entries with size of object less than following value willbe ignored
    'size_of_object': 0
}

URL_OUTPUT_FORMAT = "{:>5}\t{:<}"
URL_OUTPUT_HEADING = URL_OUTPUT_FORMAT.format("URL_ID", "URL")

SESSION_OUTPUT_FORMAT = "{:>5}\t{: ^20}\t{: ^20}\t{: ^20}\t{:>}"
SESSION_OUTPUT_HEADING = SESSION_OUTPUT_FORMAT.format(
    "ID", "Session Time", "Start Time", "End Time", "URL IDs")
