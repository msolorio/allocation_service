import pytest

from app.domain.model import OrderLine


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
