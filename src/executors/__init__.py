from __future__ import annotations

from .DocumentCrop import DocumentCrop
from .ScanEffect import ScanEffect

# Executor registry: maps each executor's `name` (the value sent as
# executor.value.name in a request) to its implementation class. Lets the
# Image's service.py register the whole package in one line:
#
#     from components.DocScanner.src.executors import EXECUTORS
#     executors = {"DocScanner": EXECUTORS}
EXECUTORS = {
    "DocumentCrop": DocumentCrop,
    "ScanEffect": ScanEffect,
}


def get_executor(name: str):
    return EXECUTORS[name]


def bootstrap_all() -> dict[str, dict[str, str]]:
    return {name: executor.bootstrap() for name, executor in EXECUTORS.items()}
