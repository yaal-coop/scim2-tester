from httpx import Client
from scim2_client import SCIMClient
from scim2_models import Group
from scim2_models import User

from scim2_tester.checker import check_server


def test_unreachable_host():
    """Test reaching a invalid URL."""

    client = Client(base_url="https://invalid.test")
    scim = SCIMClient(client, resource_types=(User, Group))

    check_server(scim)
