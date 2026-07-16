"""
    Offline smoke test: confirms every registered executor bootstraps.

        python -m components.DocScanner.src.executors
"""
from __future__ import annotations

from components.DocScanner.src.executors import bootstrap_all


if __name__ == "__main__":
    for executor_name, bootstrap_data in bootstrap_all().items():
        print(f"{executor_name}: {bootstrap_data['status']}")
