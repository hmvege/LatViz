import os
import re
import subprocess
import numpy as np
from tqdm import tqdm
from mayavi import mlab
import argparse


__TMP_FIG_FOLDER = ".fig"


def create_animation(frame_folder, animation_folder, observable, time_point,
                     method, anim_type, frame_rate=10, verbose=True):
    """
    Method for created gifs and movies from generated 3D figures.

    Args:
        frame_folder: folder path to figures that will be be stiched together.
        animation_folder: folder path to place animations in.
        observable: observable we are creating a gif or a movie for.
        method: type of 3D plot.
        anim_type: format of animation. Avaliable: 'gif', 'avi'
        figsize: integer tuple of the figure size.
    Raises:
        AssertionError: if anim_type is not recognized.
    """

    # Removes spaces
    observable = observable.replace(" ", "_")

    # Creates temporary, hidden, folder
    frame_folder = os.path.join(frame_folder, __TMP_FIG_FOLDER)

    input_paths = os.path.join(frame_folder, "iso_surface_t%02d.png")

    animation_path = os.path.join(animation_folder, '%s_%s_t%d.%s' % (
        observable.lower(), method, time_point, anim_type))

    if anim_type == "gif":
        cmd = ['convert', '-delay', '1', '-loop',
               '0', os.path.join(frame_folder, "*.png"), animation_path]

    elif anim_type == "mp4":
        cmd = ['ffmpeg', '-r', str(frame_rate), "-start_number", '0',
               '-i', input_paths, '-c:v', 'libx264', '-crf', '0', '-preset',
               'veryslow', '-c:a', 'libmp3lame', '-b:a', '320k', '-y',
               animation_path]

    elif anim_type == "avi":
        cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-y',
               '-qscale:v', '0', animation_path]
    else:
        raise NameError(
            "{} is not a recognized animation type.".format(anim_type))

    if verbose:
        print("> {}".format(" ".join(cmd)))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()

    print("Animation %s created." % animation_path)

    # removing figures + tmp folder
    if verbose:
        print("Cleaning up:")
    for _f in sorted(os.listdir(frame_folder)):
        _p = os.path.join(frame_folder, _f)
        os.remove(_p)
        if verbose:
            print("> rm {}".format(_p))

    os.rmdir(frame_folder)
    if verbose:
        print("> rmdir {}".format(frame_folder))


def check_folder(folder, dryrun=False, verbose=False):
    # Checks that figures folder exist, and if not will create it
    if not os.path.isdir(folder):
        if dryrun or verbose:
            print("> mkdir %s" % folder)
        if not dryrun:
            os.mkdir(folder)


