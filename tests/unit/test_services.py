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
