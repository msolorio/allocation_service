import pytest
import requests

import config

@pytest.mark.usefixtures("restart_api")
def test_allocate_returns_201_status():
    url = config.get_api_url()
    
    r = requests.post(f"{url}/allocate")
    
    assert r.status_code == 201