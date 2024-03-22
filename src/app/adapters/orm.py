from sqlalchemy import MetaData, Table, Column, String, Integer
from sqlalchemy.orm import mapper

from app.domain.model import OrderLine

metadata = MetaData()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderid", String(255)),
    Column("sku", String(255)),
    Column("qty", Integer, nullable=False),
)


def start_mappers():
    mapper(OrderLine, order_lines)
