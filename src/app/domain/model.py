class Batch:
    def __init__(self, batch_ref, sku, qty):
        self.batch_ref = batch_ref
        self.sku = sku
        self.available_quantity = qty

    def allocate(self, line):
        if self.available_quantity >= line.qty:
            self.available_quantity -= line.qty


class OrderLine:
    def __init__(self, orderid, sku, qty):
        self.orderid = orderid
        self.sku = sku
        self.qty = qty
