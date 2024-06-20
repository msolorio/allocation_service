import pytest
from typing import List
from datetime import date, timedelta
from tests.helpers import random_sku, random_batchref, random_orderid
from app.domain import model
from app.adapters.repository import AbstractRepository
from app.service_layer import services

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
        return next(b for b in self.batches if b.reference == reference)

    def list(self) -> List[model.Batch]:
        return list(self.batches)


def test_allocate_decrements_available_quantity_for_correct_batch():
    sku1, sku2 = random_sku(), random_sku()
    line = model.OrderLine("o1", sku1, 10)
    batch1 = model.Batch("b1", sku1, 100, eta=None)
    batch2 = model.Batch("b2", sku2, 100, eta=None)
    repo = FakeRepository([batch2, batch1])
    assert batch1.available_quantity == 100
    services.allocate(line, repo, FakeSession())
    assert batch1.available_quantity == 90
    assert batch2.available_quantity == 100


def test_allocate_returns_batchref_allocated_to():
    sku, batchref = random_sku(), random_batchref()
    line = model.OrderLine(orderid="o1", sku=sku, qty=10)
    batch = model.Batch(batch_ref=batchref, sku=sku, qty=100, eta=None)
    repo = FakeRepository([batch])
    result = services.allocate(line, repo, FakeSession())
    assert result == batchref


def test_allocate_returns_error_for_invalid_sku():
    line = model.OrderLine(orderid="o1", sku="NO_SUCH_SKU", qty=10)
    batch = model.Batch("batch1", "sku1", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku: NO_SUCH_SKU"):
        services.allocate(line, repo, FakeSession())


def test_allocate_commits_session():
    sku1 = random_sku()
    line = model.OrderLine(orderid="o1", sku=sku1, qty=10)
    batch = model.Batch("batch1", sku1, 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()
    services.allocate(line, repo, session)
    assert session.committed


def test_deallocate_increments_available_quantity_for_correct_batch():
    sku1, sku2 = random_sku(), random_sku()
    orderid = random_orderid()
    line = model.OrderLine(orderid=orderid, sku=sku1, qty=10)
    batch1 = model.Batch("b1", sku1, 100, eta=None)
    batch2 = model.Batch("b2", sku2, 100, eta=None)

    repo = FakeRepository([batch2, batch1])
    session = FakeSession()
    services.allocate(line, repo, session)
    assert batch1.available_quantity == 90
    services.deallocate(orderid, sku1, repo, session)
    assert batch1.available_quantity == 100
    assert batch2.available_quantity == 100


def test_trying_to_deallocate_unallocated_batch():
    sku = random_sku()
    batch = model.Batch("b1", sku, 100, eta=None)
    repo = FakeRepository([batch])
    services.deallocate("o1", sku, repo, FakeSession())
    assert batch.available_quantity == 100
