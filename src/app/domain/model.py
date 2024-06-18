from datetime import date
from typing import Optional, NewType
from dataclasses import dataclass

Quantity = NewType("Quantity", int)
BatchRef = NewType("BatchRef", str)
OrderId = NewType("OrderId", str)
Sku = NewType("Sku", str)


class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: OrderId
    sku: Sku
    qty: Quantity


class Batch:
    def __init__(
        self,
        batch_ref: BatchRef,
        sku: Sku,
        qty: Quantity,
        eta: Optional[date] = None,
    ):
        self.batch_ref = batch_ref
        self.sku = sku
        self.initial_quantity = qty
        self.eta = eta
        self._allocations = set()

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    @property
    def allocated_quantity(self) -> Quantity:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> Quantity:
        return self.initial_quantity - self.allocated_quantity

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.batch_ref == self.batch_ref

    def __hash__(self):
        return hash(self.batch_ref)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        if not isinstance(other, Batch):
            raise TypeError("Cannot compare Batch with non-Batch type")
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta


def allocate(line: OrderLine, batches: list[Batch]) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.batch_ref
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku: {line.sku}")
