import datetime
import warnings
from pathlib import Path

import click

from latviz.latviz import (
    create_animation,
    plot_iso_surface,
)
from latviz.utils import load_folder_data


@click.command()
@click.argument("input-folder", type=click.Path(exists=True))
@click.option("-n", required=True, type=int, help="Spatial dimensions.")
@click.option("-nt", required=True, type=int, help="Temporal dimensions.")
@click.option(
    "--flow",
    type=int,
    default=None,
    help=(
        "Flow time in given folder to select. If none is provided or just "
        "single file is found, Latviz will default to the first file available"
        " among the sorted files. This will animate in EUCLIDEAN time."
    ),
)
@click.option(
    "--eucl",
    type=int,
    default=None,
    help=(
        "Euclidean time. If folder contains multiple files and a euclidean "
        "time slice index is provided(has to be less than 'nt', the slice of "
        "each sorted file is used for animation. This will animate in FLOW "
        "time."
    ),
)
@click.option(
    "-o",
    "--output-folder",
    type=click.Path(exists=True),
    default=None,
    help=(
        "Output folder location. Temporary frames will be generated in this "
        "folder, and removed afterwards."
    ),
)
@click.option(
    "-a",
    "--animation-type",
    type=click.Choice(["gif", "avi", "mp4"]),
    default="avi",
    help="Types of output file formats.",
)
@click.option(
    "-m",
    "--observable-name",
    default="Observable",
    show_default=True,
    type=str,
    help="Name of the observable we are generating the visualization for.",
)
@click.option(
    "--vmin",
    type=float,
    default=None,
    help="Minimum value to draw contours for.",
)
@click.option(
    "--vmax",
    type=float,
    default=None,
    help="Maximum value to draw contours for.",
)
@click.option(
    "--keep-frames",
    default=False,
    is_flag=True,
    show_default=True,
    help="If true, will keep individual frames used in animation.",
)
@click.option(
    "--ncontours",
    type=int,
    default=20,
    show_default=True,
    help="Number of contours to use.",
)
@click.option(
    "--camera-distance",
    type=float,
    default=0.65,
    show_default=True,
    help="Camera distance to cube. Smaller values means closer.",
)
@click.option(
    "--title",
    type=str,
    default=None,
    help="Title of figure. No title will default to observable name.",
)
@click.option(
    "--figsize",
    type=(int, int),
    default=(1280, 1280),
    show_default=True,
    help="Figure size. Dimension of animation.",
)
@click.option(
    "--frame-rate",
    type=int,
    default=10,
    show_default=True,
    help="Frame rate of animation output.",
)
@click.option(
    "--correction-factor",
    default=None,
    type=float,
    help="If provided, will correct input values with factor. TO BE REMOVED!",
)
@click.option(
    "--axis-labels",
    default=["x", "y", "z"],
    type=(str, str, str),
    help="Axis labels.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    show_default=True,
    help="More verbose output.",
)
@click.option(
    "--dryrun", is_flag=True, show_default=True, help="No data is written."
)
def latviz(
    input_folder,
    n,
    nt,
    flow,
    eucl,
    output_folder,
    animation_type,
    observable_name,
    vmin,
    vmax,
    keep_frames,
    ncontours,
    camera_distance,
    title,
    figsize,
    frame_rate,
    correction_factor,
    axis_labels,
    dryrun,
    verbose,
):
    """Program for loading configurations and creating animations.

    Takes a folder of configuration(s), and processes them.

    TODO: change main argument to pass in series list of files?
    """

    # Sets up Euclidean time
    if eucl is None and flow is None:
        warnings.warn(
            "No flow time or Euclidean time slice is specified. Using the "
            "first file found."
        )
        time_slice = 0
        method = "flow"
    elif eucl is None and flow:
        time_slice = flow
        method = "flow"
    elif eucl and flow is None:
        time_slice = eucl
        method = "eucl"
    else:
        raise UserWarning(
            "Both options 'eucl' and 'flow' has been provided. Please select "
            "only on of them."
        )

    data = load_folder_data(
        Path(input_folder),
        n,
        nt,
        euclidean_time=eucl,
        flow_time=flow,
    )
    if verbose:
        print("Data loaded")

    # Set up the output folders
    if output_folder is None:
        time_stamp = datetime.datetime.strftime(
            datetime.datetime.today(), "%Y%m%d-%H%M%S"
        )
        output_folder = Path(
            f"animation_{' '.join(observable_name.lower().split(' '))}"
            f"_{time_stamp}"
        )
        assert (
            not output_folder.exists()
        ), f"default output folder already exists: {str(output_folder)}"
        output_folder.mkdir()

    frames_folder = output_folder / "frames"
    frames_folder.mkdir()

    plot_iso_surface(
        data,
        observable_name,
        frames_folder,
        vmin=vmin,
        vmax=vmax,
        n_contours=ncontours,
        camera_distance=camera_distance,
        xlabel=axis_labels[0],
        ylabel=axis_labels[1],
        zlabel=axis_labels[2],
        title=observable_name,
        figsize=figsize,
        correction_factor=correction_factor,
        verbose=verbose,
    )

    create_animation(
        frames_folder,
        output_folder,
        observable_name,
        time_slice,
        method,
        animation_type,
        frame_rate=frame_rate,
        verbose=verbose,
    )

    if not keep_frames:
        for f in frames_folder.iterdir():
            f.unlink()
        frames_folder.rmdir()
        if verbose:
            print(f"Removed {str(frames_folder)} and its content.")
