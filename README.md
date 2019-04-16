# LatViz
A small command line interface for visualizing gauge field configurations.

Two methods exist for visualizing Gluonic fields, one with [Visit](https://wci.llnl.gov/simulation/computer-codes/visit) and one with [Mayavi](http://docs.enthought.com/mayavi/mayavi/), although the former is on a seperate branch.

This project was created by @hmvege and @giopede.

<p align="center">
    <img src="figures/Topological_charge_flow_t400.gif" alt="Topological charge of the gauge field" width="600"/>
</p>
    
<p align="center">
    <i>The topological charge of a gauge field.</i>
</p>


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