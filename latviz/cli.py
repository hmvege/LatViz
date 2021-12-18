import datetime
from pathlib import Path

import click
from loguru import logger

from latviz.latviz import create_animation, plot_iso_surface
from latviz.utils import load_fields


@click.command(context_settings={"show_default": True})
@click.argument(
    "field_paths", nargs=-1, type=click.Path(exists=True, path_type=Path)
)
@click.option("-n", required=True, type=int, help="Spatial dimensions.")
@click.option("-nt", required=True, type=int, help="Temporal dimensions.")
@click.option(
    "-t",
    "--time_slice",
    type=int,
    default=None,
    help=(
        "Time slice to select in case that multiple fields/observables are "
        "provided."
    ),
)
@click.option(
    "-o",
    "--output-folder",
    type=click.Path(exists=True, path_type=Path),
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
    help="If true, will keep individual frames used in animation.",
)
@click.option(
    "-c",
    "--n_contours",
    type=int,
    default=20,
    help="Number of contours to use.",
)
@click.option(
    "--camera-distance",
    type=float,
    default=1.0,
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
    help="Figure size. Dimension of animation.",
)
@click.option(
    "--frame-rate",
    type=int,
    default=10,
    help="Frame rate of animation output.",
)
@click.option(
    "--axis-labels",
    default=["X axis", "Y axis", "Z axis"],
    type=(str, str, str),
    help="Axis labels.",
)
def latviz(
    field_paths,
    n,
    nt,
    time_slice,
    output_folder,
    animation_type,
    observable_name,
    vmin,
    vmax,
    keep_frames,
    n_contours,
    camera_distance,
    title,
    figsize,
    frame_rate,
    axis_labels,
):
    """Program for loading configurations and creating animations.

    Takes a folder of configuration(s), and processes them.

    Assumes that each configuration is a binary .bin file, that has the shape
    (time, z, y, x) and have Fortran ordering.
    """

    if len(field_paths) > 1 and time_slice is None:
        logger.warning(
            "Multiple fields provided but no time_slice is provided. Using "
            "time_slice = 0"
        )
        time_slice = 0

    data = load_fields(field_paths, n, nt, time_slice=time_slice)
    logger.info("Data loaded")

    # Set up the output folders
    if output_folder is None:
        time_stamp = datetime.datetime.strftime(
            datetime.datetime.today(), "%Y%m%d-%H%M%S"
        )
        output_folder = Path(
            f"animation_{'-'.join(observable_name.lower().split(' '))}"
            f"_{time_stamp}"
        )
        if output_folder.exists():
            raise ValueError(
                f"default output folder already exists: {str(output_folder)}"
            )
        output_folder.mkdir()

    frames_folder = output_folder / "frames"
    frames_folder.mkdir()

    plot_iso_surface(
        data,
        observable_name,
        frames_folder,
        vmin=vmin,
        vmax=vmax,
        n_contours=n_contours,
        camera_distance=camera_distance,
        xlabel=axis_labels[0],
        ylabel=axis_labels[1],
        zlabel=axis_labels[2],
        title=title,
        figsize=figsize,
    )

    create_animation(
        frames_folder,
        output_folder,
        observable_name,
        animation_type,
        time_slice=time_slice,
        frame_rate=frame_rate,
    )

    if not keep_frames:
        for f in frames_folder.iterdir():
            f.unlink()
        frames_folder.rmdir()
        logger.info(f"Removed {str(frames_folder)} and its content.")
