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
