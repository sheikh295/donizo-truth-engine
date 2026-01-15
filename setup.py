from setuptools import setup, find_packages

# Long description
long_description = "Deterministic financial pricing engine for construction markets"

setup(
    name="donizo-engine",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "donizo_engine=donizo_engine.cli:main",
        ],
    },
    python_requires=">=3.10",
    author="Donizo Team",
    description="Deterministic financial pricing engine for construction markets",
    long_description=long_description,
    long_description_content_type="text/markdown",
)
