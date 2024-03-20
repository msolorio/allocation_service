class Batch:
    def __init__(self, batch_ref, sku, qty):
        self.batch_ref = batch_ref
        self.sku = sku
        self.initial_quantity = qty
        self._allocations = set()

    def allocate(self, line):
        if self.can_allocate(line) and line not in self._allocations:
            self._allocations.add(line)

    def can_allocate(self, line):
        return self.available_quantity >= line.qty

    @property
    def allocated_quantity(self):
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self):
        return self.initial_quantity - self.allocated_quantity


class OrderLine:
    def __init__(self, orderid, sku, qty):
        self.orderid = orderid
        self.sku = sku
        self.qty = qty
