# LatViz - Lattice Visualization
A small command line interface for visualizing gauge field configurations.

LatViz uses the [Mayavi](http://docs.enthought.com/mayavi/mayavi/) package as backbone for creating the frames, then the frames are stitched together using either [ImageMagick](https://imagemagick.org/index.php) or [ffmpeg](https://ffmpeg.org).

There are two categories of animations which can be generated. One is from a single lattice configurations, the other is from a time series of configurations where a time slice has been specified.

This project was created by [hmvege](http://github.com/hmvege) and [giopede](http://github.com/giopede).

<p align="center">
    <img src="figures/topological_charge_flow_t400.gif" alt="Topological charge of the gauge field" width="600"/>
</p>

<p align="center">
    <i>The topological charge of a gauge field.</i>
</p>

## Installation

### The Python environment
First, set up a clean Python environment for Python 3.6 (the latest version currently tested is 3.6.14). Many methods exist, and use whatever method which is preferred,

#### Conda
```bash
conda create -n env-latviz-py3.6.14 python=3.6.14
conda activate env-latviz-py3.6.14
```

#### PyEnv
```bash
pyenv virtualenv 3.6.14 python3.6.14
pyenv activate python3.6.14
```

#### Virtual env `venv`
Assuming Python 3.6.14 is being used, we create the virtual environment `venv` by,

```bash
python -m venv venv
source venv/bin/activate
```

### Animation backends
#### ffmpeg
[ffmpeg](https://ffmpeg.org) is needed in order to create the `avi` and `mp4` animations.

```bash
brew install ffmpeg
```

#### ImageMagick
[ImageMagick](https://imagemagick.org/index.php) is needed to create gifs.
```bash
brew install ImageMagick
```


### Installing LatViz
Install the required modules for Mayavi and any additional modules required,
```bash
pip install -r requirements.txt
```

Then, install the LatViz CLI,

```bash
pip install -e .
```

## Examples

changes.)
### Animating a single configuration
Running
```
latviz example_data -n 32 -nt 64 --flow 800 -m "Energy" --title "Energy density" --ncontours 15 --vmax 0.1 --vmin 0.001 --correction-factor -0.015625
```
for the configuration of the energy density
```
example_data/field_density_b62_b6.200000_N32_NT64_np512_config00800.bin
```
where `--correction_factor` adds a normalization correction `-1/64` to the field configuration due to an error in field configuration, produces the figure

<p align="center">
    <img src="figures/energy_flow_t800.gif" alt="Topological charge of the gauge field" width="600"/>
</p>

### Animating a series of configurations at a specified time slice
An example using of an animation using a set of enumerated configurations. In this case, the application of [gradient flow](https://link.springer.com/article/10.1007/JHEP08(2010)071).

```
latviz *.bin -n 32 -nt 64 --flow 800 -m "Energy" --title "Energy density" --ncontours 15 --vmax 0.1 --vmin 0.001 --correction-factor -0.015625
```

## Testing


## Troubleshooting
