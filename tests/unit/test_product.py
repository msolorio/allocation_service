from datetime import date, timedelta
import pytest
from app.domain.model import Product, OrderLine, Batch, OutOfStock
from tests.helpers import random_sku

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_raises_out_of_stock_exception_if_cannot_allocate():
    product = Product(
        "SMALL-FORK", batches=[Batch("batch1", "SMALL-FORK", 10, eta=today)]
    )
    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        product.allocate(OrderLine("order1", "SMALL-FORK", 20))


def test_allolcate_decreases_available_quantity():
    product = Product(
        "SMALL-FORK", batches=[Batch("batch1", "SMALL-FORK", 20, eta=today)]
    )

    product.allocate(OrderLine("order1", "SMALL-FORK", 10))
    assert product.batches[0].available_quantity == 10


def test_deallocate():
    sku, batchref = random_sku(), "batch1"
    product = Product(sku, batches=[Batch(batchref, sku, 100, eta=None)])
    line = OrderLine("o1", sku, 10)
    product.allocate(line)
    assert product.batches[0].available_quantity == 90
    product.deallocate("o1", sku)
    assert product.batches[0].available_quantity == 100


def test_cannot_deallocate_unallocated_line():
    sku = random_sku()
    product = Product(sku, batches=[Batch("batch1", sku, 20, eta=today)])
    assert product.batches[0].available_quantity == 20
    product.deallocate("order1", sku)
    assert product.batches[0].available_quantity == 20
