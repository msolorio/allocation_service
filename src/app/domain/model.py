from datetime import date
from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(
        self,
        batch_ref: str,
        sku: str,
        qty: int,
        eta: Optional[date] = None,
    ):
        self.batch_ref = batch_ref
        self.sku = sku
        self.initial_quantity = qty
        self._allocations = set()

    def allocate(self, line):
        if self.can_allocate(line) and line not in self._allocations:
            self._allocations.add(line)

    def deallocate(self, line):
        if line in self._allocations:
            self._allocations.remove(line)

    def can_allocate(self, line):
        return self.sku == line.sku and self.available_quantity >= line.qty

    @property
    def allocated_quantity(self):
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self):
        return self.initial_quantity - self.allocated_quantity
