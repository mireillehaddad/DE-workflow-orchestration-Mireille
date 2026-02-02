#!/usr/bin/env python
# coding: utf-8

import click
import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm
from pathlib import Path


def ingest_parquet(
    file_path: Path,
    engine,
    target_table: str,
    chunksize: int = 100000,
):
    # Read parquet
    df = pd.read_parquet(file_path)

    # Create table schema
    df.head(0).to_sql(
        name=target_table,
        con=engine,
        if_exists="replace",
        index=False
    )
    print(f"Table {target_table} created")

    # Insert in chunks
    total_rows = len(df)
    for start in tqdm(range(0, total_rows, chunksize)):
        end = start + chunksize
        df_chunk = df.iloc[start:end]

        df_chunk.to_sql(
            name=target_table,
            con=engine,
            if_exists="append",
            index=False
        )

    print(f"Done ingesting {total_rows} rows into {target_table}")


@click.command()
@click.option('--pg-user', default='root')
@click.option('--pg-pass', default='root')
@click.option('--pg-host', default='localhost')
@click.option('--pg-port', default='5432')
@click.option('--pg-db', default='ny_taxi')
@click.option('--target-table', required=True)
@click.option('--chunksize', default=100000, type=int)
@click.option(
    '--file',
    type=click.Path(exists=True),
    required=True,
    help='Path to parquet file'
)
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, chunksize, file):
    engine = create_engine(
        f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
    )

    ingest_parquet(
        file_path=Path(file),
        engine=engine,
        target_table=target_table,
        chunksize=chunksize
    )


if __name__ == '__main__':
    main()
