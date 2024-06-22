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
        return next((b for b in self.batches if b.batch_ref == reference), None)

    def list(self) -> List[model.Batch]:
        return list(self.batches)


def test_add_batch():
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch(
        batchref="b1",
        sku="CRUNCHY-ARMCHAIR",
        qty=100,
        eta=None,
        repo=repo,
        session=session,
    )
    assert repo.get("b1") is not None
    assert repo.get("b1").sku == "CRUNCHY-ARMCHAIR"
    assert session.committed


def test_allocate_prefers_in_stock_over_shipment_batches():
    sku1, sku2 = random_sku(), random_sku()
    repo = FakeRepository()
    services.add_batch("b1", sku1, 100, eta=None, repo=repo, session=FakeSession())
    services.add_batch("b2", sku2, 100, eta=today, repo=repo, session=FakeSession())
    batchref = services.allocate(
        orderid="o1", sku=sku1, qty=10, repo=repo, session=FakeSession()
    )
    assert batchref == "b1"


def test_allocate_prefers_earlier_batches():
    sku = random_sku()
    repo = FakeRepository()
    services.add_batch(
        "speedy-batch", sku, 100, eta=today, repo=repo, session=FakeSession()
    )
    services.add_batch(
        "normal-batch", sku, 100, eta=tomorrow, repo=repo, session=FakeSession()
    )
    services.add_batch(
        "slow-batch", sku, 100, eta=later, repo=repo, session=FakeSession()
    )
    batchref = services.allocate(
        orderid="o1", sku=sku, qty=10, repo=repo, session=FakeSession()
    )
    assert batchref == "speedy-batch"


def test_allocate_returns_batchref_allocated_to():
    sku, batchref = random_sku(), random_batchref()
    repo = FakeRepository()
    services.add_batch(
        batchref=batchref, sku=sku, qty=100, eta=None, repo=repo, session=FakeSession()
    )
    result = services.allocate(
        orderid="o1", sku=sku, qty=10, repo=repo, session=FakeSession()
    )
    assert result == batchref


def test_allocate_returns_error_for_invalid_sku():
    repo = FakeRepository()
    services.add_batch(
        batchref="batch1",
        sku="sku1",
        qty=100,
        eta=None,
        repo=repo,
        session=FakeSession(),
    )

    with pytest.raises(services.InvalidSku, match="Invalid sku: NO_SUCH_SKU"):
        services.allocate(
            orderid="o1", sku="NO_SUCH_SKU", qty=10, repo=repo, session=FakeSession()
        )


def test_allocate_commits_session():
    sku = random_sku()
    repo = FakeRepository()
    session = FakeSession()
    services.add_batch(
        batchref="batch1",
        sku=sku,
        qty=100,
        eta=None,
        repo=repo,
        session=session,
    )
    services.allocate(orderid="o1", sku=sku, qty=10, repo=repo, session=session)
    assert session.committed


def test_deallocate():
    sku, orderid = random_sku(), random_orderid()
    repo = FakeRepository()
    services.add_batch(
        batchref="b1", sku=sku, qty=10, eta=None, repo=repo, session=FakeSession()
    )
    services.allocate(
        orderid=orderid, sku=sku, qty=10, repo=repo, session=FakeSession()
    )
    with pytest.raises(Exception):
        services.allocate(
            orderid=orderid, sku=sku, qty=10, repo=repo, session=FakeSession()
        )

    services.deallocate(orderid=orderid, sku=sku, repo=repo, session=FakeSession())
    services.allocate(
        orderid=orderid, sku=sku, qty=10, repo=repo, session=FakeSession()
    )
