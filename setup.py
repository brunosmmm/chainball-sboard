"""Setup the chainball scoreboard."""

from setuptools import setup, find_packages

setup(
    name="Chainball Scoreboard",
    version="1.0",
    packages=find_packages(),
    install_requires=["pyserial>=3.4", "dbus-python>=1.2.8"],
    package_data={"data": ["sfx/*"]},
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="The chainball scoreboard",
    scripts=["board"],
)
