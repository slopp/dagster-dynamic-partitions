from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="dagster_project",
        packages=find_packages(),
        package_data={"dagster_project": ["dbt_project/*"]},
        install_requires=[
            "dagster",
            "dagster-dbt",
            "dagster-duckdb",
            "dagster-cloud",
            "dbt-duckdb"
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )