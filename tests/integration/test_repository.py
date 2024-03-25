from app.adapters import repository
from app.domain.model import Batch, OrderLine


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (batch_ref, sku, initial_quantity, eta) VALUES (:batch_ref, :sku, :qty, :eta)",
        dict(batch_ref=ref, sku=sku, qty=qty, eta=eta),
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batches WHERE batch_ref = :batch_ref",
        dict(batch_ref=ref),
    )
    return batch_id


def insert_orderline(session, orderid, sku, qty):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES (:orderid, :sku, :qty)",
        dict(orderid=orderid, sku=sku, qty=qty),
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid = :orderid",
        dict(orderid=orderid),
    )
    return orderline_id


def test_repository_can_save_a_batch(session):
    repo = repository.SqlAlchemyRepository(session)
    batch = Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo.add(batch)
    session.commit()

    rows = list(
        session.execute("SELECT batch_ref, sku, initial_quantity, eta FROM batches")
    )
    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def test_repository_can_retrieve_batch_with_allocations(session):
    batch_id = insert_batch(session, "batch1", "ADORABLE-SETTEE", 100, None)
    orderline_id = insert_orderline(session, "order1", "ADORABLE-SETTEE", 30)
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id) VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
    )
    repo = repository.SqlAlchemyRepository(session)

    result = repo.get("batch1")

    expected = Batch("batch1", "ADORABLE-SETTEE", 100, eta=None)
    assert result == expected
    assert result.sku == expected.sku
    assert result.initial_quantity == expected.initial_quantity
    assert result.eta == expected.eta
    assert result._allocations == {OrderLine("order1", "ADORABLE-SETTEE", 30)}
