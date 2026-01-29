from os import environ

from setuptools import find_packages, setup

setup(
    name="pull-up",
    version=environ.get("GITVERSIONNUMBER", "0.0.0"),
    author="Robin Kupper",
    author_email="robin.kupper@diddiz.de",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    python_requires=">=3.13",
    install_requires=[
        "black",
        "dash",
        "dash-bootstrap-components",
        "dash-bootstrap-templates",
        "pandas",
        "plotly",
        "tabulate",
    ],
    extras_require={
        "dev": [
            "pre-commit",
            "pytest",
        ],
    },
)
