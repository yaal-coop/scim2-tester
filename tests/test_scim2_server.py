import pytest
from scim2_client.engines.werkzeug import TestSCIMClient
from scim2_server.backend import InMemoryBackend
from scim2_server.provider import SCIMProvider
from scim2_server.utils import load_default_resource_types
from scim2_server.utils import load_default_schemas
from werkzeug.test import Client

from scim2_tester import check_server


@pytest.fixture
def scim2_server():
    backend = InMemoryBackend()
    app = SCIMProvider(backend)

    for schema in load_default_schemas().values():
        app.register_schema(schema)

    for resource_type in load_default_resource_types().values():
        app.register_resource_type(resource_type)

    return app


def test_discovered_scim2_server(scim2_server):
    client = TestSCIMClient(Client(scim2_server))
    client.discover()
    check_server(client, raise_exceptions=True)


def test_undiscovered_scim2_server(scim2_server):
    client = TestSCIMClient(Client(scim2_server))
    check_server(client, raise_exceptions=True)
