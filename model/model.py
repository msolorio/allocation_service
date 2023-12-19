from dataclasses import dataclass
from typing import NewType
from datetime import date
from typing import Optional, List


Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)


class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: Reference
    sku: Sku
    qty: Quantity


class Batch:
    def __init__(
        self, reference: Reference, sku: Sku, qty: Quantity, eta: Optional[date] = None
    ):
        self.reference = reference
        self.sku = sku
        self._purchased_quantity = qty
        self.eta = eta
        self._allocations = set()  # type: Set[OrderLine]

    def __repr__(self):
        return f"<Batch {self.reference}>"

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False

        return other.reference == self.reference

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def can_allocate(self, line: OrderLine) -> bool:
        return (
            self.sku == line.sku
            and not line in self._allocations
            and self.available_quantity >= line.qty
        )

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.__allocated_quantity

    @property
    def __allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)


def allocate(line: OrderLine, batches: List[Batch]) -> Reference:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku: {line.sku}")
