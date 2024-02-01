from allocation.domain import model
from datetime import date


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES "
        '("order1", "RED-CHAIR", 12),'
        '("order1", "BLUE-TABLE", 12),'
        '("order2", "BLUE-SOFA", 14)'
    )

    expected = [
        model.OrderLine("order1", "RED-CHAIR", 12),
        model.OrderLine("order1", "BLUE-TABLE", 12),
        model.OrderLine("order2", "BLUE-SOFA", 14),
    ]

    assert session.query(model.OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session):
    new_line = model.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()

    rows = list(session.execute("SELECT orderid, sku, qty FROM order_lines"))

    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]


def test_batch_mapper_can_load_batches(session):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES "
        '("batch1", "RED-CHAIR", 20, NULL),'
        '("batch2", "BLUE-TABLE", 15, "2023-01-01"),'
        '("batch3", "GREEN-SOFA", 10, "2023-02-01")'
    )

    expected = [
        model.Batch("batch1", "RED-CHAIR", 20),
        model.Batch("batch2", "BLUE-TABLE", 15, date(2023, 1, 1)),
        model.Batch("batch3", "GREEN-SOFA", 10, date(2023, 2, 1)),
    ]

    assert session.query(model.Batch).all() == expected


def test_batch_mapper_can_save_batch(session):
    new_batch = model.Batch("batch4", "YELLOW-CHAIR", 25, date(2023, 1, 1))

    session.add(new_batch)
    session.commit()

    rows = list(
        session.execute("SELECT reference, sku, _purchased_quantity, eta FROM batches")
    )

    assert rows == [("batch4", "YELLOW-CHAIR", 25, "2023-01-01")]


def test_allocations_mapper_can_save_allocations(session):
    order_line = model.OrderLine("order1", "PURPLE-CHAIR", 8)
    batch = model.Batch("batch1", "PURPLE-CHAIR", 10, date(2023, 4, 1))

    # methods under test
    batch.allocate(order_line)
    session.add(batch)
    session.commit()

    rows = list(session.execute("SELECT orderline_id, batch_id from allocations"))

    assert rows == [(order_line.id, batch.id)]


def test_allocations_mapper_can_load_allocations(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES ('order1', 'BLACK-CHAIR', 15)"
    )
    [[orderline_id]] = list(
        session.execute(
            "SELECT id FROM order_lines WHERE orderid = 'order1' AND sku = 'BLACK-CHAIR'"
        )
    )

    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES ('batch1', 'BLACK-CHAIR', 15, '2023-01-01')"
    )
    [[batch_id]] = list(
        session.execute(
            "SELECT id FROM batches WHERE reference = 'batch1' AND sku = 'BLACK-CHAIR'"
        )
    )

    session.execute(
        f"INSERT INTO allocations (orderline_id, batch_id) VALUES ({orderline_id}, {batch_id})"
    )

    batch = session.query(model.Batch).filter_by(id=batch_id).first()

    assert batch._allocations == {model.OrderLine("order1", "BLACK-CHAIR", 15)}
