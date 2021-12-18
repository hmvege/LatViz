from setuptools import setup

PACKAGE_NAME = "latviz"

VERSION = "0.0.2"

DESCRIPTION = (
    "A tool for producing visualizations of Lattice QCD fields. "
    "Accepts fields as binary files, where the order is (t, x, y, z)."
)

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Mathias Vege",
    license="MIT",
    packages=[
        PACKAGE_NAME,
    ],
    install_requires=[
        "click>=8.0.3",
        "loguru>=0.5.3",
        "numpy>=1.21.4",
        "pyvista>=0.32.1",
        "tqdm>=4.62.3",
    ],
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "latviz=latviz.cli:latviz",
        ]
    },
)
