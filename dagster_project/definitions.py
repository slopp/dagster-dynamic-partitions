import ast
import base64
import json
import os

from dagster import (
    AssetSelection,
    Definitions,
    DynamicPartitionsDefinition,
    StaticPartitionsDefinition,
    SkipReason,
    asset,
    define_asset_job,
    sensor,
)
from dagster_dbt import dbt_cli_resource, load_assets_from_dbt_project
#from dagster_duckdb_pandas import duckdb_pandas_io_manager

from .resources import (
    FakeDuckDBIOManager,
    DirectoryLister,
    ErrorWriter,
    FileReader,
)


resources =  {
        "file_reader": FileReader(directory="data"),
        "error_writer": ErrorWriter(directory="failed"),
        "warehouse_io_manager": FakeDuckDBIOManager(db_path="example.duckdb"),
        "dbt": dbt_cli_resource.configured(
            {"project_dir": "dbt_project", "profiles_dir": "dbt_project/config"}
        ),
}



# --- Assets
#dynamic_regions = DynamicPartitionsDefinition(name="dynamic_regions")
dynamic_regions = StaticPartitionsDefinition(["northeast","southwest","northeast_oopsie"])

@asset(
    io_manager_key="warehouse_io_manager",
    partitions_def=dynamic_regions,
    key_prefix=["vehicles"],
    group_name="vehicles",
)
def plant_data(context, file_reader: FileReader):
    """
    Raw data is read from directory, with each new file 
    creating a new partition 

    """

    file = f"{context.asset_partition_key_for_output()}.csv"
    data = file_reader.read(file)
    data['region'] = context.asset_partition_key_for_output()

    return data


# downstream assets managed by dbt
dbt_assets = load_assets_from_dbt_project(
    project_dir="dbt_project", profiles_dir="dbt_project/config"
)

# --- Jobs
asset_job = define_asset_job(
    name="new_plant_data_job",
    selection=AssetSelection.all(),
    partitions_def=dynamic_regions
)

# --- Sensors
@sensor(job=asset_job)
def watch_for_new_plant_data(context):
    """Sensor watches for new data files to be processed"""

    ls = DirectoryLister(directory="data")
    cursor = context.cursor or None
    already_seen = set()
    if cursor is not None:
        already_seen = set(ast.literal_eval(cursor))

    files = set(ls.list())
    new_files = files - already_seen

    if len(new_files) == 0:
        return SkipReason("No new files to process")


    run_requests = []

    for f in new_files:
        partition_key=f.replace(".csv", "")
        #dynamic_regions.add_partitions([partition_key], context.instance)
        run_requests.append(
            asset_job.run_request_for_partition(
                partition_key=partition_key #, instance=context.instance
            )
        )
    
    context.update_cursor(str(files))
    return run_requests


defs = Definitions(
    assets=[plant_data, *dbt_assets],
    resources=resources,
    jobs=[asset_job],
    sensors=[watch_for_new_plant_data],
)
