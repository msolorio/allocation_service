from typing import Optional
from datetime import date

import domain.model as model
import adapters.repository as repository


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


class InvalidSku(Exception):
    pass


def allocate(
    orderid: str, sku: str, qty: int, repo: repository.AbstractRepository, session
) -> str:
    line = model.OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku: {line.sku}")
    batchref = model.allocate(line, batches)
    session.commit()

    return batchref


def add_batch(
    batchref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    repo: repository.AbstractRepository,
    session,
):
    repo.add(model.Batch(batchref, sku, qty, eta))
    session.commit()
