import pytest
from app.adapters import unit_of_work
from app.domain import model
from tests.helpers import random_batchref, random_sku, random_orderid


def insert_product(session, sku):
    session.execute(
        "INSERT INTO products (sku) VALUES (:sku)",
        dict(sku=sku),
    )


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO batches (batch_ref, sku, initial_quantity, eta) VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )
    [[batch_id]] = session.execute(
        "SELECT id FROM batches WHERE batch_ref=:ref",
        dict(ref=ref),
    )
    return batch_id


def insert_orderline(session, orderid, sku, qty):
    session.execute(
        "INSERT INTO order_lines (orderid, sku, qty) VALUES (:orderid, :sku, :qty)",
        dict(orderid=orderid, sku=sku, qty=qty),
    )
    [[orderline_id]] = session.execute(
        "SELECT id FROM order_lines WHERE orderid=:orderid",
        dict(orderid=orderid),
    )
    return orderline_id


def insert_allocation(session, orderline_id, batch_id):
    session.execute(
        "INSERT INTO allocations (orderline_id, batch_id) VALUES (:orderline_id, :batch_id)",
        dict(orderline_id=orderline_id, batch_id=batch_id),
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


def test_uow_can_add_product(session_factory):
    sku = random_sku()
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        uow.products.add(model.Product(sku, batches=[]))
        uow.commit()
    session = session_factory()
    result = session.execute("SELECT sku FROM products")
    assert list(result) == [(sku,)]


def test_uow_can_retrieve_product_by_sku(session_factory):
    sku = random_sku()
    session = session_factory()
    insert_product(session, sku)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku)
        assert product.sku == sku


def test_uow_can_allocate_line_to_a_batch(session_factory):
    sku, batch_ref = random_sku(), random_batchref()
    session = session_factory()
    insert_product(session, sku)
    insert_batch(session, batch_ref, sku, 100, None)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku)
        line = model.OrderLine(orderid="order1", sku=sku, qty=10)
        product.allocate(line)
        uow.commit()

    batchref = get_allocated_batch_ref(session, "order1", sku)
    assert batchref == batch_ref


def test_uow_can_deallocate_line(session_factory):
    sku, batch_ref, orderid = random_sku(), random_batchref(), random_orderid()
    session = session_factory()
    insert_product(session, sku)
    batch_id = insert_batch(session, batch_ref, sku, 100, None)
    orderline_id = insert_orderline(session, orderid, sku, 10)
    insert_allocation(session, orderline_id, batch_id)
    session.commit()
    assert get_allocated_batch_ref(session, orderid, sku) == batch_ref

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku)
        product.deallocate(orderid, sku)
        uow.commit()

    result = session.execute(
        f"SELECT * FROM allocations WHERE orderline_id={orderline_id}",
    )
    assert list(result) == []


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


def test_can_add_batch_to_product(session_factory):
    sku = random_sku()
    session = session_factory()
    insert_product(session, sku)
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        product = uow.products.get(sku)
        product.add_batch(model.Batch("batch1", sku, 100, None))
        uow.commit()

    new_session = session_factory()
    rows = list(
        new_session.execute(
            'SELECT batch_ref, sku, initial_quantity, eta FROM "batches"'
        )
    )
    assert rows == [("batch1", sku, 100, None)]
