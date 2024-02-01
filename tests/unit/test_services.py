import pytest
from typing import List
from allocation.domain import model
from allocation.service_layer import services
from allocation.adapters.repository import AbstractRepository
from allocation.service_layer.unit_of_work import AbstractUnitOfWork
from tests.helpers import random_sku, random_batchref


class FakeRepository(AbstractRepository):
    def __init__(self, products: List[model.Product]):
        self._products = set(products)

    def add(self, product: model.Product):
        self._products.add(product)

    def get(self, sku: str) -> model.Product:
        return next((p for p in self._products if p.sku == sku), None)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.commited = False

    def commit(self):
        self.commited = True

    def rollback(self):
        pass


def test_add_batch_for_new_product():
    sku = random_sku()
    uow = FakeUnitOfWork()

    services.add_batch("b1", sku, 100, "2000-01-01", uow)

    assert uow.products.get(sku=sku) is not None
    assert "b1" in [b.reference for b in uow.products.get(sku=sku).batches]
    assert uow.commited


def test_add_batch_for_existing_product():
    sku = random_sku()
    uow = FakeUnitOfWork()
    uow.products.add(model.Product(sku=sku, batches=[model.Batch("b1", sku, 10, None)]))

    services.add_batch("b2", sku, 10, "2000-01-01", uow)

    assert "b2" in [b.reference for b in uow.products.get(sku=sku).batches]


def test_allocate_allocates_to_a_batch():
    sku = random_sku()
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 10, None, uow)
    services.add_batch("b2", sku, 10, "2000-01-01", uow)
    services.allocate("o1", sku, 10, uow)
    batch = services.allocate("o2", sku, 10, uow)

    assert batch == "b2"


def test_allocate_returns_allocation():
    sku = random_sku()
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, "2000-01-01", uow)
    result = services.allocate("o1", sku, 10, uow)

    assert result == "b1"


def test_allocate_errors_for_invalid_sku():
    sku, invalid_sku = random_sku(), random_sku()
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, "2000-01-01", uow)

    with pytest.raises(services.InvalidSku, match=invalid_sku):
        services.allocate("o1", invalid_sku, 10, uow)


def test_allocate_commits():
    sku = random_sku()
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, "2000-01-01", uow)
    services.allocate("o1", sku, 10, uow)

    assert uow.commited
