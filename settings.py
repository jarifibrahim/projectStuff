from sqlalchemy import create_engine, orm

DB_NAME = "yast.db"
DATETIME_FORMAT = '%d/%b/%Y:%H:%M:%S'
engine = create_engine('sqlite:///./' + DB_NAME)
Session = orm.sessionmaker(bind=engine)
session = Session()
