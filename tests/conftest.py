import pytest, time, requests
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlalchemy.exc import OperationalError
from app.adapters.orm import metadata, start_mappers
from app import config


def wait_for_webapp_to_come_up():
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail("API never came up")


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@pytest.fixture
def restart_api():
    (Path(__file__).parent / "../src/app/entrypoints/flask_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()


@pytest.fixture
def psql_session(postgres_db):
    start_mappers()
    session = sessionmaker(bind=postgres_db)()
    yield session
    clear_mappers()

    session.execute("DELETE from allocations WHERE true")
    session.execute("DELETE FROM batches WHERE true")
    session.execute("DELETE FROM order_lines WHERE true")
    session.commit()


@pytest.fixture
def add_stock(psql_session):
    batches_added = set()
    skus_added = set()

    def _add_stock(lines):
        for ref, sku, qty, eta in lines:
            psql_session.execute(
                "INSERT INTO batches (batch_ref, sku, initial_quantity, eta)"
                " VALUES (:ref, :sku, :qty, :eta)",
                dict(ref=ref, sku=sku, qty=qty, eta=eta),
            )
            [[batch_id]] = psql_session.execute(
                "SELECT id FROM batches WHERE batch_ref=:ref AND sku=:sku",
                dict(ref=ref, sku=sku),
            )
            batches_added.add(batch_id)
            skus_added.add(sku)
        psql_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        psql_session.execute(
            "DELETE FROM allocations WHERE batch_id=:batch_id",
            dict(batch_id=batch_id),
        )
        psql_session.execute(
            "DELETE FROM batches WHERE id=:batch_id",
            dict(batch_id=batch_id),
        )
    for sku in skus_added:
        psql_session.execute(
            "DELETE FROM order_lines WHERE sku=:sku",
            dict(sku=sku),
        )
        psql_session.commit()
