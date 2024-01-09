import pytest
import service_layer.services as services
from adapters.repository import FakeRepository
from tests.helpers import random_sku, random_batchref


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_commits():
    repo = FakeRepository([])
    session = FakeSession()
    services.add_batch("batch1", "LAMP", 100, "2000-01-01", repo, session)
    services.allocate("o1", "LAMP", 10, repo, session)

    assert session.commited


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "LAMP", 100, "2000-01-01", repo, session)
    assert repo.get("b1") is not None
    assert session.commited


def test_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "LAMP", 100, "2000-01-01", repo, session)
    result = services.allocate("o1", "LAMP", 10, repo, session)
    assert result == "batch1"


def test_allocate_saves_allocations():
    sku = random_sku()
    earliest_batchref = random_batchref("earliest")
    later_batchref = random_batchref("later")

    repo, session = FakeRepository([]), FakeSession()
    services.add_batch(earliest_batchref, sku, 10, "2000-01-01", repo, session)
    services.add_batch(later_batchref, sku, 10, "2000-01-02", repo, session)

    result1 = services.allocate("o1", sku, 10, repo, session)
    assert result1 == earliest_batchref

    result2 = services.allocate("o2", sku, 10, repo, session)
    assert result2 == later_batchref


def test_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("batch1", "COUCH", 100, "2000-01-01", repo, session)

    with pytest.raises(services.InvalidSku):
        services.allocate("o1", "LAMP", 10, repo, session)
