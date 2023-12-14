from model.model import Batch, OrderLine, allocate
from datetime import date, timedelta

today = date.today()
tomorrow = today + timedelta(days=1)
later = today + timedelta(days=10)


def test_allocates_line_to_batch():
    batch = Batch("batch-1", "SMALL-TABLE", 100, None)
    line = OrderLine("order-ref", "SMALL-TABLE", 10)

    allocate(line, [batch])

    assert batch.available_quantity == 90


def test_allocates_line_to_earliest_batch():
    earliest = Batch("batch-earliest", "SMALL-TABLE", 100, today)
    middle = Batch("batch-middle", "SMALL-TABLE", 100, tomorrow)
    latest = Batch("batch-latest", "SMALL-TABLE", 100, later)
    line = OrderLine("order-ref", "SMALL-TABLE", 10)

    allocate(line, [middle, earliest, latest])

    assert earliest.available_quantity == 90
    assert middle.available_quantity == 100
    assert latest.available_quantity == 100


def test_allocates_to_in_stock_batches_over_shipment_batches():
    in_stock_batch = Batch("batch-in_stock_batch", "SMALL-TABLE", 100, None)
    shipment_batch = Batch("batch-shipment_batch", "SMALL-TABLE", 100, today)
    line = OrderLine("order-ref", "SMALL-TABLE", 10)

    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_returns_batch_ref_of_the_batch_allocated_to():
    in_stock_batch = Batch("batch-in_stock_batch", "SMALL-TABLE", 100, None)
    shipment_batch = Batch("batch-shipment_batch", "SMALL-TABLE", 100, today)
    line = OrderLine("order-ref", "SMALL-TABLE", 10)

    assert allocate(line, [shipment_batch, in_stock_batch]) == in_stock_batch.ref


# raised out of stock exception if cannot allocate
