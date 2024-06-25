import pytest, time, requests
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers
from sqlalchemy.exc import OperationalError
from app.adapters.orm import metadata, start_mappers, wait_for_db
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


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_db(engine)
    metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


@pytest.fixture
def session_factory(in_memory_db):
    start_mappers()
    yield sessionmaker(bind=in_memory_db)
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
