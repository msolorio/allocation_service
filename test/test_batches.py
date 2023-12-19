from model.model import Batch, OrderLine


def make_batch_and_line(sku, batch_qty, line_qty):
    return (Batch("batch-ref", sku, batch_qty), OrderLine("order-ref", sku, line_qty))


def test_allocating_line_to_batch_decreases_batch_quantity():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)

    batch.allocate(line)

    assert batch.available_quantity == 18


def test_can_allocate_if_batch_quantity_greater_than_line_quantity():
    large_batch, small_line = make_batch_and_line("SMALL-TABLE", 20, 2)

    assert large_batch.can_allocate(small_line)


def test_cannot_allocate_if_batch_quantity_less_than_line_quantity():
    small_batch, large_line = make_batch_and_line("SMALL-TABLE", 2, 20)

    assert small_batch.can_allocate(large_line) is False


def test_can_allocate_if_batch_quantity_equal_to_line_quantity():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 20)

    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_dont_match():
    batch = Batch("batch-ref", "SMALL-TABLE", 20)
    line = OrderLine("order-ref", "BLUE-CUSHION", 20)

    assert batch.can_allocate(line) is False


def test_cannot_allocate_a_line_to_a_batch_more_than_once():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)

    batch.allocate(line)

    assert batch.can_allocate(line) is False


def test_attempting_to_allocate_second_time_doesnt_reduce_available_quantity():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)

    batch.allocate(line)
    batch.allocate(line)

    assert batch.available_quantity == 18


def test_deallocating_line_from_batch_increased_batch_quantity():
    batch, line = make_batch_and_line("SMALL-TABLE", 20, 2)

    batch.allocate(line)
    batch.deallocate(line)

    assert batch.available_quantity == 20


def test_can_only_deallocate_allocations():
    batch, line_1 = make_batch_and_line("SMALL-TABLE", 20, 2)
    line_2 = OrderLine("order-ref-2", "SMALL-TABLE", 2)

    batch.allocate(line_1)
    batch.deallocate(line_2)

    assert batch.available_quantity == 18
