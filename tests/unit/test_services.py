import pytest
from typing import List
import domain.model as model
from service_layer import services
from adapters.repository import AbstractRepository
from service_layer.unit_of_work import AbstractUnitOfWork
from tests.helpers import random_sku, random_batchref


class FakeRepository(AbstractRepository):
    def __init__(self, products: List[model.Product]):
        self._products = set(products)

    def add(self, product: model.Product):
        self._products.add(product)

    def get(self, sku: str) -> model.Product:
        return next((p for p in self._products if p.sku == sku), None)


# class FakeRepository(AbstractRepository):
#     def __init__(self, batches: List[model.Batch]):
#         self._batches = set(batches)

#     def add(self, batch: model.Batch):
#         self._batches.add(batch)

#     def get(self, reference: model.Reference) -> model.Batch:
#         return next((b for b in self._batches if b.reference == reference), None)

#     def list(self) -> List[model.Batch]:
#         return list(self._batches)


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.commited = False

    def commit(self):
        self.commited = True

    def rollback(self):
        pass


# class FakeUnitOfWork(AbstractUnitOfWork):
#     def __init__(self):
#         self.batches = FakeRepository([])
#         self.commited = False

#     def commit(self):
#         self.commited = True

#     def rollback(self):
#         pass


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


# def test_returns_allocation():
#     uow = FakeUnitOfWork()
#     services.add_batch("batch1", "LAMP", 100, "2000-01-01", uow)
#     result = services.allocate("o1", "LAMP", 10, uow)
#     assert result == "batch1"


# def test_allocate_saves_allocations():
#     sku = random_sku()
#     earliest_batchref = random_batchref("earliest")
#     later_batchref = random_batchref("later")
#     uow = FakeUnitOfWork()
#     services.add_batch(earliest_batchref, sku, 10, "2000-01-01", uow)
#     services.add_batch(later_batchref, sku, 10, "2000-01-02", uow)

#     result1 = services.allocate("o1", sku, 10, uow)
#     assert result1 == earliest_batchref

#     result2 = services.allocate("o2", sku, 10, uow)
#     assert result2 == later_batchref


# def test_invalid_sku():
#     uow = FakeUnitOfWork()
#     services.add_batch("batch1", "COUCH", 100, "2000-01-01", uow)

#     with pytest.raises(services.InvalidSku):
#         services.allocate("o1", "LAMP", 10, uow)
