from app.domain import model
from app.adapters import repository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: model.OrderLine, repo: repository.AbstractRepository, session):
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku: {line.sku}")
    batch_ref = model.allocate(line, batches)
    session.commit()
    return batch_ref


def deallocate(orderid: str, sku: str, repo: repository.AbstractRepository, session):
    batches = repo.list()
    model.deallocate(orderid, sku, batches)
    session.commit()
