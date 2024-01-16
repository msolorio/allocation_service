import pytest
from service_layer import unit_of_work
from domain import model


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


def test_uow_can_retrieve_batch_and_allocate_to_it(sqlite_session_factory):
    session = sqlite_session_factory()
    insert_batch(session, "b1", "WORKBENCH", 100, "2000-01-01")
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        batch = uow.batches.get(reference="b1")
        line = model.OrderLine("o1", "WORKBENCH", 10)
        batch.allocate(line)
        uow.commit()

    batchref = get_batchref_allocated_to(session, "o1", "WORKBENCH")
    assert batchref == "b1"


def test_uow_rolls_back_uncommitted_work_by_default(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        uow.batches.add(model.Batch("b1", "WORKBENCH", 10, None))

    new_session = sqlite_session_factory()

    assert list(new_session.execute("SELECT * FROM batches")) == []


def test_uow_rolls_back_on_error(sqlite_session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)

    with pytest.raises(MyException):
        with uow:
            uow.batches.add(model.Batch("b1", "WORKBENCH", 10, None))
            raise MyException()
            uow.commit()

    new_session = sqlite_session_factory()

    assert list(new_session.execute("SELECT * FROM batches")) == []