def plot_iso_surface(field, observable_name, frame_folder,
                     file_type="png", vmin=None, vmax=None, n_contours=30,
                     camera_distance=0.65, xlabel="x", ylabel="y", zlabel="z",
                     title=None, figsize=(1280, 1280), 
                     correction_factor=None, verbose=False):
    """
    Function for plotting iso surfaces and animate the result.

    Args:
        field: field array of size (N,N,N,NT) to plot. The number of
            points to animate over is always the last dimension.
        observable_name: str of observable_name we are plotting.
        frame_folder: location of where to temporary store frames.
        file_type: string of file extension type. Default is 'png'.
        vmin: float lower cutoff value of the field. Default is None.
        vmax: float upper cutoff value of the field. Default is None.
        n_contours: optional integer argument for number of contours.
            Default is 15.
        correction_factor: optional, default None. Will correct plot values 
            with correction_factor.
        verbose: default is False
    """

    assert isinstance(observable_name, str), (
        "Observable name must be string type")
    check_folder(frame_folder, dryrun=False, verbose=verbose)

    # Creates temporary folder for figures
    frame_folder = os.path.join(frame_folder, __TMP_FIG_FOLDER)
    check_folder(frame_folder, dryrun=False, verbose=verbose)

    NT, N = field.shape[:2]

    if not isinstance(correction_factor, type(None)):
        assert isinstance(correction_factor, float), \
            "Correction factor is not of type float: {} type: {}".format(
                correction_factor, type(correction_factor))

        field *= correction_factor

    if not isinstance(title, type(None)):
        title += ", "
    else:
        title = ""

    if isinstance(vmin, type(None)):
        vmin = np.min(field)

    if isinstance(vmax, type(None)):
        vmax = np.max(field)

    # Sets up the contours
    contour_list = np.linspace(vmin, vmax, n_contours)
    contour_list = contour_list.tolist()

    # Makes sure we do not show figure
    mlab.options.offscreen = True

    f = mlab.figure(size=figsize, bgcolor=(0.9, 0.9, 0.9), fgcolor=(0, 0, 0))

    # Render options
    f.scene.render_window.point_smoothing = True
    f.scene.render_window.line_smoothing = True
    f.scene.render_window.polygon_smoothing = True
    f.scene.render_window.multi_samples = 8  # Try with 4 if this is slow

    for it in tqdm(range(NT), desc="Rendering {}".format(observable_name)):
        mlab.clf(figure=f)

        # print (np.min(field[it]), np.max(field[it]))

        source = mlab.pipeline.scalar_field(field[it], figure=f)
        mlab.pipeline.iso_surface(source, vmin=vmin, vmax=vmax,
                                  contours=contour_list, reset_zoom=False,
                                  opacity=0.5, figure=f)

        # Adjusts camera view
        mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
                  focalpoint=(N/2.0, N/2.0, N/2.0), figure=f)

        # mlab.draw(f)

        mlab.scalarbar(title="Contour", orientation="vertical")
        mlab.title(title + "t=%02d" % it, size=0.4, height=0.94)

        # Sets ticks on axis
        ax = mlab.axes(figure=f, nb_labels=5)

        mlab.xlabel(xlabel)
        mlab.ylabel(ylabel)
        mlab.zlabel(zlabel)

        # Creates outline of box
        mlab.outline()

        fpath = os.path.join(
            frame_folder, "iso_surface_t%02d.%s" % (it, file_type))

        mlab.savefig(fpath, figure=f, magnification='auto', size=None)

        if verbose:
            tqdm.write("file created at %s" % fpath)

    mlab.close()


def load_field_from_file(file, N, NT, euclidean_time=None):
    """
    Loads field from file.

    Args:
        file: str, file path to .bin file containing lattice data.
        N: int, spatial time.
        NT: int, temporal time.
        euclidean_time: int, what Euclidean time slice to look at. Default
            is retrieving all Euclidean time slices.
    """
    if isinstance(euclidean_time, type(None)):

        # Loads specific flow time
        return np.fromfile(file, dtype=float).reshape((N, N, N, NT),
                                                      order="F")
    else:

        # Loads euclidean time
        block_size = N**3*8  # 8 is bytes
        start = euclidean_time*block_size

        with open(file, "rb") as fp:
            fp.seek(start)
            block = fp.read(block_size)
            block = np.frombuffer(block, dtype=np.double)

        return np.array(block).reshape((N, N, N), order="F")


def load_folder_data(folder, N, NT, euclidean_time=None, flow_time=None):
    """
    Loads folder containing binary data.
    """

    assert (isinstance(euclidean_time, type(None)) ^
            isinstance(flow_time, type(None))), (
        "Either choose Euclidean time of Flow time")

    def _filter_files(_f):
        """Function for filtering out hidden files. Can be extended."""
        if _f.startswith("."):
            return False
        else:
            return True

    folder_files = list(filter(_filter_files, os.listdir(folder)))
    folder_files = map(lambda _f: os.path.join(folder, _f), folder_files)
    folder_files = list(sorted(folder_files))

    data = []

    if not isinstance(flow_time, type(None)):

        def _flow_time_filter(_f):
            """Selects .bin config with correct flow time."""
            found_flow_time = re.findall(r"config(\d+).bin", _f)
            assert len(found_flow_time) == 1, (
                "Multiple configs for similar flow time %d." % flow_time)

            if int(flow_time) == int(found_flow_time[0]):
                return True
            else:
                return False

        _tmp_folder_files = list(filter(_flow_time_filter, folder_files))

        if len(_tmp_folder_files) == 0:
            raise IOError("No flow data with flow time {0:} found among"
                          " following files: \n{1}".format(
                              flow_time, ", ".join(folder_files)))

        folder_files = _tmp_folder_files

    # Loading data
    for _f in tqdm(folder_files,
                   desc="Reading in data from {}".format(folder)):

        data.append(load_field_from_file(
            _f, N, NT, euclidean_time=euclidean_time))

    # Making sure we return with zeroth axis as the one to animate with.
    if not isinstance(flow_time, type(None)):
        data = np.rollaxis(data[0], -1, 0)
    else:
        data = np.asarray(data)

    return data


