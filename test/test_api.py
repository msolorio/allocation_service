import uuid
import pytest
import requests

import config


def random_suffix():
    return uuid.uuid4().hex[:6]


def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"


def random_batchref(name=""):
    return f"batch-{name}-{random_suffix()}"


def random_orderid(name=""):
    return f"order-{name}-{random_suffix()}"


@pytest.mark.usefixtures("restart_api")
def test_allocate_returns_201_status():
    url = config.get_api_url()

    r = requests.get(f"{url}/health")

    assert r.status_code == 201


@pytest.mark.usefixtures("restart_api")
def test_allocate_returns_201_and_allocated_batch(add_stock):
    sku, other_sku = random_sku(), random_sku("other")
    earliest_batchref = random_batchref("earliest")
    later_batchref = random_batchref("later")
    other_batchref = random_batchref("other")

    add_stock(
        [
            (earliest_batchref, sku, 100, "2000-01-01"),
            (later_batchref, sku, 100, "2000-01-02"),
            (other_batchref, other_sku, 100, "2000-01-01"),
        ]
    )

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earliest_batchref


@pytest.mark.usefixtures("restart_api")
def test_alloate_persists_allocations(add_stock):
    sku = random_sku()
    earliest_batchref = random_batchref("earliest")
    later_batchref = random_batchref("later")

    add_stock(
        [
            (earliest_batchref, sku, 10, "2000-01-01"),
            (later_batchref, sku, 10, "2000-01-02"),
        ]
    )

    line_1 = {"orderid": random_orderid("line_1"), "sku": sku, "qty": 10}
    line_2 = {"orderid": random_orderid("line_2"), "sku": sku, "qty": 10}

    url = config.get_api_url()

    request_1 = requests.post(f"{url}/allocate", json=line_1)

    assert request_1.status_code == 201
    assert request_1.json()["batchref"] == earliest_batchref

    request_2 = requests.post(f"{url}/allocate", json=line_2)

    assert request_2.status_code == 201
    assert request_2.json()["batchref"] == later_batchref


@pytest.mark.usefixtures("restart_api")
def test_400_message_out_of_stock(add_stock):
    sku = random_sku()
    batchref = random_batchref()

    add_stock([(batchref, sku, 10, "2000-01-01")])

    line = {"orderid": random_orderid(), "sku": sku, "qty": 20}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == f"Out of stock for sku: {sku}"


@pytest.mark.usefixtures("restart_api")
def test_400_message_invalid_sku():
    unknown_sku = random_sku()
    line = {"orderid": random_orderid(), "sku": unknown_sku, "qty": 20}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku: {unknown_sku}"
