from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.server_utils.shared import db


@dataclass
class Association(db.Model):
    __tablename__ = "associations"
    id = db.Column("id", db.Integer, primary_key=True)

    key: str = db.Column(db.String(100))
    url: str = db.Column(db.String(1000))

    stats: Mapped["Stats"] = relationship(back_populates="association")

    def __init__(self, key: str, url: str) -> None:
        self.key = key
        self.url = url


@dataclass
class Stats(db.Model):
    __tablename__ = "stats"
    id = db.Column("id", db.Integer, primary_key=True)

    key: str = db.Column(db.String(100))
    impressions: Mapped[List["Impression"]] = relationship()

    association_id: Mapped[int] = mapped_column(ForeignKey("associations.id"))
    association: Mapped["Association"] = relationship(back_populates="stats")

    def __init__(self, key: str, count: int) -> None:
        self.key = key
        self.count = count


class Impression(db.Model):
    __tablename__ = "impressions"
    id: Mapped[int] = mapped_column(primary_key=True)
    datetime = mapped_column(db.DateTime)

    stats_id: Mapped[int] = mapped_column(ForeignKey("stats.id"))
    stats: Mapped["Stats"] = relationship(back_populates="impressions")

    def __init__(self, datetime: datetime) -> None:
        self.datetime = datetime
