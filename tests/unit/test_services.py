import pytest
from typing import List
from datetime import date, timedelta
from tests.helpers import random_sku, random_batchref, random_orderid
from app.domain import model

from app.adapters.product_repository import AbstractProductRepository
from app.service_layer import services
from app.adapters import unit_of_work

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeProductRepository(AbstractProductRepository):
    def __init__(self, products: List[model.Product] = []):
        self.products = set(products)

    def add(self, product: model.Product):
        self.products.add(product)

    def get(self, sku: str) -> model.Product:
        return next((p for p in self.products if p.sku == sku), None)


class FakeUnitOfWork2(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeProductRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch():
    uow = FakeUnitOfWork2()
    services.add_batch(
        batchref="b1",
        sku="CRUNCHY-ARMCHAIR",
        qty=100,
        eta=None,
        uow=uow,
    )
    product = uow.products.get("CRUNCHY-ARMCHAIR")
    assert product is not None
    assert len(product.batches) == 1
    assert product.batches[0].sku == "CRUNCHY-ARMCHAIR"
    assert uow.committed


def test_allocate_prefers_in_stock_over_shipment_batches():
    sku = random_sku()
    uow = FakeUnitOfWork2()
    services.add_batch("b1", sku, 100, eta=None, uow=uow)
    services.add_batch("b2", sku, 100, eta=today, uow=uow)
    batchref = services.allocate(
        orderid="o1",
        sku=sku,
        qty=10,
        uow=uow,
    )
    assert batchref == "b1"


def test_allocate_prefers_earlier_batches():
    sku = random_sku()
    uow = FakeUnitOfWork2()
    services.add_batch("speedy-batch", sku, 100, eta=today, uow=uow)
    services.add_batch("normal-batch", sku, 100, eta=tomorrow, uow=uow)
    services.add_batch("slow-batch", sku, 100, eta=later, uow=uow)
    batchref = services.allocate(orderid="o1", sku=sku, qty=10, uow=uow)
    assert batchref == "speedy-batch"


def test_allocate_returns_batchref_allocated_to():
    sku, batchref = random_sku(), random_batchref()
    uow = FakeUnitOfWork2()
    services.add_batch(batchref=batchref, sku=sku, qty=100, eta=None, uow=uow)
    result = services.allocate(orderid="o1", sku=sku, qty=10, uow=uow)
    assert result == batchref


def test_allocate_returns_error_for_invalid_sku():
    uow = FakeUnitOfWork2()
    services.add_batch(
        batchref="batch1",
        sku="sku1",
        qty=100,
        eta=None,
        uow=uow,
    )

    with pytest.raises(services.InvalidSku, match="Invalid sku: NO_SUCH_SKU"):
        services.allocate(orderid="o1", sku="NO_SUCH_SKU", qty=10, uow=uow)


def test_allocate_commits_session():
    sku = random_sku()
    uow = FakeUnitOfWork2()
    services.add_batch(batchref="batch1", sku=sku, qty=100, eta=None, uow=uow)
    services.allocate(orderid="o1", sku=sku, qty=10, uow=uow)
    assert uow.committed


def test_deallocate():
    sku, orderid1, orderid2 = random_sku(), random_orderid(), random_orderid()
    uow = FakeUnitOfWork2()
    services.add_batch(batchref="b1", sku=sku, qty=10, eta=None, uow=uow)
    services.allocate(orderid=orderid1, sku=sku, qty=10, uow=uow)
    with pytest.raises(Exception):
        services.allocate(orderid=orderid2, sku=sku, qty=10, uow=uow)

    services.deallocate(orderid=orderid1, sku=sku, uow=uow)
    services.allocate(orderid=orderid2, sku=sku, qty=10, uow=uow)
