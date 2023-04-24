from __future__ import annotations

from dataclasses import dataclass

from src.server_utils.shared import db


@dataclass
class Association(db.Model):
    __tablename__ = "associations"
    id = db.Column("id", db.Integer, primary_key=True)

    key: str = db.Column(db.String(100))
    url: str = db.Column(db.String(1000))

    def __init__(self, key: str, url: str) -> None:
        self.key = key
        self.url = url


@dataclass
class Stats(db.Model):
    __tablename__ = "stats"
    id = db.Column("id", db.Integer, primary_key=True)

    key: str = db.Column(db.String(100))
    count: int = db.Column(db.Integer)

    def __init__(self, key: str, count: int) -> None:
        self.key = key
        self.count = count
