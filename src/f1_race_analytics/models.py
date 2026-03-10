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

    # M-to-1 link to Championsip
    championship_id: int | None = Field(default=None, foreign_key="championship.id")
    championship: Championship | None = Relationship(back_populates="races")

    # M-to-M link to RaceResult
    results: list["RaceResult"] = Relationship(back_populates="race")


class Constructor(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Identifies the constructor in the API endpoints - different from the DB id above
    constructor_id: str
    name: str
    nationality: str

    # 3-way M-to-M link to Championship and Driver
    entry_links: list["ChampionshipEntryLink"] = Relationship(
        back_populates="constructor"
    )


class Driver(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # Identifies the driver in the API endpoints - different from the DB id above
    driver_id: str
    number: str
    first_name: str
    last_name: str
    nationality: str

    # 3-way M-to-M link to Championship and Constructor
    entry_links: list["ChampionshipEntryLink"] = Relationship(back_populates="driver")

    # M-to-M link to RaceResult
    results: list["RaceResult"] = Relationship(back_populates="driver")


class ChampionshipEntryLink(SQLModel, table=True):
    """
    Who drove for who in which season.
    It's 3-way because the driver<>constructor relationship changes every season.
    """

    championship_id: int = Field(foreign_key="championship.id", primary_key=True)
    constructor_id: int = Field(foreign_key="constructor.id", primary_key=True)
    driver_id: int = Field(foreign_key="driver.id", primary_key=True)

    championship: "Championship" = Relationship(back_populates="entry_links")
    constructor: "Constructor" = Relationship(back_populates="entry_links")
    driver: "Driver" = Relationship(back_populates="entry_links")


class RaceResult(SQLModel, table=True):
    race_id: int | None = Field(default=None, foreign_key="race.id", primary_key=True)
    driver_id: int | None = Field(
        default=None, foreign_key="driver.id", primary_key=True
    )

    # Relationship context: data that belongs to the combination Race-Driver
    position: int
    points: int

    race: "Race" = Relationship(back_populates="results")
    driver: "Driver" = Relationship(back_populates="results")
