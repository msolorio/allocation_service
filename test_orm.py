import model.model as model
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
