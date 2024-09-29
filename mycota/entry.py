import logging
import sys
from pathlib import Path

import pandas as pd

from .api import fetch_all


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    cache_path = Path('.cache.pickle.xz')
    if cache_path.exists():
        df = pd.read_pickle(cache_path)
    else:
        df = pd.DataFrame.from_records(
            data=fetch_all(template='Mycomorphbox'), index='pageid',
        )
        df.to_pickle(cache_path)
    print(df)
