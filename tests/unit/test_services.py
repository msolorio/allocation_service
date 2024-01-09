import pytest
import service_layer.services as services
from adapters.repository import FakeRepository
import domain.model as model
from tests.helpers import random_sku, random_batchref


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_commits():
    # line = model.OrderLine("o1", "LAMP", 10)
    batch = model.Batch("batch1", "LAMP", 100, "2000-01-01")
    repo = FakeRepository([batch])
    session = FakeSession()
    services.allocate("o1", "LAMP", 10, repo, session)

    assert session.commited


def test_returns_allocation():
    # line = model.OrderLine("o1", "LAMP", 10)
    batch = model.Batch("batch1", "LAMP", 100, "2000-01-01")
    repo = FakeRepository([batch])

    result = services.allocate("o1", "LAMP", 10, repo, FakeSession())
    assert result == "batch1"


def test_allocate_saves_allocations():
    sku = random_sku()
    earliest_batchref = random_batchref("earliest")
    later_batchref = random_batchref("later")
    repo = FakeRepository(
        [
            model.Batch(earliest_batchref, sku, 10, "2000-01-01"),
            model.Batch(later_batchref, sku, 10, "2000-01-02"),
        ]
    )
    # line1 = model.OrderLine("o1", sku, 10)
    # line2 = model.OrderLine("o2", sku, 10)

    result1 = services.allocate("o1", sku, 10, repo, FakeSession())
    assert result1 == earliest_batchref

    result2 = services.allocate("o2", sku, 10, repo, FakeSession())
    assert result2 == later_batchref


def test_invalid_sku():
    # line = model.OrderLine("o1", "LAMP", 10)
    batch = model.Batch("batch1", "COUCH", 100, "2000-01-01")
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku):
        services.allocate("o1", "LAMP", 10, repo, FakeSession())


def test_out_of_stock():
    batch = model.Batch("batch1", "LAMP", 10, "2000-01-01")
    # line = model.OrderLine("o1", "LAMP", 20)
    repo = FakeRepository([batch])

    with pytest.raises(model.OutOfStock):
        services.allocate("o1", "LAMP", 20, repo, FakeSession())
