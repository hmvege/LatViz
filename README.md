# LatViz

A program containing two methods for visualizing Gluonic fields, one with [Visit](https://wci.llnl.gov/simulation/computer-codes/visit) and one with [Mayavi](http://docs.enthought.com/mayavi/mayavi/).

## Installing
First, set up a clean conda environment for Python 3,
```
conda create -n env-mayavi-py3.6.8 python=3.6.8
```

`ffmpeg` is needed in order to create the animations.
```
brew install ffmpeg
```

Install the required modules for Mayavi and any additional modules required,
```
pip3 install tqdm numpy mayavi
```