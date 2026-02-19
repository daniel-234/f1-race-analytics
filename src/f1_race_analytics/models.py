from sqlmodel import Field, Relationship, SQLModel 

class Championship(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    year: int

    races: list["Race"] = Relationship(back_populates="championship")


class Race(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str 

    championship_id: int | None = Field(default=None, foreign_key="championship.id")
    championship: Championship | None = Relationship(back_populates="races")