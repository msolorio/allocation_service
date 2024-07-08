import pytest
from datetime import date

from app.domain.model import OrderLine, Batch, Product


def test_orderline_mapper_can_load_lines(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES "
        "('order1', 'RED-CHAIR', 12),"
        "('order1', 'BLUE-CHAIR', 24),"
        "('order2', 'RED-TABLE', 1)"
    )
    expected = [
        OrderLine(orderid="order1", sku="RED-CHAIR", qty=12),
        OrderLine(orderid="order1", sku="BLUE-CHAIR", qty=24),
        OrderLine(orderid="order2", sku="RED-TABLE", qty=1),
    ]

    assert session.query(OrderLine).all() == expected


def test_orderline_mapper_can_save_lines(session):
    new_line = OrderLine(orderid="order1", sku="ALARM-CLOCK", qty=10)
    session.add(new_line)
    session.commit()

    rows = list(session.execute("SELECT orderid, sku, qty FROM order_lines"))
    assert rows == [("order1", "ALARM-CLOCK", 10)]


def test_batch_mapper_can_load_batches(session):
    session.execute(
        "INSERT INTO batches (batch_ref, sku, initial_quantity, eta) VALUES "
        "('batch1', 'GENERIC-SOFA', 20, null),"
        "('batch2', 'LAMP', 100, '2020-01-01'),"
        "('batch3', 'CHAIR', 50, '2020-01-02')"
    )
    expected = [
        Batch(batch_ref="batch1", sku="GENERIC-SOFA", qty=20, eta=None),
        Batch(batch_ref="batch2", sku="LAMP", qty=100, eta=date(2020, 1, 1)),
        Batch(batch_ref="batch3", sku="CHAIR", qty=50, eta=date(2020, 1, 2)),
    ]

    assert session.query(Batch).all() == expected


def test_batch_mapper_save_batches(session):
    new_batch = Batch(batch_ref="batch1", sku="GENERIC-SOFA", qty=20)
    session.add(new_batch)
    session.commit()

    rows = list(
        session.execute("SELECT batch_ref, sku, initial_quantity, eta FROM batches")
    )
    assert rows == [("batch1", "GENERIC-SOFA", 20, None)]


def test_allocations_mapper_can_save_allocations(session):
    line = OrderLine(orderid="order1", sku="DECORATIVE-TRINKET", qty=2)
    batch = Batch(batch_ref="batch1", sku="DECORATIVE-TRINKET", qty=5)
    session.add(line)
    session.add(batch)
    batch.allocate(line)
    session.commit()

    rows = list(session.execute("SELECT orderline_id, batch_id FROM allocations"))
    assert rows == [(line.id, batch.id)]


def test_allocations_mapper_can_load_allocatins(session):
    sku = "DECORATIVE-TRINKET"
    qty = 12
    orderid = "order1"
    batchref = "batch1"
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES (:orderid, :sku, :qty)",
        dict(orderid=orderid, sku=sku, qty=qty),
    )
    [[olid]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    session.execute(
        "INSERT INTO batches (batch_ref, sku, initial_quantity) VALUES (:batchref, :sku, :qty)",
        dict(batchref=batchref, sku=sku, qty=qty),
    )
    [[bid]] = session.execute(
        "SELECT id FROM batches WHERE batch_ref=:batch_ref", dict(batch_ref="batch1")
    )
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id) VALUES (:olid, :bid)",
        dict(olid=olid, bid=bid),
    )

    batch = session.query(Batch).filter_by(id=bid).first()
    assert batch._allocations == {OrderLine(orderid=orderid, sku=sku, qty=qty)}


def test_product_mapper_can_load_products(session):
    session.execute("INSERT INTO products (sku) VALUES ('RED-CHAIR')")
    expected = [Product(sku="RED-CHAIR", batches=[])]

    assert session.query(Product).all() == expected


def test_product_mapper_can_save_products(session):
    new_product = Product(sku="BLUE-PLATE", batches=[])
    session.add(new_product)
    session.commit()

    rows = list(session.execute("SELECT sku FROM products"))
    assert rows == [("BLUE-PLATE",)]
