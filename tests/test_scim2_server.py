import threading
import wsgiref.simple_server

import portpicker
import pytest
from httpx import Client
from scim2_client import SCIMClient
from scim2_models import Group
from scim2_models import User
from scim2_server.backend import InMemoryBackend
from scim2_server.provider import SCIMProvider
from scim2_server.utils import load_default_resource_types
from scim2_server.utils import load_default_schemas

from scim2_tester import check_server
from scim2_tester.utils import Status


@pytest.fixture(scope="session")
def scim2_server():
    backend = InMemoryBackend()
    app = SCIMProvider(backend)
    for schema in load_default_schemas().values():
        app.register_schema(schema)
    for resource_type in load_default_resource_types().values():
        app.register_resource_type(resource_type)

    host = "localhost"
    port = portpicker.pick_unused_port()
    httpd = wsgiref.simple_server.make_server(host, port, app)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()
    try:
        yield host, port
    finally:
        httpd.shutdown()
        server_thread.join()


def test_scim2_server(scim2_server):
    host, port = scim2_server
    client = Client(base_url=f"http://{host}:{port}")
    scim = SCIMClient(client, resource_types=(User, Group))
    results = check_server(scim)
    assert all(result.status == Status.SUCCESS for result in results)
