import pytest
from app.adapters import unit_of_work
from app.domain import model
from tests.helpers import random_batchref, random_sku


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (batch_ref, sku, initial_quantity, eta) VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_allocated_batch_ref(session, orderid, sku):
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid AND sku=:sku",
        dict(orderid=orderid, sku=sku),
    )
    [[batch_ref]] = session.execute(
        "SELECT batch_ref FROM allocations JOIN batches ON allocations.batch_id = batches.id WHERE allocations.orderline_id=:orderline_id",
        dict(orderline_id=orderline_id),
    )
    return batch_ref


def test_uow_can_retrieve_batch_and_allocate_to_it(session_factory):
    sku, batch_ref = random_sku(), random_batchref()
    session = session_factory()
    insert_batch(session, batch_ref, sku, 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        batch = uow.batches.get(reference=batch_ref)
        line = model.OrderLine(orderid="order1", sku=sku, qty=10)
        batch.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, "order1", sku)
    assert batchref == batch_ref


def test_rolls_back_uncommited_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow._session, "batch1", "WORKBENCH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow._session, "batch1", "LARGE-FORK", 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []
