from dataclasses import dataclass


@dataclass(frozen=True)
class OrderLine:
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int):
        self.ref = ref
        self.sku = sku
        self.available_quantity = qty
        self.allocated_lines = set()

    def can_allocate(self, line: OrderLine) -> bool:
        return (
            self.sku == line.sku
            and not line in self.allocated_lines
            and self.available_quantity >= line.qty
        )

    def allocate(self, line: OrderLine) -> None:
        if self.can_allocate(line):
            self.available_quantity -= line.qty
            self.allocated_lines.add(line)
