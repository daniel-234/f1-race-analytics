from sqlmodel import SQLModel, create_engine

sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)