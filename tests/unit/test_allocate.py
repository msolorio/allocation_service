import pytest
from datetime import date, timedelta

from app.domain.model import allocate, Batch, OrderLine, OutOfStock

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_prefers_in_stock_batches_to_shipment_batches():
    in_stock_batch = Batch("in-stock-batch", "RETRO-CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO-CLOCK", 100, eta=today)
    line = OrderLine("oref", "RETRO-CLOCK", 10)

    allocate(line, [shipment_batch, in_stock_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_shipment_batches():
    earliest = Batch("speedy-batch", "MINIMALIST-SPOON", 100, eta=today)
    medium = Batch("normal-batch", "MINIMALIST-SPOON", 100, eta=tomorrow)
    latest = Batch("slow-batch", "MINIMALIST-SPOON", 100, eta=later)
    line = OrderLine("order1", "MINIMALIST-SPOON", 10)

    allocate(line, [latest, medium, earliest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_batch_ref_of_allocated_batch():
    in_stock_batch = Batch("in-stock-batch", "HIGHBROW-POSTER", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "HIGHBROW-POSTER", 100, eta=today)
    line = OrderLine("oref", "HIGHBROW-POSTER", 10)

    result = allocate(line, [shipment_batch, in_stock_batch])

    assert result == in_stock_batch.batch_ref


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)

    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        allocate(OrderLine("order1", "SMALL-FORK", 20), [batch])
