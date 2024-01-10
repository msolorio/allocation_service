import pytest
import service_layer.services as services
from service_layer.unit_of_work import FakeUnitOfWork
from tests.helpers import random_sku, random_batchref


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "LAMP", 100, "2000-01-01", uow)
    assert uow.batches.get("b1") is not None
    assert uow.commited


def test_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "LAMP", 100, "2000-01-01", uow)
    result = services.allocate("o1", "LAMP", 10, uow)
    assert result == "batch1"


def test_allocate_saves_allocations():
    sku = random_sku()
    earliest_batchref = random_batchref("earliest")
    later_batchref = random_batchref("later")
    uow = FakeUnitOfWork()
    services.add_batch(earliest_batchref, sku, 10, "2000-01-01", uow)
    services.add_batch(later_batchref, sku, 10, "2000-01-02", uow)

    result1 = services.allocate("o1", sku, 10, uow)
    assert result1 == earliest_batchref

    result2 = services.allocate("o2", sku, 10, uow)
    assert result2 == later_batchref


def test_invalid_sku():
    uow = FakeUnitOfWork()
    services.add_batch("batch1", "COUCH", 100, "2000-01-01", uow)

    with pytest.raises(services.InvalidSku):
        services.allocate("o1", "LAMP", 10, uow)
