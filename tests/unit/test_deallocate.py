from datetime import date, timedelta
from app.domain.model import Batch, OrderLine, allocate, deallocate
from tests.helpers import random_sku

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_can_deallocate():
    earliest = Batch("batch1", "SMALL-FORK", 20, eta=today)
    medium = Batch("batch2", "SMALL-FORK", 20, eta=tomorrow)
    latest = Batch("batch3", "SMALL-FORK", 20, eta=later)
    batches = [medium, earliest, latest]
    line = OrderLine("order1", "SMALL-FORK", 2)
    allocate(line, batches)
    assert earliest.available_quantity == 18

    deallocate(line.orderid, line.sku, batches)
    assert earliest.available_quantity == 20


def test_can_only_deallocate_allocated_lines():
    sku = random_sku()
    earliest = Batch("batch1", sku, 20, eta=today)
    medium = Batch("batch2", sku, 20, eta=tomorrow)
    latest = Batch("batch3", sku, 20, eta=later)
    batches = [medium, earliest, latest]
    orderid = "order1"
    sku = sku
    deallocate(orderid, sku, batches)
    assert earliest.available_quantity == 20
    assert medium.available_quantity == 20
    assert latest.available_quantity == 20
