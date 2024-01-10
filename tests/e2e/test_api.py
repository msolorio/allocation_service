import pytest
import requests

import config
from tests.helpers import random_sku, random_batchref, random_orderid


def add_batch(ref, sku, qty, eta):
    url = config.get_api_url()

    r = requests.post(
        f"{url}/add_batch", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
    )

    assert r.status_code == 201


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_allocate_returns_201_and_allocated_batch():
    sku, other_sku = random_sku(), random_sku("other")
    earliest_batchref = random_batchref("earliest")
    later_batchref = random_batchref("later")
    other_batchref = random_batchref("other")

    add_batch(earliest_batchref, sku, 100, "2000-01-01")
    add_batch(later_batchref, sku, 100, "2000-01-02")
    add_batch(other_batchref, other_sku, 100, "2000-01-01")

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earliest_batchref


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_400_message_invalid_sku():
    unknown_sku = random_sku()
    line = {"orderid": random_orderid(), "sku": unknown_sku, "qty": 20}

    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=line)

    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku: {unknown_sku}"
