import pytest, time, traceback, threading
from psycopg2.errors import SerializationFailure
from app.adapters import unit_of_work
from app.domain import model
from tests.helpers import random_batchref, random_sku, random_orderid
from sqlalchemy.exc import OperationalError


def insert_product(session, sku, version_number=1):
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version_number)",
        dict(sku=sku, version_number=version_number),
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


def try_to_allocate_slowly(orderid, sku, exceptions):
    line = model.OrderLine(orderid, sku, 10)
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    try:
        with uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


def test_concurrent_allocations_are_not_allowed(psql_session_factory):
    sku, batch_ref = random_sku(), random_batchref()
    session = psql_session_factory()
    insert_product(session, sku, version_number=1)
    insert_batch(session, batch_ref, sku, 100, None)
    session.commit()

    orderid1, orderid2 = random_orderid(), random_orderid()
    exceptions = []
    try_to_allocate_order1 = lambda: try_to_allocate_slowly(orderid1, sku, exceptions)
    try_to_allocate_order2 = lambda: try_to_allocate_slowly(orderid2, sku, exceptions)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version_number]] = session.execute(
        "SELECT version_number FROM products WHERE sku=:sku",
        dict(sku=sku),
    )
    assert version_number == 2
    [exception] = exceptions
    assert "could not serialize access due to concurrent update" in str(exception)

    allocations = list(
        session.execute(
            "SELECT orderid FROM allocations"
            " JOIN order_lines ON allocations.orderline_id = order_lines.id"
            " WHERE order_lines.sku = :sku",
            dict(sku=sku),
        )
    )
    assert len(allocations) == 1
