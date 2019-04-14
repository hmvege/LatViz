import os
import re
import subprocess
import numpy as np
from tqdm import tqdm
from mayavi import mlab
import argparse


def create_animation(frame_folder, animation_folder, observable, time_point,
                     method, anim_type):
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
    # Updates data folder
    frame_folder = os.path.join(frame_folder, "tmp")

    # size = figsize
    def _get_size(folder, fpath):
        size = pltimg.imread(os.path.join(folder, fpath)).shape[:2]
        _return_size = [size[0], size[1]]
        for i, s in enumerate(size):
            if s % 2 != 0:
                _return_size[i] = s + 1
        return _return_size[::-1]

    input_paths = os.path.join(frame_folder, "iso_surface_t%02d.png")

    animation_path = os.path.join(animation_folder, '%s_%s_t%d.%s' % (
        observable, method, time_point, anim_type))

    frame_rate = 10

    if anim_type == "gif":
        input_paths = list(map(lambda _f: os.path.join(frame_folder, _f),
                               os.listdir(frame_folder)))
        cmd = ['convert', '-delay', '1', '-loop',
               '0', input_paths, animation_path]

    elif anim_type == "mp4":

        # size = _get_size(frame_folder, os.listdir(frame_folder)[0])
        # cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-c:v',
        #        'libx264', '-crf', '0', '-preset', 'veryslow', '-c:a',
        #        'libmp3lame', '-b:a', '320k', '-y', '-vf',
        #        'scale=%d:%d' % (size[0], size[1]),
        #        '-r', str(frame_rate), animation_path]

        cmd = ['ffmpeg', '-r', str(frame_rate), "-start_number", '0',
               '-i', input_paths, '-c:v', 'libx264', '-crf', '0', '-preset',
               'veryslow', '-c:a', 'libmp3lame', '-b:a', '320k', '-y',
               animation_path]

        # For converting to a good format:
        # ffmpeg -i energy_iso_surface_t1000.mp4 -pix_fmt yuv420p -crf 18 energy_iso_surface_t1000_good.mp4

    elif anim_type == "avi":
        # AVI
        # size = _get_size(frame_folder, os.listdir(input_paths)[0])
        # cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-y',
        #        '-qscale:v', '0', '-vf', 'scale=%d:%d' % (size[0], size[1]),
        #        '-r', str(frame_rate), animation_path]

        cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-y',
               '-qscale:v', '0', animation_path]
    else:
        raise NameError(
            "{} is not a recognized animation type.".format(anim_type))

    print("> {}".format(" ".join(cmd)))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    read_out = proc.stdout.read()
    print("Animation %s created." % animation_path)


def check_folder(folder, dryrun=False, verbose=False):
    # Checks that figures folder exist, and if not will create it
    if not os.path.isdir(folder):
        if dryrun or verbose:
            print("> mkdir %s" % folder)
        if not dryrun:
            os.mkdir(folder)


