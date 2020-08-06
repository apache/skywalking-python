# Plugin Test

Plugin test is required and should pass before a new plugin is able to be merged into the master branch.

## Mock Collector

Mock Collector respects the same protocol as the SkyWalking backend, and thus receives the report data from the agent side,
besides, it also exposes some http endpoints for verification.

## Tested Service

A tested service is a service involving the plugin that is to be tested, and exposes some endpoints to trigger the instrumentation
and report data to the mock collector.

## Docker Compose

`docker-compose` is used to orchestrate the mock collector and the tested service(s), the `docker-compose.yml` should be
able to run with `docker-compose -f docker-compose.yml up` in standalone mode, which can be used in debugging too.

## Expected Data

The `expected.data.yml` file contains the expected segment data after we have triggered the instrumentation and report to mock collector,
since the mock collector received the segment data then, we can post the expected data to the mock collector and verify whether
they match. This can be done through the `/dataValidate` of the mock collector, say `http://collector:12800/dataValidate`, for example.

## Example

If we want to test the plugin for the built-in library `http`, we will:

1. Build a tested service, which sets up an http server by `http` library, and exposes an http endpoint to be triggered in the test codes, say `/trigger`, take [this provider service](../tests/plugin/sw_http/services/provider.py) as example.
1. Compose a `docker-compose.yml` file, orchestrating the service built in step 1 and the mock collector, take [this `docker-compose.yml`](../tests/plugin/sw_http/docker-compose.yml) as example.
1. Write test codes to trigger the endpoint int step 1, and send the expected data file to the mock collector to verify, take [this test](../tests/plugin/sw_http/test_http.py) as example.

## Notes

Remember to add the library/module into the [setup.py](../setup.py) `extras_require/test` so that other developers can have it installed
after pulling your commits, and run test locally.
