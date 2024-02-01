from datetime import date
from allocation.domain import model
from allocation.adapters import repository


def test_repository_can_save_batch(session):
    # batch = model.Batch("batch-ref", "BLUE-CHAIR", 10, eta=None)
    repo = repository.SqlAlchemyProductsRepository(session)

    repo.add(model.Product(sku="DESK", batches=[]))
    session.commit()

    rows = list(session.execute("SELECT sku, version_number FROM products"))

    assert rows == [("DESK", 0)]


def insert_order_line(session):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES ('order1', 'BLACK-CHAIR', 15)"
    )
    [[orderline_id]] = list(
        session.execute(
            "SELECT id FROM order_lines WHERE orderid = 'order1' AND sku = 'BLACK-CHAIR'"
        )
    )

    return orderline_id


def insert_batch(session):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) VALUES ('batch1', 'BLACK-CHAIR', 15, '2023-01-01')"
    )
    [[batch_id]] = list(
        session.execute(
            "SELECT id FROM batches WHERE reference = 'batch1' AND sku = 'BLACK-CHAIR'"
        )
    )
    return batch_id


def insert_product(session):
    session.execute("INSERT INTO products (sku) VALUES ('BLACK-CHAIR')")


def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        f"INSERT INTO allocations (orderline_id, batch_id) VALUES ({orderline_id}, {batch_id})"
    )


def test_repository_can_retrieve_batch_with_allocations(session):
    insert_product(session)
    orderline_id = insert_order_line(session)
    batch_id = insert_batch(session)
    insert_allocation(session, orderline_id, batch_id)

    repo = repository.SqlAlchemyProductsRepository(session)
    # get batch with repo
    product = repo.get("BLACK-CHAIR")

    # test that it has correct properties with allocations
    expected_batch = model.Batch("batch1", "BLACK-CHAIR", 15, eta=date(2023, 1, 1))
    assert product.batches[0] == expected_batch  # Batch.__eq__ only compares references
    assert product.batches[0].sku == expected_batch.sku
    assert product.batches[0]._purchased_quantity == expected_batch._purchased_quantity
    assert product.batches[0].eta == expected_batch.eta
    assert product.batches[0]._allocations == {
        model.OrderLine("order1", "BLACK-CHAIR", 15)
    }
