import abc
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.adapters import repository
from app import config


class AbstractUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository

    def __enter__(self):
        pass

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        pass

    @abc.abstractmethod
    def rollback(self):
        pass


DEFAULT_SESSION_FACTORY = sessionmaker(bind=create_engine(config.get_postgres_uri()))


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self._session_factory = session_factory

    def __enter__(self):
        self._session = self._session_factory()
        self.batches = repository.SqlAlchemyRepository(self._session)

    def __exit__(self, *args):
        super().__exit__(*args)
        self._session.close()

    def rollback(self):
        self._session.rollback()

    def commit(self):
        self._session.commit()
