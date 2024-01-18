from typing import Optional
from datetime import date

from domain import model
from service_layer import unit_of_work


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


class InvalidSku(Exception):
    pass


def allocate(
    orderid: str,
    sku: str,
    qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
):
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            raise InvalidSku(f"Invalid sku: {line.sku}")
        batchref = product.allocate(line)
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
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku=sku, batches=[])
            uow.products.add(product)
        product.batches.append(model.Batch(batchref, sku, qty, eta))
        uow.commit()
