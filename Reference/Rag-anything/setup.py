"""Compatibility shim for tools that still invoke ``setup.py`` directly.

All package metadata and dependencies live in ``pyproject.toml``. Keeping this
file metadata-free prevents the build from reading UTF-8 project files with the
Windows process default encoding.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
