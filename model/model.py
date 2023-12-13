from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int):
        self.ref = ref
        self.sku = sku
        self.initial_quantity = qty
        self.allocated_lines = set()

    @property
    def allocated_quantity(self) -> int:
        return sum([line.qty for line in self.allocated_lines])

    @property
    def available_quantity(self) -> int:
        return self.initial_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        return (
            self.sku == line.sku
            and not line in self.allocated_lines
            and self.available_quantity >= line.qty
        )

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self.allocated_lines.add(line)

    def deallocate(self, line: OrderLine):
        if line in self.allocated_lines:
            self.allocated_lines.remove(line)
