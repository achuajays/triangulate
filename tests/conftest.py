"""Shared pytest configuration: adds --update-golden for golden-file tests."""

def pytest_addoption(parser):
    parser.addoption(
        "--update-golden", action="store_true", default=False,
        help="Regenerate golden files instead of comparing against them.",
    )
