from model.model import Batch, OrderLine


def test_allocating_line_to_batch_decrements_batch_quantity():
    batch = Batch(ref="batch-ref", sku="SMALL-TABLE", qty=20)
    order_line = OrderLine(sku="SMALL-TABLE", qty=2)

    batch.allocate(order_line)

    assert batch.available_quantity == 18


def test_cannot_allocate_line_to_batch_if_not_enough_available_quantity():
    batch = Batch(ref="batch-ref", sku="BLUE-CUSHION", qty=1)
    order_line = OrderLine(sku="BLUE-CUSHION", qty=2)

    batch.allocate(order_line)

    assert batch.available_quantity == 1
