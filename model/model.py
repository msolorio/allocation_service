class Batch:
    def __init__(self, ref=None, sku=None, qty=0):
        self.ref = ref
        self.sku = sku
        self.available_quantity = qty

    def allocate(self, line):
        if self.available_quantity >= line.quantity:
            self.available_quantity -= line.quantity


class OrderLine:
    def __init__(self, sku=None, qty=0):
        self.sku = sku
        self.quantity = qty
