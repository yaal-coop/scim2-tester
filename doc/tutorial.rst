Tutorial
--------

Basic CLI
=========

scim2-tester provides a very basic command line:

.. code-block:: console

    python scim2_tester/checker.py https://scim.example

However, we encourage you to use the more complete integration in :doc:`scim2-cli <scim2_cli:index>`:

.. code-block:: console

    pip install scim2-cli
    scim https://scim.example test

You can check the :ref:`scim2-cli test command reference <scim2_cli:test>` for more details.

Unit test suite integration
===========================

If you build a Python SCIM sever application and need a complete test suite to check you implementation, you can integrate `scim2-tester` in your test suite with little effort.
Thanks to scim2-client :class:`~scim2_client.engines.werkzeug.TestSCIMClient` engine, no real HTTP request is made, but the server code is directly executed.
In combination with :paramref:`~scim2_tester.check_server.raise_exceptions`, this allows you to catch server exceptions in the test contexts, which is very handy for development.

As :class:`~scim2_client.engines.werkzeug.TestSCIMClient` relies on :doc:`Werkzeug <werkzeug:index>`, you need to check that you have installed the right dependencies to use it:

.. code-block:: console

   uv add --group dev scim2-models[werkzeug]

.. code-block:: python

    from scim2_models import User, Group
    from scim2_client.engines.werkzeug import TestSCIMClient
    from scim2_tester import check_server, Status
    from werkzeug.test import Client
    from myapp import create_app

    def test_scim_tester():
        app = create_app(...)
        client = TestSCIMClient(app=Clien(app), scim_prefix="/scim/v2")
        check_server(client, raise_exceptions=True)
