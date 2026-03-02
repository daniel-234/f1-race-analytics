from datetime import date

from sqlmodel import Field, Relationship, SQLModel


class Championship(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    year: int

    races: list["Race"] = Relationship(back_populates="championship")

    entry_links: list["ChampionshipEntryLink"] = Relationship(
        back_populates="championship"
    )


class Race(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    circuit_id: str
    date: date
    circuit_name: str
    circuit_locality: str
    circuit_country: str

    championship_id: int | None = Field(default=None, foreign_key="championship.id")
    championship: Championship | None = Relationship(back_populates="races")

    # TODO: add relation race <> driver


class Constructor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    constructor_id: str
    name: str
    nationality: str

    entry_links: list["ChampionshipEntryLink"] = Relationship(
        back_populates="constructor"
    )


class Driver(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    number: str
    first_name: str
    last_name: str
    nationality: str

    entry_links: list["ChampionshipEntryLink"] = Relationship(back_populates="driver")
    # TODO: add relation race <> driver


class ChampionshipEntryLink(SQLModel, table=True):
    """
    Who drove for who in which season.
    It's 3-way because the driver<>constructor relationship changes every season.
    """

    championship_id: int | None = Field(
        default=None, foreign_key="championship.id", primary_key=True
    )
    constructor_id: int | None = Field(
        default=None, foreign_key="constructor.id", primary_key=True
    )
    driver_id: int | None = Field(
        default=None, foreign_key="driver.id", primary_key=True
    )

    championship: "Championship" = Relationship(back_populates="entry_links")
    constructor: "Constructor" = Relationship(back_populates="entry_links")
    driver: "Driver" = Relationship(back_populates="entry_links")
