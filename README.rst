.. contents:: Table of Contents
   :local:

Introduction
============

The EOSC Data Transform Service is a service that supplies the EOSC Search Service portal with data from various sources. The data is collected, transformed to meet our requirements, and then sent to external services such as Solr and Amazon S3 Cloud.

The data obtained from APIs includes ``services, data sources, providers, offers, bundles, trainings, interoperability guidelines``. These data are updated in real-time, but there is also a possibility of updating all records.

The data obtained from dumps includes ``publications, datasets, software, other research products, organizations, and projects``. Live updates are not available, only batch updates.

Documentation
=============
The service uses Sphinx for generating both local and public documentation. Follow the instructions below to access the documentation.

Public Documentation
---------------------
The public documentation for the EOSC Data Transform Service is available online at `Read the Docs <https://eosc-search-service.readthedocs.io/en/latest/index.html>`_.
This should be your first point of reference for detailed information about the service.

Local Sphinx Documentation
---------------------------
You can generate and view the Sphinx documentation locally by running the following command in the docs directory:

.. code-block:: shell

   make html

Once generated, the documentation will be available at `docs/build/html/index.html`. Open it in a browser to navigate the API, Schemas and other documentation.

To remove old build files and ensure a fresh documentation generation, use the following command before running `make html`:

.. code-block:: shell

   make clean

This will delete the `docs/build/` directory, allowing Sphinx to regenerate all files from scratch.

API
===

Transform Endpoints
-------------------

- ``/batch`` - handles a live update. One or more resources per request.
- ``/full`` - handles an update of the whole data collection.
- ``/dump`` - handles a dump update to create a single data iteration.

Solr Manipulation Endpoints
---------------------------

- ``/create_collections`` - creates all necessary Solr collections for a single data iteration.
- ``/create_aliases`` - creates aliases for all collections from a single data iteration.
- ``/delete_collections`` - deletes all collections from a single data iteration.

Deployment
==========

1. Get Solr instance and/or Amazon S3 bucket.
2. Adjust ``docker-compose.yml`` to your requirements.
3. Set ``.env`` variables.
4. Deployment is simple and easy. Type:

.. code-block:: shell

    docker-compose up -d --build
    docker-compose up

Dependencies
------------

- ``Solr`` instance (optional) **and/or** ``Amazon S3 cloud`` (optional). At least one of them is necessary.

ENV variables
-------------

We are using ``.env`` (in the root of the EOSC Transform Service) to store user-specific constants. Details:

General
^^^^^^^
- ``ENVIRONMENT``: ``Literal["dev", "test", "production"] = "dev"`` - Choose environment in which you want to work in.
- ``LOG_LEVEL``: ``str = "info"`` - Logging level.
- ``SENTRY_DSN`` - endpoint for Sentry logged errors. For development leave this variable unset.

Services
^^^^^^^^
Solr
----
- ``SOLR_URL``: ``AnyUrl = "http://localhost:8983/solr/"`` - Solr address.
- ``SOLR_COLS_PREFIX``: ``str = ""`` - The prefix of the Solr collections to which data will be sent.

S3
--
- ``S3_ACCESS_KEY``: ``str = ""`` - Your S3 access key with write permissions.
- ``S3_SECRET_KEY``: ``str = ""`` - Your S3 secret key with write permissions.
- ``S3_ENDPOINT``: ``str = ""`` - S3 endpoint. Example: ``https://s3.cloud.com``.
- ``S3_BUCKET``: ``str = ""`` - S3 bucket. Example: ``ess-mock-dumps``.

AMS
-----
- ``AMS_SUBSCRIPTION``: ``bool = True`` - Subscribe to JMS?
    - ``AMS_API_BASE_URL``: ``str = "https://api-new.msg.argo.grnet.gr/v1"`` - The address of AMS API.
    - ``AMS_API_TOKEN``: ``str = "CHANGE_ME"`` - The token used for authorization.
    - ``AMS_PROJECT_NAME``: ``str = "eosc-beyond-providers"``- The project name.

