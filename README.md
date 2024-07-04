# Posts API -- Backend

This repo is an extremely simple backend for a posts service (a la Tumblr). It uses FastAPI as the API definition library, PostgreSQL as the database, and uvicorn as the ASGI server.

## Running and Accessing the Backend

The simplest way to get started is to run as a Docker service with Docker Compose. This will work on Linux or macOS and doesn't require installing any dependencies on your local machine except Docker.

There is a `Makefile` included in the repository with commands to build and run the image:

* `make build-image`: Build the app image, tagging it as `backend_posts_api:latest`
* `make up`: Run the app after you've built the image. The API is hosted on port 8000.

You can run them like this in a terminal:

```shell
make build-image
make up
```

Once the services are started, you can go to <http://localhost:8000> in your web browser to see the main page, a rendered copy of this document.

FastAPI includes an OpenAPI/Swagger page for API documentation at `/docs`, so you can go to <http://localhost:8000/docs> to interact with the API from a web browser. Alternatively, you can use `cURL` from the CLI.

## Endpoints

There are several endpoints to interact with the applications users and posts. They are all documented on the <http://localhost:8000/docs> page. All the events return a 200-series (200 or 204) code for successful requests and 404 when relevant resources cannot be found. If invalid input is provided, the API will return a 422 status code and the response will include information about the malformed input.

## Local/Dev Setup

Local or dev setup requires Python to be installed. The repository is configured to use [`mise-en-place`](https://mise.jdx.dev/) for easy setup. If you have `mise` installed, running `mise install` will install the required tool versions. If you don't have `mise`, install Python 3.12 and [`pdm`](https://pdm-project.org/en/latest/) by whatever means works best for you.

Once you have `pdm` and Python, running `pdm install` will create a virtual environment in this folder and install the dependencies, and the project. The project will be installed in "editable" mode, so any changes you make to the code locally will automatically be included in the virtual environment.

### Running Tests

The test suite uses `pytest`. Run `pdm test` or `pdm run pytest --cov=backend_posts_api tests/` to run the entire suite.

#### Note about the tests

I wrote a very small test suite. Most of the testing I conducted was using the `/docs` HTML page to verify things worked and that some edge cases were caught. Given more time, I would create a much more extensive test suite that covered many of the edge cases that I caught with ad-hoc testing. In other words, the test suite doesn't represent my typical professional output; I decided to prioritize the functionality and deployment of the app rather than tests.

### Linting and Formatting

Ruff is configured as the linter and formatter. Run `pdm lint` or `pdm format`.
