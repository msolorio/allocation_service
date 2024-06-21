import pytest
from datetime import date, timedelta

from app.domain.model import allocate, Batch, OrderLine, OutOfStock

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def test_raises_out_of_stock_exception_if_cannot_allocate():
    batch = Batch("batch1", "SMALL-FORK", 10, eta=today)

    with pytest.raises(OutOfStock, match="SMALL-FORK"):
        allocate(OrderLine("order1", "SMALL-FORK", 20), [batch])
