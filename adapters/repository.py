from typing import List
import abc
import domain.model as model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Product):
        pass

    @abc.abstractmethod
    def get(self, reference: model.Reference) -> model.Product:
        pass


class SqlAlchemyProductsRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product: model.Product):
        self.session.add(product)

    def get(self, sku: model.Sku) -> model.Product:
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def list(self) -> List[model.Product]:
        return self.session.query(model.Product).all()
