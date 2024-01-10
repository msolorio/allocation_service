from service_layer import unit_of_work
import domain.model as model


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta) "
        "VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_batchref_allocated_to(session, orderid, sku):
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    [[batchref]] = session.execute(
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id "
        "WHERE orderline_id=:orderline_id",
        dict(orderline_id=orderline_id),
    )
    return batchref


def test_uow_can_retrieve_batch_and_allocate_to_it(session_factory):
    session = session_factory()
    insert_batch(session, "b1", "WORKBENCH", 100, "2000-01-01")
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        batch = uow.batches.get(reference="b1")
        line = model.OrderLine("o1", "WORKBENCH", 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_batchref_allocated_to(session, "o1", "WORKBENCH")
    assert batchref == "b1"
