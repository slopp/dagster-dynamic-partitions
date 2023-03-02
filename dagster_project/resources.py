import os
from typing import Optional

import pandas as pd
from dagster._config.structured_config import ConfigurableResource, ConfigurableIOManager
import duckdb

class FileReader(ConfigurableResource):
    """Reads CSVs from a specific folder"""

    directory: Optional[str]

    def read(self, file) -> pd.DataFrame:
        return pd.read_csv(f"{self.directory}/{file}")


class ErrorWriter(ConfigurableResource):
    """Writes failed dataframes to a specific folder"""

    directory: Optional[str]

    def write(self, obj: pd.DataFrame, file: str):
        return obj.to_csv(f"{self.directory}/{file}")


class DirectoryLister(ConfigurableResource):
    """Lists files in a directory"""

    directory: Optional[str]

    def list(self):
        return os.listdir(self.directory)


class FakeDuckDBIOManager(ConfigurableIOManager):
    """ Mostly fake DuckDB IO manager that appends partitioned data to a duckdb table """

    db_path: str

    def handle_output(self, context: "OutputContext", obj: pd.DataFrame) -> None:
        conn = duckdb.connect(database=self.db_path)
        table = context.asset_key.path[-1]
        conn.execute(
            f"create table if not exists {table} as select * from"
            " obj;"
        )
        if not conn.fetchall():
            # table was not created, therefore already exists. Insert the data
            conn.execute(f"insert into {table} select * from obj")

        return

    def load_input(self, context: "InputContext") -> pd.DataFrame:
        conn = duckdb.connect(database=self.db_path)
        df =  conn.execute(f"SELECT * FROM {context.asset_key.path[-1]}").fetchdf()
        conn.close()
        return df


         