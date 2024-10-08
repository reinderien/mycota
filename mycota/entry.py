import argparse
import logging
import sys

from .data import connect_or_download, dump_cols, dump_schema, run_queries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='python -m mycota',
        description='Download and query Wikipedia mycota morphology database. Once the database is '
        'created, this program opens it in read-only mode.',
    )
    parser.add_argument(
        '-c', '--columns', action='store_true',
        help='Print group summaries for every column',
    )
    parser.add_argument(
        '-s', '--schema', action='store_true',
        help='Describe the database schema',
    )
    parser.add_argument(
        'query', nargs='*',
        help="One or more SQLite queries selecting from 'mycota'",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    args = parse_args()
    with connect_or_download() as conn:
        if args.schema:
            print(dump_schema(conn))
        if args.columns:
            print('\n\n'.join(dump_cols(conn)))
        run_queries(conn=conn, queries=args.query)
