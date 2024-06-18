import abc
from typing import List
from app.domain.model import Batch


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: Batch):
        pass

    @abc.abstractmethod
    def get(self, reference: str) -> Batch:
        pass

    @abc.abstractmethod
    def list(self) -> List[Batch]:
        pass


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch: Batch):
        self.session.add(batch)

    def get(self, reference: str) -> Batch:
        return self.session.query(Batch).filter_by(batch_ref=reference).one()

    def list(self) -> List[Batch]:
        return self.session.query(Batch).all()
