from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base


DB_NAME = "yast.db"
# Format of the datetime string in the log file
DATETIME_FORMAT = '%d/%b/%Y:%H:%M:%S'
engine = create_engine('sqlite:///./' + DB_NAME)
Session = orm.sessionmaker(bind=engine)
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
SQUID_LOG_RE = '\d+\.\d+\s+\d+\s+([0-9\.]+)\s\w{1,8}\/\d{3}\s\d+.+'
