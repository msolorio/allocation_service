import pytest, time, traceback, threading
from allocation.service_layer import unit_of_work
from allocation.domain import model
from tests.helpers import random_sku, random_orderid, random_batchref


def insert_batch(session, ref, sku, qty, eta, product_version=1):
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version_number)",
        dict(sku=sku, version_number=product_version),
    )

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
        "SELECT b.reference from allocations JOIN batches AS b ON batch_id = b.id "
        "WHERE orderline_id=:orderline_id",
        dict(orderline_id=orderline_id),
    )
    return batchref


def test_uow_can_retrieve_batch_and_allocate_to_it(
    sqlite_session_factory,
):
    session = sqlite_session_factory()
    sku, orderid = random_sku(), random_orderid()
    insert_batch(session, "b1", sku, 100, "2000-01-01")
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        product = uow.products.get(sku=sku)
        line = model.OrderLine(orderid, sku, 10)
        product.allocate(line)
        uow.commit()

    batchref = get_batchref_allocated_to(session, orderid, sku)
    assert batchref == "b1"


def test_uow_rolls_back_uncommitted_work_by_default(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    with uow:
        uow.products.add(model.Product(sku="WORKBENCH", batches=[]))

    new_session = sqlite_session_factory()

    assert list(new_session.execute("SELECT * FROM products")) == []


def test_uow_rolls_back_on_error(sqlite_session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)

    with pytest.raises(MyException):
        with uow:
            uow.products.add(model.Product(sku="LAMP", batches=[]))
            raise MyException()
            uow.commit()

    new_session = sqlite_session_factory()

    assert list(new_session.execute("SELECT * FROM products")) == []


def try_to_allocate(orderid, sku, exceptions):
    line = model.OrderLine(orderid, sku, 10)
    try:
        with unit_of_work.SqlAlchemyUnitOfWork() as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)


def test_concurrent_updates_to_version_are_not_allowed(postgres_session):
    sku = random_sku()
    batchref = random_batchref()
    insert_batch(postgres_session, batchref, sku, 100, "2000-01-01", product_version=4)
    postgres_session.commit()

    order1, order2 = "order1", "order2"
    exceptions = []
    try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions)
    try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[product_version]] = postgres_session.execute(
        "SELECT version_number FROM products where sku=:sku",
        dict(sku=sku),
    )

    allocations = list(
        postgres_session.execute(
            "SELECT b.reference FROM batches AS b "
            "FULL JOIN allocations AS a "
            "ON b.id = a.batch_id "
            "WHERE b.reference = :batchref",
            dict(batchref=batchref),
        )
    )

    assert product_version == 5
    assert len(allocations) == 1
