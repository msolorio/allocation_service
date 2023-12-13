from dataclasses import dataclass
from typing import NewType
from datetime import date
from typing import Optional, List


Quantity = NewType("Quantity", int)
Sku = NewType("Sku", str)
Reference = NewType("Reference", str)


@dataclass(frozen=True)
class OrderLine:
    orderid: Reference
    sku: Sku
    qty: Quantity


class Batch:
    def __init__(
        self, ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date] = None
    ):
        self.ref = ref
        self.sku = sku
        self.__purchased_quantity = qty
        self.eta = eta
        self.__allocated_lines = set()  # type: Set[OrderLine]

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False

        return other.ref == self.ref

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def can_allocate(self, line: OrderLine) -> bool:
        return (
            self.sku == line.sku
            and not line in self.__allocated_lines
            and self.available_quantity >= line.qty
        )

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self.__allocated_lines.add(line)

    def deallocate(self, line: OrderLine):
        if line in self.__allocated_lines:
            self.__allocated_lines.remove(line)

    @property
    def available_quantity(self) -> int:
        return self.__purchased_quantity - self.__allocated_quantity

    @property
    def __allocated_quantity(self) -> int:
        return sum(line.qty for line in self.__allocated_lines)


def allocate(line: OrderLine, batches: List[Batch]):
    batch = next(b for b in sorted(batches) if b.can_allocate(line))

    batch.allocate(line)
