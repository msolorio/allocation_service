from typing import Optional
from datetime import date

import domain.model as model
import adapters.repository as repository
import service_layer.unit_of_work as unit_of_work


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


class InvalidSku(Exception):
    pass


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku: {line.sku}")
        batchref = model.allocate(line, batches)
        uow.commit()

    return batchref


def add_batch(
    batchref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        uow.batches.add(model.Batch(batchref, sku, qty, eta))
        uow.commit()
