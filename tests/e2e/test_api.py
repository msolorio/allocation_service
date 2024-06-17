import requests
import pytest

from app import config

from tests.helpers import random_sku, random_batchref, random_orderid


def test_app_running():
    url = config.get_api_url()

    r = requests.get(f"{url}/health")

    assert r.status_code == 200
    assert r.text == "OK"


@pytest.mark.usefixtures("restart_api")
def test_allocate_returns_201_and_allocated_batchref(add_stock):
    sku1, sku2 = random_sku(), random_sku()
    batch1, batch2, batch3 = random_batchref(), random_batchref(), random_batchref()
    orderid = random_orderid()
    add_stock(
        [
            (batch1, sku1, 100, None),
            (batch2, sku1, 100, None),
            (batch3, sku2, 100, None),
        ]
    )
    data = {"orderid": orderid, "sku": sku1, "qty": 10}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == batch1
