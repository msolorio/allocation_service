import pytest
from service_layer import unit_of_work
from domain import model
from tests.helpers import random_sku, random_orderid


def insert_batch(session, ref, sku, qty, eta):
    session.execute(
        "INSERT INTO products (sku) VALUES (:sku)",
        dict(sku=sku),
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
        "SELECT b.reference FROM allocations JOIN batches AS b ON batch_id = b.id "
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
