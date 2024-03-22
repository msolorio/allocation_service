from sqlalchemy import MetaData, Table, Column, String, Integer
from sqlalchemy.orm import mapper

from app.domain.model import OrderLine, Batch

metadata = MetaData()

order_lines = Table(
    "order_lines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderid", String(255), nullable=False),
    Column("sku", String(255), nullable=False),
    Column("qty", Integer, nullable=False),
)

batches = Table(
    "batches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("batch_ref", String(255), nullable=False),
    Column("sku", String(255), nullable=False),
    Column("initial_quantity", Integer, nullable=False),
    Column("eta", String(255)),
)


def start_mappers():
    mapper(OrderLine, order_lines)
    mapper(Batch, batches)
