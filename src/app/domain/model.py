from datetime import date
from typing import Optional, NewType
from dataclasses import dataclass

Quantity = NewType("Quantity", int)
BatchRef = NewType("BatchRef", str)
OrderId = NewType("OrderId", str)
Sku = NewType("Sku", str)


@dataclass(frozen=True)
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
