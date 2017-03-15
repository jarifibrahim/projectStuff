from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, \
    Table, Interval
from sqlalchemy.orm import relationship
import datetime
import settings


def get_or_create(session, model, **kwargs):
    # Get the last item inserted
    instance = session.query(model).filter_by(
        **kwargs).order_by(model.id.desc()).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


class TokenCommon(settings.Base):
    __tablename__ = 'Token_common'

    def __init__(self, values):
        super(TokenCommon, self).__init__()
        self.ip_address = values[0]
        self.user_identifier = values[1]
        self.user_id = values[2]
        self.date_time = datetime.datetime.strptime(
            values[3], settings.DATETIME_FORMAT)
        self.time_zone = values[4]
        self.method = values[5]
        self.resource_requested = values[6].split("?")[0] if values[
            6] else ""
        self.request_ext = self.resource_requested.split(
            ".")[-1] if values[6] else ""
        self.protocol = values[7]
        self.status_code = values[8]
        self.size_of_object = values[9]

    token_id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), index=True)
    user_identifier = Column(String(50))
    user_id = Column(String(50))
    date_time = Column(DateTime)
    time_zone = Column(String(50))
    method = Column(String(10), index=True)
    resource_requested = Column(String(100), index=True)
    request_ext = Column(String(50), index=True)
    protocol = Column(String(50))
    status_code = Column(Integer, index=True)
    size_of_object = Column(Integer, index=True)

    def __str__(self):
        return settings.APACHE_COMMON_OUTPUT_FORMAT.format(
            str(self.token_id), self.ip_address, self.user_identifier,
            self.user_id, str(self.date_time), self.time_zone, self.method,
            str(self.status_code), str(self.size_of_object), self.protocol,
            self.resource_requested)


class TokenCombined(settings.Base):
    __tablename__ = 'Token_combined'

    def __init__(self, values):
        super(TokenCombined, self).__init__()
        self.ip_address = values[0]
        self.user_identifier = values[1]
        self.user_id = values[2]
        self.date_time = datetime.datetime.strptime(
            values[3], settings.DATETIME_FORMAT)
        self.time_zone = values[4]
        self.method = values[5]
        self.resource_requested = values[6].split("?")[0] if values[
            6] else ""
        self.request_ext = self.resource_requested.split(
            ".")[-1] if values[6] else ""
        self.protocol = values[7]
        self.status_code = values[8]
        self.size_of_object = values[9]
        self.referrer = values[10]
        self.user_agent = values[11]

    token_id = Column(Integer, primary_key=True)
    ip_address = Column(String(50), index=True)
    user_identifier = Column(String(50))
    user_id = Column(String(50))
    date_time = Column(DateTime)
    time_zone = Column(String(50))
    method = Column(String(10), index=True)
    resource_requested = Column(String(100), index=True)
    request_ext = Column(String(50), index=True)
    protocol = Column(String(50))
    status_code = Column(Integer, index=True)
    size_of_object = Column(Integer, index=True)
    referrer = Column(String(300))
    user_agent = Column(String(200))


class TokenSquid(settings.Base):
    __tablename__ = 'Token_squid'

    def __init__(self, values):
        super(TokenSquid, self).__init__()
        # The timestamp string contains milliseconds which cannot be
        # directly removed. So the string is converted to float and
        # then to an int
        self.date_time = datetime.datetime.fromtimestamp(int(float(values[0])))
        self.duration = int(values[1])
        self.ip_address = values[2]
        self.status_code = int(values[3].split("/")[-1])
        self.bytes_delivered = int(values[4])
        self.method = values[5]
        self.url = values[6].split("?")[0]
        self.user = values[7]
        self.hierarchy_code = values[8]
        self.type_content = values[9]
        self.request_ext = self.url.split(".")[-1]

    token_id = Column(Integer, primary_key=True)
    date_time = Column(DateTime)
    duration = Column(Integer)
    ip_address = Column(String(50), index=True)
    status_code = Column(Integer, index=True)
    bytes_delivered = Column(Integer, index=True)
    method = Column(String(10), index=True)
    url = Column(String(50), index=True)
    user = Column(String(100))  # User Identity (RFC931)
    hierarchy_code = Column(String(50))
    type_content = Column(String(50))
    request_ext = Column(String(20), index=True)


# Defines many to many relationship between Uurl and Session Table
association_table = Table('association', settings.Base.metadata,
                          Column('uurl_id', Integer, ForeignKey('uurl.id')),
                          Column('session_id', Integer,
                                 ForeignKey('session_master.id'))
                          )


class Uurl(settings.Base):
    """ Unique URL Table """
    __tablename__ = 'uurl'

    id = Column(Integer, primary_key=True)
    url = Column(String(300))
    sessions = relationship(
        "Session", secondary=association_table, back_populates="session_urls")

    def __str__(self):
        return settings.URL_OUTPUT_FORMAT.format(self.id, self.url)


class Session(settings.Base):
    """ Session Table """
    __tablename__ = 'session_master'

    id = Column(Integer, primary_key=True)
    session_time = Column(Interval)
    ip = Column(String(20), index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    session_urls = relationship(
        "Uurl", secondary=association_table, back_populates="sessions")

    def __str__(self):
        url = [int(x.id) for x in self.session_urls]
        return settings.SESSION_OUTPUT_FORMAT.format(
            self.id, self.ip, str(self.session_time), str(url))
