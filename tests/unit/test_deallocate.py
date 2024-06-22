import pytest
from datetime import date, timedelta

from app.domain.model import allocate, Batch, OrderLine, deallocate
from tests.helpers import random_orderid, random_sku

today = date.today()


def test_deallocate_increases_available_quantity():
    sku, orderid = random_sku(), random_orderid()
    batch = Batch("batch1", sku, 20, eta=today)
    allocate(OrderLine(orderid, sku, 10), [batch])
    assert batch.available_quantity == 10
    deallocate(orderid, sku, [batch])
    assert batch.available_quantity == 20


def test_cannot_deallocate_unallocated_line():
    sku = random_sku()
    batch = Batch("batch1", sku, 20, eta=today)
    assert batch.available_quantity == 20
    deallocate("order1", sku, [batch])
    assert batch.available_quantity == 20
