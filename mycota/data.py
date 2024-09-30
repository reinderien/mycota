import logging
import sqlite3
import typing
from pathlib import Path

import pandas as pd

from .api import fetch_all


logger = logging.getLogger('data')


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype(pd.StringDtype())  # Use new dtype

    # Strip leading and trailing apostrophes from name
    df['name'] = df['name'].str.replace(
        pat=r"^'*(.*?)'*$",
        repl=r'\1',
        regex=True,
    )

    # Replace NaN-likes with NaN
    as_lower = df.apply(lambda s: s.str.lower(), axis=1)
    df[(as_lower == 'no') | (as_lower == 'na') | (as_lower == 'none')] = None

    # Replace empty strings with NaN
    lengths = df.apply(lambda s: s.str.len(), axis=1)
    df[lengths == 0] = None

    # Drop all-NaN columns
    df = df.loc[:, ~df.isna().all()]

    return df


def get_frame() -> pd.DataFrame:
    logger.info('Downloading from Wikipedia')
    df = pd.DataFrame.from_records(
        data=fetch_all(template='Mycomorphbox'), index='pageid',
    )
    return clean(df)


def connect_or_download(cache_path: Path = Path('.cache.sqlite')) -> sqlite3.Connection:
    if cache_path.exists():
        logger.info('Connecting to cached SQLite database')
    else:
        df = get_frame()
        logger.info('Creating SQLite database')
        with sqlite3.connect(cache_path) as conn:
            df.to_sql(name='mycota', con=conn)
    return sqlite3.connect(f'file:{cache_path}?mode=ro', uri=True)


def dump_schema(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "select sql from sqlite_master where type='table' and name='mycota';"
    )
    try:
        res, = cur.fetchone()
        return res
    finally:
        cur.close()


def run_queries(conn: sqlite3.Connection, queries: typing.Iterable[str]) -> None:
    pd.options.display.max_columns = 0
    pd.options.display.max_rows = None
    for query in queries:
        print(pd.read_sql_query(sql=query, con=conn))