def plot_iso_surface(field, observable_name, frame_folder,
                     file_type="png", vmin=None, vmax=None, cgif=True,
                     cmovie=True, n_contours=20, camera_distance=1.0,
                     xlabel="x", ylabel="y", zlabel="z", title=None,
                     figsize=(1280, 1280), verbose=False):
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
        cgif: bool if we are to create a gif. Default is True.
        cmovie: bool if we are to create a movie. Default is True.
        n_contours: optional integer argument for number of contours.
            Default is 15.
        verbose: default is False
    """

    assert isinstance(observable_name, str), (
        "Observable name must be string type")
    check_folder(frame_folder, dryrun=False, verbose=verbose)

    # Creates temporary folder for figures
    frame_folder = os.path.join(frame_folder, "tmp")
    check_folder(frame_folder, dryrun=False, verbose=verbose)

    NT, N = field.shape[:2]

    if title != None:
        title += ", "
    else:
        title = ""

    if isinstance(vmin, type(None)):
        vmin = np.min(field)

    if isinstance(vmax, type(None)):
        vmax = np.max(field)

    contour_list = np.linspace(vmin, vmax, 30)

    contour_list = contour_list.tolist()

    mlab.options.offscreen = True

    f = mlab.figure(size=figsize, bgcolor=(0.8, 0.8, 0.8), fgcolor=(1, 1, 1))

    # Render options
    f.scene.render_window.point_smoothing = True
    f.scene.render_window.line_smoothing = True
    f.scene.render_window.polygon_smoothing = True
    f.scene.render_window.multi_samples = 8  # Try with 4 if you think this is slow

    for it in tqdm(range(NT), desc="Rendering {}".format(observable_name)):
        mlab.clf(figure=f)

        source = mlab.pipeline.scalar_field(field[it], figure=f)
        mlab.pipeline.iso_surface(source, vmin=vmin, vmax=vmax,
                                  contours=contour_list, reset_zoom=False,
                                  opacity=0.5, figure=f)

        mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
                  focalpoint=(N/2.0, N/2.0, N/2.0), figure=f)

        # mlab.draw(f)

        mlab.scalarbar(title=" ")
        mlab.title(title + "t=%d" % (it + 1), size=0.4, height=0.94)
        mlab.xlabel(xlabel)
        mlab.ylabel(ylabel)
        mlab.zlabel(zlabel)

        fpath = os.path.join(
            frame_folder, "iso_surface_t%02d.%s" % (it, file_type))

        mlab.savefig(fpath, figure=f, magnification='auto', size=None)

        if verbose:
            print("file created at %s" % fpath)

        # mlab.show()

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
        return np.fromfile(file, dtype=float).reshape((N, N, N, NT), order="F")
    else:

        # Loads euclidean time
        block_size = N**3*8
        start = euclidean_time*block_size

        with open(file, "rb") as fp:
            fp.seek(start)
            block = fp.read(block_size)
            # , count=block_size, offset=start)
            block = np.frombuffer(block, dtype=np.double)
            # print (block)

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

        folder_files = list(filter(_flow_time_filter, folder_files))

    for _f in tqdm(folder_files, desc="Reading in data from {}".format(folder)):
        data.append(load_field_from_file(
            _f, N, NT, euclidean_time=euclidean_time))

    # Making sure we return with zeroth axis as the one to animate with.
    if not isinstance(flow_time, type(None)):
        data = np.rollaxis(data[0], -1, 0)
    else:
        data = np.asarray(data)

    return data[:5]


def main():
    N = 32
    NT = 64
    euclidean_time = 1
    flow_time = None
    file_folders = "input/topc"
    figure_folder = "figures/"
    animation_folder = "animations/"
    observable = "topc"

    if not isinstance(euclidean_time, type(None)):
        time_point = euclidean_time
        method = "euclidean"
    else:
        time_point = euclidean_time
        method = "euclidean"

    anim_type = "gif"
    file_type = "png"

    data = load_folder_data(file_folders, N, NT,
                            euclidean_time=euclidean_time,
                            flow_time=flow_time)

    plot_iso_surface(data, observable, figure_folder)

    create_animation(figure_folder, animation_folder, observable, time_point,
                     method, anim_type)

    # ######## Initiating command line parser ########
    # description_string = '''
    # Program for starting large parallel Lattice Quantum Chromo Dynamics jobs.
    # '''
    # parser = argparse.ArgumentParser(prog='GLAC job creator', description=description_string)

    # ######## Prints program version if prompted ########
    # parser.add_argument('--version', action='version', version='%(prog)s 1.0.2')
    # parser.add_argument('--dryrun', default=False, action='store_true', help='Dryrun to not perform any critical actions.')
    # parser.add_argument('-v', '--verbose', default=False, action='store_true', help='A more verbose output when generating.')


if __name__ == '__main__':
    main()