STOMP (JMS)
-----
- ``STOMP_SUBSCRIPTION``: ``bool = False`` - Subscribe to JMS?
    - ``STOMP_HOST``: ``str = "127.0.0.1"`` - The hostname or IP address of the STOMP broker.
    - ``STOMP_PORT``: ``int = 61613``- The port on which the STOMP broker is listening.
    - ``STOMP_LOGIN``: ``str = "guest"`` - The username for connecting to the STOMP broker.
    - ``STOMP_PASS``: ``str = "guest"``- The password for connecting to the STOMP broker.
    - ``STOMP_CLIENT_NAME``: ``str = "transformer-client"`` - A name to identify this STOMP client instance.
    - ``STOMP_SSL``: ``bool = False`` - Set to ``True`` to enable SSL for the STOMP connection. Ensure SSL certificates are properly configured if this is enabled.
    - ``STOMP_TOPIC_PREFIX``: ``str = ""`` - Prefix that is added to STOMP base topics. E.g. "adapter.update" -> "beta.adapter.update".

Sources of Data
^^^^^^^^^^^^^^^
Local Data Dump
---------------

- ``DATASET_PATH``: ``str`` - A path to datasets **directory**.
- ``PUBLICATION_PATH``: ``str`` - A path to publications **directory**.
- ``SOFTWARE_PATH``: ``str`` - A path to software **directory**.
- ``OTHER_RP_PATH``: ``str`` - A path to other research products **directory**.
- ``ORGANISATION_PATH``: ``str`` - A path to organisation **directory**.
- ``PROJECT_PATH``: ``str`` - A path to project **directory**.

Relations
---------

- ``RES_ORG_REL_PATH``: ``str`` - A path to resultOrganization **directory**.
- ``RES_PROJ_REL_PATH``: ``str`` - A path to resultProject **directory**.
- ``ORG_PROJ_REL_PATH``: ``str`` - A path to organizationProject **directory**.

Data from API
-------------
Marketplace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- ``MP_API_ADDRESS``: ``AnyUrl = "https://userspace.sandbox.eosc-beyond.eu"`` - A Marketplace API address.
- ``MP_API_TOKEN``: ``str`` - An authorization token for the Marketplace API.

Provider Component
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- ``GUIDELINE_ADDRESS``: ``AnyUrl = "https://integration.providers.sandbox.eosc-beyond.eu/api/public/interoperabilityRecord/all?catalogue_id=all&active=true&suspended=false&quantity=10000"`` - A full address to get all interoperability guidelines **endpoint**.
- ``TRAINING_ADDRESS``: ``AnyUrl = "https://integration.providers.sandbox.eosc-beyond.eu/api/public/trainingResource/all?catalogue_id=all&active=true&suspended=false&quantity=10000"`` - A full address to get all trainings **endpoint**.
- ``ADAPTER_ADDRESS``: ``AnyUrl = "https://integration.providers.sandbox.eosc-beyond.eu/api/public/adapter/all?active=true&suspended=false&quantity=10000"`` - A full address to get all adapters **endpoint**.
- ``NODE_ADDRESS``: ``AnyUrl = "https://integration.providers.sandbox.eosc-beyond.eu/api/vocabulary/byType/NODE"`` - Get all nodes for OAG mapping.
Authentication (Optional)
"""""""""""""""""""""""""""""""""""""""""""
If the target endpoint requires authentication, the following settings can be used to enable token-based access:

- ``PC_AUTH``: ``bool = False``
  Enables or disables authentication. Set to `True` to retrieve a bearer token before calling the API.

- ``PC_REFRESH_TOKEN``: ``str = ""``
  A valid **refresh token** used to obtain an access token.

- ``PC_TOKEN_URL``: ``str = "https://core-proxy.sandbox.eosc-beyond.eu/auth/realms/core/protocol/openid-connect/token"``
  The URL to fetch the access token using the refresh token (following the OpenID Connect token flow).

- ``PC_CLIENT_ID``: ``str = "providers-api-token-client"``
  The client ID registered in the authentication server used to identify the requesting application.

If authentication is enabled (`PC_AUTH = True`), the application will request a bearer token using the provided credentials and attach it to the request header as:

.. code-block:: python

    headers["Authorization"] = f"Bearer {access_token}"

If the token request fails, a `requests.HTTPError` is raised.

Transformation General Settings
-------------
- ``INPUT_FORMAT``: ``str = "json"`` - Format of the input data files.
- ``OUTPUT_FORMAT``: ``str = "json"`` - Format of the output data files.

Running Service
===============

How to use the service? Upon successful launch of the service, the following components will be initiated:

- ``EOSC Transform Service``: by default, at http://0.0.0.0:8080 and http://0.0.0.0:8080/docs to access Swagger. It can be used to trigger actions.
- ``Flower Dashboard``: by default, at http://0.0.0.0:5555 to view current and past actions and monitor them.
