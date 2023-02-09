from setuptools import find_packages, setup

if __name__ == "__main__":
    setup(
        name="dagster_project",
        packages=find_packages(),
        package_data={"dagster_project": ["dbt_project/*"]},
        install_requires=[
            "dagster",
            "dagster-cloud",
            "dagster-dbt",
            "pandas",
            "numpy",
            "scipy",
            "dbt-core",
            "dbt-duckdb",
            "requests",
        ],
        extras_require={"dev": ["dagit", "pytest"]},
    )