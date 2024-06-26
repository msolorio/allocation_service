import pytest
from typing import List
from datetime import date, timedelta
from tests.helpers import random_sku, random_batchref, random_orderid
from app.domain import model
from app.adapters.repository import AbstractRepository
from app.service_layer import services
from app.adapters import unit_of_work

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeRepository(AbstractRepository):
    def __init__(self, batches: List[model.Batch] = []):
        self.batches = set(batches)

    def add(self, batch: model.Batch):
        self.batches.add(batch)

    def get(self, reference: str) -> model.Batch:
        return next((b for b in self.batches if b.batch_ref == reference), None)

    def list(self) -> List[model.Batch]:
        return list(self.batches)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository()
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch(
        batchref="b1",
        sku="CRUNCHY-ARMCHAIR",
        qty=100,
        eta=None,
        uow=uow,
    )
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_prefers_in_stock_over_shipment_batches():
    sku = random_sku()
    uow = FakeUnitOfWork()
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
    uow = FakeUnitOfWork()
    services.add_batch("speedy-batch", sku, 100, eta=today, uow=uow)
    services.add_batch("normal-batch", sku, 100, eta=tomorrow, uow=uow)
    services.add_batch("slow-batch", sku, 100, eta=later, uow=uow)
    batchref = services.allocate(orderid="o1", sku=sku, qty=10, uow=uow)
    assert batchref == "speedy-batch"


def test_allocate_returns_batchref_allocated_to():
    sku, batchref = random_sku(), random_batchref()
    uow = FakeUnitOfWork()
    services.add_batch(batchref=batchref, sku=sku, qty=100, eta=None, uow=uow)
    result = services.allocate(orderid="o1", sku=sku, qty=10, uow=uow)
    assert result == batchref


def test_allocate_returns_error_for_invalid_sku():
    uow = FakeUnitOfWork()
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
    uow = FakeUnitOfWork()
    services.add_batch(batchref="batch1", sku=sku, qty=100, eta=None, uow=uow)
    services.allocate(orderid="o1", sku=sku, qty=10, uow=uow)
    assert uow.committed


def test_deallocate():
    sku, orderid = random_sku(), random_orderid()
    uow = FakeUnitOfWork()
    services.add_batch(batchref="b1", sku=sku, qty=10, eta=None, uow=uow)
    services.allocate(orderid=orderid, sku=sku, qty=10, uow=uow)
    with pytest.raises(Exception):
        services.allocate(orderid=orderid, sku=sku, qty=10, uow=uow)

    services.deallocate(orderid=orderid, sku=sku, uow=uow)
    services.allocate(orderid=orderid, sku=sku, qty=10, uow=uow)
