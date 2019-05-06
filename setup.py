"""Setup the chainball scoreboard."""

from setuptools import setup, find_packages

setup(
    name="Chainball Scoreboard",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "cheroot>=6.5.5",
        "pygame>=1.9.6",
        "pyserial>=3.4",
        "dbus-python>=1.2.8",
    ],
    package_data={"views": ["*.tpl"], "data": ["*"]},
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="The chainball scoreboard",
    scripts=["board"],
)
