from sqlmodel import Field, Relationship, SQLModel 


class Championship(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    year: int

    races: list["Race"] = Relationship(back_populates="championship")

    entry_links: list["ChampionshipEntryLink"] = Relationship(back_populates="championship")


class Race(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str 

    championship_id: int | None = Field(default=None, foreign_key="championship.id")
    championship: Championship | None = Relationship(back_populates="races")


class Constructor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    nationality: str 

    entry_links: list["ChampionshipEntryLink"] = Relationship(back_populates="constructor")


class Driver(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    nationality: str

    entry_links: list["ChampionshipEntryLink"] = Relationship(back_populates="driver")


class ChampionshipEntryLink(SQLModel, table=True):
    championship_id: int | None = Field(default=None, foreign_key="championship.id", primary_key=True)
    constructor_id: int | None = Field(default=None, foreign_key="constructor.id", primary_key=True)
    driver_id: int | None = Field(default=None, foreign_key="driver.id", primary_key=True)

    championship: "Championship" = Relationship(back_populates="entry_links")
    constructor: "Constructor" = Relationship(back_populates="entry_links")
    driver: "Driver" = Relationship(back_populates="entry_links") 