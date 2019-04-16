# LatViz
A small command line interface for visualizing gauge field configurations.

Two methods exist for visualizing Gluonic fields, one with [Visit](https://wci.llnl.gov/simulation/computer-codes/visit) and one with [Mayavi](http://docs.enthought.com/mayavi/mayavi/), although the former is on a seperate branch.

This project was created by [hmvege](http://github.com/hmvege) and [giopede](http://github.com/giopede).

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


## Test data

Running 
```
python LViz.py example_data 32 64 -flow 800 -obs "Energy" --title "Energy density" -nc 15 -vmax 0.1 -vmin 0.001 --correction_factor -0.015625
```
for the configuration 
```
example_data/field_density_b62_b6.200000_N32_NT64_np512_config00800.bin
```
where `--correction_factor` adds a normalization correction `-1/64` to the field configuration due to an error in field configuration, produces the figure

<p align="center">
    <img src="figures/energy_flow_t800.gif" alt="Topological charge of the gauge field" width="600"/>
</p>
