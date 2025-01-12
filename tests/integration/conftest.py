import os

import pytest


@pytest.fixture(autouse=True)
def skip_by_platform(request):
    test_integrations = os.getenv("TEST_INTEGRATIONS", "true").lower() == "true"
    if (
        request.node.get_closest_marker("skip_integration_test_if_not_enabled")
        and not test_integrations
    ):
        pytest.skip(
            "Integration tests are disabled to avoid side-effects and longer runtimes"
        )


def pytest_configure(config):
    config.addinivalue_line("markers", "skip_integration_test_if_not_enabled")
