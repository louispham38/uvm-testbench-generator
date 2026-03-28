from setuptools import setup, find_packages

setup(
    name="uvmgen",
    version="1.0.0",
    description="UVM Testbench Generator - SaaS & Local Tool for Verification Engineers",
    packages=find_packages(),
    include_package_data=True,
    package_data={"uvmgen": ["templates/**/*.j2", "static/**/*"]},
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "jinja2>=3.1.2",
        "pydantic>=2.5.0",
        "click>=8.1.7",
        "python-multipart>=0.0.6",
        "aiofiles>=23.2.1",
    ],
    entry_points={
        "console_scripts": [
            "uvmgen=uvmgen.cli:main",
        ],
    },
    python_requires=">=3.9",
)
