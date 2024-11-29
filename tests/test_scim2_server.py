import pytest
from scim2_client.engines.werkzeug import TestSCIMClient
from scim2_models import EnterpriseUser
from scim2_models import Group
from scim2_models import User
from scim2_server.backend import InMemoryBackend
from scim2_server.provider import SCIMProvider
from scim2_server.utils import load_default_resource_types
from scim2_server.utils import load_default_schemas

from scim2_tester import check_server

TestSCIMClient.__test__ = False


@pytest.fixture
def scim2_server():
    backend = InMemoryBackend()
    app = SCIMProvider(backend)

    for schema in load_default_schemas().values():
        app.register_schema(schema)

    for resource_type in load_default_resource_types().values():
        app.register_resource_type(resource_type)

    return app


def test_scim2_server(scim2_server):
    scim = TestSCIMClient(scim2_server, resource_models=(User[EnterpriseUser], Group))
    check_server(scim, raise_exceptions=True)