def main():
    # Initiating command line parser
    description_string = \
        '''Program for loading configurations and creating animations.'''

    parser = argparse.ArgumentParser(
        prog='LatViz', description=description_string)

    # Basic commands
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--dryrun', default=False, action='store_true',
                        help='Dryrun to not perform any critical actions.')
    parser.add_argument('-v', '--verbose', default=False,
                        action='store_true',
                        help='A more verbose output when generating.')

    # Required arguments
    parser.add_argument("folder", type=str,
                        help="Folder containing configurations.")
    parser.add_argument("N", type=int, help="Spatial size of lattice.")
    parser.add_argument("NT", type=int, help="Temporal size of lattice.")

    # Optional arguments
    parser.add_argument("-obs", "--observable", default="observable",
                        type=str, help="Name of the observable name.")
    parser.add_argument("-at", "--anim_type", default="gif",
                        choices=["gif", "avi", "mp4"], type=str,
                        help="Type of animation to create.")
    parser.add_argument("-figf", "--figures_folder", default="figures",
                        type=str,
                        help="Folder to temporary store figures in.")
    parser.add_argument("-animf", "--animation_folder",
                        default="animations", type=str,
                        help="Folder to store animations in.")

    # Animation related arguments
    parser.add_argument("-vmin", type=float, default=None,
                        help="Minimum value to draw contours for.")
    parser.add_argument("-vmax", type=float, default=None,
                        help="Maximum value to draw contours for.")
    parser.add_argument(
        "--file_type", default="png", type=str,
        help="Filetype to use when creating figures for animation.")
    parser.add_argument("-nc", "--n_contours", default=20, type=int,
                        help="Number of contours to use.")
    parser.add_argument(
        "--camera_distance", default=0.65, type=float,
        help="Camera distance to cube. Smaller values means closer.")
    parser.add_argument("--title", default=None, type=str,
                        help="Title of figure.")
    parser.add_argument("-fz", "--figsize", default=(1280, 1280),
                        type=tuple,
                        help="Figure size. Dimension of animation.")
    parser.add_argument("-fr", "--frame_rate", default=10, type=int,
                        help="Frame rate.")

    # In case field input is bad and needs to be modified.
    parser.add_argument("--correction_factor", default=None, type=float,
                        help=("If provided, will correct input "
                              "values with factor."))

    # Forcing using to specify either flow or euclidean time
    anim_time_group = parser.add_mutually_exclusive_group(required=True)
    anim_time_group.add_argument(
        "-flow", type=int,
        help="Flow time to create euclidean time animation from.")
    anim_time_group.add_argument(
        "-eucl", type=int, help="Euclidean time slice to animate in flow time")

    args = parser.parse_args()

    # Sets up Euclidean time
    if not isinstance(args.eucl, type(None)):
        time_point = args.eucl
        method = "eucl"
    else:
        time_point = args.flow
        method = "flow"

    assert (len(args.figsize) == 2) and (type(args.figsize[0]) == int) \
        and (type(args.figsize[1]) == int), \
        "incorrect figsize: {}".format(figsize)

    assert args.vmin < args.vmax, \
        "vmin is less than vmax: {} < {}".format(args.vmin, args.vmax)

    data = load_folder_data(args.folder, args.N, args.NT,
                            euclidean_time=args.eucl,
                            flow_time=args.flow)

    plot_iso_surface(data, args.observable, args.figures_folder,
                     file_type=args.file_type, vmin=args.vmin, vmax=args.vmax,
                     n_contours=args.n_contours,
                     camera_distance=args.camera_distance, xlabel="x",
                     ylabel="y", zlabel="z", title=args.observable,
                     figsize=args.figsize, 
                     correction_factor=args.correction_factor,
                     verbose=args.verbose)

    create_animation(args.figures_folder, args.animation_folder,
                     args.observable, time_point, method, args.anim_type,
                     frame_rate=args.frame_rate, verbose=args.verbose)


if __name__ == '__main__':
    main()
