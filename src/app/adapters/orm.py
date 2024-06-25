import time
from sqlalchemy import MetaData, Table, Column, String, Integer, ForeignKey
from sqlalchemy.orm import mapper, relationship
from sqlalchemy.exc import OperationalError
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

allocations = Table(
    "allocations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("orderline_id", Integer, ForeignKey("order_lines.id")),
    Column("batch_id", Integer, ForeignKey("batches.id")),
)


def start_mappers():
    lines_mapper = mapper(OrderLine, order_lines)
    mapper(
        Batch,
        batches,
        properties={
            "_allocations": relationship(
                lines_mapper,
                secondary=allocations,
                collection_class=set,
            )
        },
    )


def wait_for_db(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    raise OperationalError("Database never came up")


def create_tables(engine):
    metadata.create_all(engine)


def init(db_engine):
    wait_for_db(db_engine)
    create_tables(db_engine)
    start_mappers()
