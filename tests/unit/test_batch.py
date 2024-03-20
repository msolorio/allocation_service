import pytest

from app.domain.model import Batch, OrderLine


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch(batch_ref="batch-001", sku=sku, qty=batch_qty),
        OrderLine(orderid="order-123", sku=sku, qty=line_qty),
    )


def test_allocating_line_to_batch_reduces_batch_quantity():
    batch, line = make_batch_and_line(sku="ELEGANT-LAMP", batch_qty=20, line_qty=2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_cannot_allocate_to_batch_if_not_enough_available_quantity():
    small_batch, large_line = make_batch_and_line(
        sku="ELEGANT-LAMP", batch_qty=5, line_qty=10
    )

    small_batch.allocate(large_line)

    assert small_batch.available_quantity == 5


def test_can_allocate_if_avaiable_quantity_is_equal_to_line_quantity():
    batch, line = make_batch_and_line(sku="ELEGANT-LAMP", batch_qty=10, line_qty=10)

    batch.allocate(line)

    assert batch.available_quantity == 0


def test_cannot_allocate_line_to_batch_more_than_once():
    batch, line = make_batch_and_line(sku="ELEGANT-LAMP", batch_qty=20, line_qty=2)

    batch.allocate(line)
    batch.allocate(line)

    assert batch.available_quantity == 18


def test_cannot_allocate_if_skus_do_not_match():
    batch = Batch(batch_ref="batch-001", sku="CHAIR", qty=20)
    different_sku_line = OrderLine(orderid="order-123", sku="TABLE", qty=2)

    batch.allocate(different_sku_line)

    assert batch.available_quantity == 20


def test_deallocate_line_from_batch():
    batch, line = make_batch_and_line(sku="ELEGANT-LAMP", batch_qty=20, line_qty=2)

    batch.allocate(line)
    assert batch.available_quantity == 18

    batch.deallocate(line)
    assert batch.available_quantity == 20


def test_can_only_dealocate_allocated_lines():
    batch, unallocated_line = make_batch_and_line(
        sku="ELEGANT-LAMP", batch_qty=20, line_qty=2
    )

    batch.deallocate(unallocated_line)

    assert batch.available_quantity == 20
