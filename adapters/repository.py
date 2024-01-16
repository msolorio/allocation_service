from typing import List
import abc
import domain.model as model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        pass

    @abc.abstractmethod
    def get(self, reference: model.Reference) -> model.Batch:
        pass


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch: model.Batch):
        self.session.add(batch)

    def get(self, reference: model.Reference) -> model.Batch:
        return self.session.query(model.Batch).filter_by(reference=reference).first()

    def list(self) -> List[model.Batch]:
        return self.session.query(model.Batch).all()
