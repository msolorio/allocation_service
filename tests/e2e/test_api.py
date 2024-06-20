import requests
import pytest
from datetime import date, timedelta

from app import config

from tests.helpers import random_sku, random_batchref, random_orderid

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


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
            (batch1, sku1, 100, today),
            (batch2, sku1, 100, tomorrow),
            (batch3, sku2, 100, later),
        ]
    )
    data = {"orderid": orderid, "sku": sku1, "qty": 10}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocation", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == batch1


@pytest.mark.usefixtures("restart_api")
def test_allocate_unhappy_path_returns_400_and_error(add_stock):
    sku, small_batch, large_order = random_sku(), random_batchref(), random_orderid()
    add_stock([(small_batch, sku, 10, today)])
    data = {"orderid": large_order, "sku": sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocation", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Out of stock for sku: {sku}"


@pytest.mark.usefixtures("restart_api")
def test_deallocate(add_stock):
    sku = random_sku()
    batchref = random_batchref()
    orderid1, orderid2 = random_orderid(), random_orderid()
    url = config.get_api_url()
    add_stock([(batchref, sku, 100, today)])
    orderline1 = {"orderid": orderid1, "sku": sku, "qty": 100}

    r1 = requests.post(f"{url}/allocation", json=orderline1)
    assert r1.status_code == 201
    assert r1.json()["batchref"] == batchref

    orderline2 = {"orderid": orderid2, "sku": sku, "qty": 100}
    r2 = requests.post(f"{url}/allocation", json=orderline2)
    assert r2.status_code == 400
    assert r2.json()["message"] == f"Out of stock for sku: {sku}"

    r3 = requests.delete(f"{url}/allocation", json={"orderid": orderid1, "sku": sku})
    assert r3.status_code == 204

    r4 = requests.post(f"{url}/allocation", json=orderline2)
    assert r4.status_code == 201
    assert r4.json()["batchref"] == batchref
