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
    df[  (as_lower == 'no')
       | (as_lower == 'na')
       | (as_lower == 'n/a')
       | (as_lower == 'none')
    ] = None

    # Replace empty strings with NaN
    lengths = df.apply(lambda s: s.str.len(), axis=1)
    df[lengths == 0] = None

    # Drop all-NaN columns
    df = df.loc[:, ~df.isna().all()]

    return df


def collate(df: pd.DataFrame) -> pd.DataFrame:
    by_column = df.sort_index(axis='columns')

    # pattern-match on numeric column index suffix
    pieces = by_column.columns.str.extract(r'''(?x)
        ^
        (?P<stem>.+?)  # lazy, allow for leading digits
        (?P<idx>\d*)  # may be an empty string for first or only cols
        $
    ''')
    pieces['oldname'] = by_column.columns

    # unique stems for which any corresponding col has an index suffix
    multi_stems = pieces.loc[pieces['idx'] != '', 'stem'].drop_duplicates()

    # all stems for which any stem in the group has a suffix
    multi_pieces = pd.merge(
        left=pieces.reset_index(), right=multi_stems, on='stem',
    )

    # renumber, because the first column name is missing a '1'
    multi_pieces['newname'] = multi_pieces['stem'] + (
        multi_pieces.groupby('stem').cumcount() + 1
    ).astype(pd.StringDtype())

    # renumber column index in the original dataframe
    by_column.rename(columns=pd.Series(
        index=multi_pieces['oldname'],
        data=multi_pieces['newname'].values,
    ).to_dict(), inplace=True)

    for stem, group in multi_pieces.groupby('stem'):
        by_column[stem] = (
            by_column[group['newname']]  # take columns in this group
            .stack()                  # flatten to one multi-indexed col
            .groupby(level='pageid')  # groups per original row
            .agg(', '.join)           # into one string each
        )
    return by_column


def get_frame() -> pd.DataFrame:
    logger.info('Downloading from Wikipedia')
    df = pd.DataFrame.from_records(
        data=fetch_all(template='Mycomorphbox'), index='pageid',
    )
    df = clean(df)
    return collate(df)


def make_table(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    cols = df.index.name + ', ' + df.columns.str.cat(sep=', ')
    cur = conn.execute(
        f'create virtual table mycota using fts5({cols});'
    )
    cur.close()


def connect_or_download(cache_path: Path = Path('.cache.sqlite')) -> sqlite3.Connection:
    if cache_path.exists():
        logger.info('Connecting to cached SQLite database')
    else:
        df = get_frame()
        logger.info('Creating SQLite database')
        try:
            with sqlite3.connect(cache_path) as conn:
                make_table(conn, df)
                df.to_sql(name='mycota', con=conn, if_exists='append')
        except sqlite3.Error:
            # remove rather than leaving an inconsistent file
            cache_path.unlink(missing_ok=True)
            raise
    return sqlite3.connect(f'file:{cache_path}?mode=ro', uri=True, autocommit=False)


def dump_schema(conn: sqlite3.Connection) -> str:
    cur = conn.execute(
        "select sql from sqlite_master where type='table' and name='mycota';"
    )
    try:
        res, = cur.fetchone()
        return res
    finally:
        cur.close()


def dump_cols(conn: sqlite3.Connection) -> typing.Iterable[str]:
    pd.options.display.max_rows = None  # type: ignore  # stub is wrong
    cur = conn.execute('''
        select name from pragma_table_info('mycota')
        -- exclude known generated columns
        where name not in ('capShape', 'ecologicalType', 'howEdible', 'sporePrintColor', 'stipeCharacter', 'whichGills')
        order by name
    ''')
    try:
        for column, in cur.fetchall():
            if column not in {'pageid', 'name', 'title'}:
                df = pd.read_sql_query(
                    sql=f'select {column}, count(*) from mycota group by {column} order by {column}',
                    con=conn,
                )
                yield str(df)
    finally:
        cur.close()


def run_queries(conn: sqlite3.Connection, queries: typing.Iterable[str]) -> None:
    pd.options.display.max_columns = 0
    pd.options.display.max_rows = None  # type: ignore  # stub is wrong
    for query in queries:
        print(pd.read_sql_query(sql=query, con=conn))
