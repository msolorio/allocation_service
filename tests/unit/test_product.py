import pytest
from datetime import date, timedelta
from allocation.domain.model import Batch, OrderLine, Product, OutOfStock
from tests.helpers import random_sku

today = date.today()
tomorrow = today + timedelta(days=1)
later = today + timedelta(days=2)


def test_prefers_in_stock_batches_to_shipment_batches():
    sku = random_sku()
    in_stock_batch = Batch("instock_batch", sku, 100, None)
    shipment_batch = Batch("shipment_batch", sku, 100, today)
    product = Product(sku=sku, batches=[shipment_batch, in_stock_batch])
    line = OrderLine("o1", sku, 10)
    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    sku = random_sku()
    earliest_batch = Batch("earliest", sku, 100, today)
    middle_batch = Batch("earliest", sku, 100, tomorrow)
    latest_batch = Batch("earliest", sku, 100, later)
    product = Product(sku=sku, batches=[latest_batch, earliest_batch, middle_batch])
    line = OrderLine("o1", sku, 10)
    product.allocate(line)

    assert earliest_batch.available_quantity == 90
    assert middle_batch.available_quantity == 100
    assert latest_batch.available_quantity == 100


def test_returns_allocated_batch_ref():
    sku = random_sku()
    in_stock_batch = Batch("instock_batch", sku, 100, None)
    shipment_batch = Batch("shipment_batch", sku, 100, today)
    product = Product(sku=sku, batches=[in_stock_batch, shipment_batch])
    line = OrderLine("o1", sku, 10)
    allocation = product.allocate(line)

    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_if_cannot_allocate():
    sku = random_sku()
    batch1 = Batch("b1", sku, 10, None)
    batch2 = Batch("b2", sku, 8, None)
    product = Product(sku=sku, batches=[batch1])
    line = OrderLine("o1", sku, 20)

    with pytest.raises(OutOfStock, match=sku):
        product.allocate(line)


def test_allocation_increments_version_number():
    sku = random_sku()
    batch1 = Batch("b1", sku, 100, None)
    product = Product(sku=sku, batches=[batch1])
    line = OrderLine("o1", sku, 10)

    product.version_number = 11
    product.allocate(line)

    assert product.version_number == 12
