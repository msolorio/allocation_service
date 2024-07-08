from datetime import date
from typing import Optional
from app.domain import model
from app.adapters import unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
):
    line = model.OrderLine(orderid=orderid, sku=sku, qty=qty)
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f"Invalid sku: {sku}")
        batch_ref = product.allocate(line)
        uow.commit()
    return batch_ref


def deallocate(
    orderid: str,
    sku: str,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=sku)
        if product is not None:
            product.deallocate(orderid, sku)
            uow.commit()


def add_batch(
    batchref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)
        product.add_batch(model.Batch(batch_ref=batchref, sku=sku, qty=qty, eta=eta))
        uow.commit()
