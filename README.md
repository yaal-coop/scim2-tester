# scim2-tester

Python methods based on [scim2-models](https://scim2-models.readthedocs.io) and [scim2-client](https://scim2-client.readthedocs.io/en), to check if SCIM servers respect the [RFC7643](https://datatracker.ietf.org/doc/html/rfc7643.html) and [RFC7644](https://datatracker.ietf.org/doc/html/rfc7644.html) specifications.

It aims to be used in unit test and Continuous Integration suites and in healthcheck tools.
If you are seeking a CLI integration of scim2-tester, take a look at [scim2-cli](https://scim2-cli.readthedocs.io).

## What's SCIM anyway?

SCIM stands for System for Cross-domain Identity Management, and it is a provisioning protocol.
Provisioning is the action of managing a set of resources across different services, usually users and groups.
SCIM is often used between Identity Providers and applications in completion of standards like OAuth2 and OpenID Connect.
It allows users and groups creations, modifications and deletions to be synchronized between applications.

## Installation

```shell
pip install scim2-tester
```

## Usage

scim2-tester provides a very basic command line:

```console
python scim2_tester/checker.py https://scim.example
```

However, a more complete integration is achieved through [scim2-cli](https://scim2-cli.readthedocs.io):

```console
pip install scim2-cli
scim https://scim.example test
```

You can check the [scim2-cli test command reference](https://scim2-cli.readthedocs.io/en/latest/reference.html#scim-url-test) for more details.

scim2-tester belongs in a collection of SCIM tools developed by [Yaal Coop](https://yaal.coop),
with [scim2-models](https://github.com/python-scim/scim2-models),
[scim2-client](https://github.com/python-scim/scim2-client) and
[scim2-cli](https://github.com/python-scim/scim2-cli)
