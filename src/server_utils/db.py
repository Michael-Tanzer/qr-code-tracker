from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from src.server_utils.shared import db


@dataclass
class Association(db.Model):
    __tablename__ = "associations"
    id = db.Column("id", db.Integer, primary_key=True)

    key: str = db.Column(db.String(1000))
    url: str = db.Column(db.String(1000))
    qr_style_config: Optional[str] = db.Column(Text, nullable=True)

    stats: Mapped["Stats"] = relationship(back_populates="association")

    def __init__(self, key: str, url: str, qr_style_config: Optional[dict] = None) -> None:
        """
        Initialize an Association.
        
        Args:
            key: Unique identifier for the QR code
            url: Target URL for the QR code
            qr_style_config: Optional dictionary of QR code styling options
        """
        self.key = key
        self.url = url
        if qr_style_config is not None:
            self.qr_style_config = json.dumps(qr_style_config)
        else:
            self.qr_style_config = None
    
    def get_qr_style_config(self) -> Optional[dict]:
        """
        Get QR style configuration as a dictionary.
        
        Returns:
            Optional[dict]: QR style configuration dictionary, or None if not set
        """
        if self.qr_style_config:
            return json.loads(self.qr_style_config)
        return None


@dataclass
class Stats(db.Model):
    __tablename__ = "stats"
    id = db.Column("id", db.Integer, primary_key=True)

    key: str = db.Column(db.String(1000))
    password: str = db.Column(db.String(1000))
    impressions: Mapped[List["Impression"]] = relationship()

    association_id: Mapped[int] = mapped_column(ForeignKey("associations.id"))
    association: Mapped["Association"] = relationship(back_populates="stats")

    def __init__(self, key: str, password: str = None) -> None:
        """
        Initialize Stats for a QR code.
        
        Args:
            key: Unique identifier matching the Association key
            password: Optional hashed password for accessing stats
        """
        self.key = key
        self.password = password


class Impression(db.Model):
    __tablename__ = "impressions"
    id: Mapped[int] = mapped_column(primary_key=True)
    datetime = mapped_column(db.DateTime)

    stats_id: Mapped[int] = mapped_column(ForeignKey("stats.id"))
    stats: Mapped["Stats"] = relationship(back_populates="impressions")

    def __init__(self, datetime: datetime) -> None:
        """
        Initialize an Impression record.
        
        Args:
            datetime: Timestamp when the QR code was scanned
        """
        self.datetime = datetime
