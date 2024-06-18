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
            (batch1, sku1, 100, "2000-01-01"),
            (batch2, sku1, 100, "2000-01-02"),
            (batch3, sku2, 100, "2000-01-03"),
        ]
    )
    data = {"orderid": orderid, "sku": sku1, "qty": 10}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == batch1


@pytest.mark.usefixtures("restart_api")
def test_allocate_endpoint_persists_allocation(add_stock):
    sku1 = random_sku()
    batch1, batch2 = random_batchref(), random_batchref()
    orderid1, orderid2 = random_orderid(), random_orderid()
    add_stock(
        [
            (batch1, sku1, 10, "2000-01-01"),
            (batch2, sku1, 10, "2000-01-02"),
        ]
    )
    orderline1 = {"orderid": orderid1, "sku": sku1, "qty": 10}
    orderline2 = {"orderid": orderid2, "sku": sku1, "qty": 10}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=orderline1)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch1

    r = requests.post(f"{url}/allocate", json=orderline2)
    assert r.status_code == 201
    assert r.json()["batchref"] == batch2


@pytest.mark.usefixtures("restart_api")
def test_400_message_for_out_of_stock(add_stock):
    sku, small_batch, large_order = random_sku(), random_batchref(), random_orderid()
    add_stock([(small_batch, sku, 10, "2000-01-01")])
    data = {"orderid": large_order, "sku": sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Out of stock for sku {sku}"


@pytest.mark.usefixtures("restart_api")
def test_400_message_for_invalid_sku():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"
