import pytest

from app.domain.model import Batch, OrderLine


def test_allocating_line_to_batch_reduces_batch_quantity():
    batch = Batch(batch_ref="batch-001", sku="SMALL-TABLE", qty=20)
    line = OrderLine(orderid="order-123", sku="SMALL-TABLE", qty=2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_cannot_allocate_to_batch_if_not_enough_available_quantity():
    batch = Batch(batch_ref="batch-001", sku="SMALL-TABLE", qty=5)
    line = OrderLine(orderid="order-123", sku="SMALL-TABLE", qty=10)

    batch.allocate(line)

    assert batch.available_quantity == 5


def test_can_allocate_if_avaiable_quantity_is_equal_to_line_quantity():
    batch = Batch(batch_ref="batch-001", sku="SMALL-TABLE", qty=5)
    line = OrderLine(orderid="order-123", sku="SMALL-TABLE", qty=5)

    batch.allocate(line)

    assert batch.available_quantity == 0


def test_cannot_allocate_line_to_batch_more_than_once():
    batch = Batch(batch_ref="batch-001", sku="SMALL-TABLE", qty=20)
    line = OrderLine(orderid="order-123", sku="SMALL-TABLE", qty=2)

    batch.allocate(line)
    batch.allocate(line)

    assert batch.available_quantity == 18
