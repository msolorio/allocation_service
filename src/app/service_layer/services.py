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
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku: {line.sku}")
        batch_ref = model.allocate(line, batches)
        uow.commit()
    return batch_ref


def deallocate(
    orderid: str,
    sku: str,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        batches = uow.batches.list()
        model.deallocate(orderid, sku, batches)
        uow.commit()


def add_batch(
    batchref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        uow.batches.add(model.Batch(batch_ref=batchref, sku=sku, qty=qty, eta=eta))
        uow.commit()
