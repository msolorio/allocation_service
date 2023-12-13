from model.model import Batch, OrderLine, allocate
from datetime import date, timedelta

today = date.today()
tomorrow = today + timedelta(days=1)
later = today + timedelta(days=10)


def test_allocates_line_to_earliest_batch():
    earliest = Batch("batch-1", "SMALL-TABLE", 100, today)
    middle = Batch("batch-2", "SMALL-TABLE", 100, tomorrow)
    latest = Batch("batch-2", "SMALL-TABLE", 100, later)
    line = OrderLine("order-ref", "SMALL-TABLE", 10)

    allocate(line, [middle, earliest, latest])

    assert earliest.available_quantity == 90


# allocates to current stock batches over shipment batches

# allocate returns batch ref of the batch allocated to

# raised out of stock exception if cannot allocate
