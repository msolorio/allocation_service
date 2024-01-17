from datetime import date, timedelta
from domain.model import Batch, OrderLine, Product, OutOfStock

today = date.today()
tomorrow = today + timedelta(days=1)
later = today + timedelta(days=2)


def prefers_in_stock_batches_to_shipment_batches():
    in_stock_batch = Batch("b1", "LAMP", 100, None)
    shipment_batch = Batch("b1", "LAMP", 100, today)
    product = Product(sku="LAMP", batches=[in_stock_batch, shipment_batch])
    line = OrderLine("o1", "LAMP", 10)

    product.allocate(line)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100
