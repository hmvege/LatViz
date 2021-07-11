from setuptools import setup

PACKAGE_NAME = "latviz"

VERSION = "0.0.2"

DESCRIPTION = (
    "A tool for producing visualizations of Gluonic Fields. Accepts binary "
    "files, where the order is (t, x, y, z)."
)

# with open('requirements.txt') as f:
#     requirements = f.read().splitlines()

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    author="Mathias Vege",
    license="MIT",
    packages=[
        PACKAGE_NAME,
    ],
    # install_requires=requirements,
    # install_requires=[
    #     "numpy==1.19.5",
    #     "tqdm>=4.61.2",
    #     "click>=7.1.2",
    #     # Exact package versions
    #     "apptools==4.4.0"
    #     "configobj==5.0.6"
    #     "envisage==4.7.1"
    #     "mayavi==4.6.2"
    #     "pyface==6.0.0"
    #     "Pygments==2.3.1"
    #     "six==1.12.0"
    #     "traits==5.1.0"
    #     "traitsui==6.0.0"
    #     "vtk==8.1.2"
    # ],
    # python_requires="==3.6.14",
    # setup_requires=["setuptools_scm"],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "latviz=latviz.cli:latviz",
        ]
    },
)
