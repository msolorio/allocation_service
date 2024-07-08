import abc
from app.domain.model import Product


class AbstractProductRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: Product):
        pass

    @abc.abstractmethod
    def get(self, sku: str) -> Product:
        pass


class SqlAlchemyProductRepository(AbstractProductRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product: Product):
        self.session.add(product)

    def get(self, sku: str) -> Product:
        return self.session.query(Product).filter_by(sku=sku).first()
