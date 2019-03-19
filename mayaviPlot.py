import numpy as np
import os
import subprocess
import copy as cp
import re
import matplotlib.image as pltimg
from mayavi import mlab

def check_folder(folder_name, dryrun=False, verbose=False):
	# Checks that figures folder exist, and if not will create it
	if not os.path.isdir(folder_name):
		if dryrun or verbose:
			print "> mkdir %s" % folder_name
		if not dryrun:
			os.mkdir(folder_name)


def create_animation(frame_folder, animation_folder, observable, time_point,
	method, anim_type, file_type):
	"""
	Method for created gifs and movies from generated 3D figures.

	Args:
		frame_folder: folder path to figures that will be be stiched together.
		animation_folder: folder path to place animations in.
		observable: observable we are creating a gif or a movie for.
		method: type of 3D plot.
		anim_type: format of animation. Avaliable: 'gif', 'avi'
		file_type: type of picture file we are converting to an animation.
		figsize: integer tuple of the figure size.
	Raises:
		AssertionError: if anim_type is not recognized.
	"""

	assert anim_type in [
	    "gif", "avi", "mp4"], "%s is not a recognized animation type." % anim_type

	# size = figsize
	def _get_size(folder, fpath):
		size = pltimg.imread(os.path.join(folder, fpath)).shape[:2]
		_return_size = [size[0], size[1]]
		for i, s in enumerate(size):
			if s % 2 != 0:
				_return_size[i] = s + 1
		return _return_size[::-1]

	animation_path = os.path.join(animation_folder, '%s_%s_t%d.%s' % (
	    observable, method, time_point, anim_type))
	if anim_type == "gif":
		input_paths = os.path.join(frame_folder, '%s_t*.%s' % (method, file_type))
		cmd = ['convert', '-delay', '1', '-loop', '0', input_paths, animation_path]

	elif anim_type == "mp4":
		frame_rate = 10
		input_paths = os.path.join(
		    frame_folder, '%s_t%%02d.%s' % (method, file_type))
		size = _get_size(frame_folder, os.listdir(frame_folder)[0])
		cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-c:v',
			'libx264', '-crf', '0', '-preset', 'veryslow', '-c:a', 'libmp3lame',
			'-b:a', '320k', '-y', '-vf', 'scale=%d:%d' % (size[0], size[1]),
			'-r', str(frame_rate), animation_path]
		# cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-c:v',
		# 	'libx264', '-crf', '0', '-preset', 'veryslow', '-c:a', 'libmp3lame',
		# 	'-b:a', '320k', '-y', '-r', str(frame_rate), animation_path]

		# For converting to a good format:
		# ffmpeg -i energy_iso_surface_t1000.mp4 -pix_fmt yuv420p -crf 18 energy_iso_surface_t1000_good.mp4

	else:
		frame_rate = 10
		input_paths = os.path.join(
		    frame_folder, '%s_t%%02d.%s' % (method, file_type))
		size = _get_size(frame_folder, os.listdir(input_paths)[0])
		cmd = ['ffmpeg', '-r', str(frame_rate), '-i', input_paths, '-y',
			'-qscale:v', '0', '-vf', 'scale=%d:%d' % (size[0], size[1]),
			'-r', str(frame_rate), animation_path]

	print "> %s" % " ".join(cmd)
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	read_out = proc.stdout.read()

	print "Animation %s created." % animation_path


class FieldAnimation:
	"""
	Class for handling the animation of lattice fields.

	Location of the scalar fields:
	{input_folder}/scalar_fields/{observable}/{*.bin field data}

	Output of the animation:
	{output_folder}/field_animations/{observable}/{animations}

	"""

	def __init__(self, input_folder, output_folder, N, flow_times=None,
		verbose=False, dryrun=False):
		"""
		Initializer for the field animator.

		Args:
			batch_data_folder: absolute path to the data folder. Will look
				for scalar fields inside, and observables inside there. The
				batch name will be extracted from the last folder. An example
				is: /{abs_path_to_data_batch}/data_batch/beta_value/

		"""
		self.verbose = verbose
		self.dryrun = dryrun
		self.N = N
		self.NT = 2*N
		self.data = {}

		if flow_times != None:
			self.flow_times = flow_times
		else:
			self.flow_times = False

		# Folders should work even though they are relative paths
		self.input_folder = os.path.abspath(input_folder)
		self.output_folder = os.path.abspath(output_folder)

		# Ensures folder can be accessed
		self.input_folder = os.path.expanduser(self.input_folder)
		self.output_folder = os.path.expanduser(self.output_folder)

		# Checks that the output folder exists
		check_folder(self.output_folder, self.dryrun, verbose=self.verbose)
		self.output_folder = os.path.join(self.output_folder, "field_animations")

		# Checks that the output animation figures folder exist
		check_folder(self.output_folder, self.dryrun, verbose=self.verbose)

		self._retrieve_field_data()

		# Camera parameters
		self.cam_retrieved = False
		self.view = None

		# Creates output folders for storing the animations
		for obs in self.data:
			# Creates folder of where to store the animation
			obs_anim_folder = os.path.join(self.output_folder, obs)
			check_folder(obs_anim_folder, self.dryrun, verbose=self.verbose)
			self.data[obs]["animation_folder"] = obs_anim_folder

	def _retrieve_field_data(self):
		"""Function for retrieving fields."""

		# Load the different data of the fields
		scalar_field_folder = os.path.join(self.input_folder, "scalar_fields")

		assert os.path.isdir(scalar_field_folder), ("%s folder not found."
			% scalar_field_folder)

		# Goes through the observables in the scalar fields folder
		for obs in os.listdir(scalar_field_folder):
			obs_folder = os.path.join(scalar_field_folder, obs)

			# Skips non-fodlers such as .DS_Store
			if not os.path.isdir(obs_folder):
				continue

			# Ensures we have flow time files in the observable folder
			if len(os.listdir(obs_folder)) == 0:
				continue

			self.data[obs] = cp.deepcopy(self._get_flow_files(obs_folder))

			# Creates folder of where to store the animation
			obs_folder_path = os.path.join(self.output_folder, obs)
			check_folder(obs_folder_path, self.dryrun, verbose=self.verbose)
			self.data[obs]["animation_folder"] = obs_folder_path

			# Factors in missing -1.0/64.0
			if obs == "energy":
				for t in self.data[obs].keys():
					if not isinstance(t, int):
						continue
					self.data[obs][t] *= (-1.0/64.0)

			# Sets the title of the plot
			if obs == "energy":
				self.data[obs]["title"] = "Energy"
			else:
				self.data[obs]["title"] = "Topological charge"

			if self.verbose:
				print "Data retrieved for observable %s." % obs

	def _get_flow_files(self, obs_folder):
		"""
		Function for populating a data dicitonary for a given observable folder.
		"""
		data_dict = {}

		flow_file_list = [f for f in os.listdir(obs_folder) if not f.startswith(".")]
		flow_file_list = [f for f in flow_file_list if f.endswith("bin")]

		# Only retrieves relevant files
		if self.flow_times != False:
			flow_file_list = [
			    f for f in flow_file_list if self._get_cfg_num_from_file(f) in self.flow_times]

		# Goes through flow observables in observable folder
		for flow_obs_file in sorted(flow_file_list):
			flow_obs_file_path = os.path.join(obs_folder, flow_obs_file)

			# Gets data array
			raw_data = np.fromfile(flow_obs_file_path)

			if self.verbose:
				print "Retrieved file %s" % flow_obs_file_path

			# Gets the flow time
			flow_time = self._get_cfg_num_from_file(flow_obs_file)

			# Converts data array to data field, and sets it in the dictionary
			data_dict[flow_time] = self._convert_to_field(raw_data)

		return data_dict

	def _convert_to_field(self, data_array):
		"""Converts data array to a field."""
		_field = np.zeros((self.N, self.N, self.N, self.NT))
		for it in xrange(self.NT):
			for iz in xrange(self.N):
				for iy in xrange(self.N):
					for ix in xrange(self.N):
						_field[ix, iy, iz, it] = data_array[self._index(ix, iy, iz, it)]

		return _field

	def _index(self, i, j, k, l):
		"""Global column-major contigious memory locator."""
		return int(i + self.N*(j + self.N*(k + self.N*l)))

	def _get_cfg_num_from_file(self, fname):
		"""
		Function for getting the flow time from a file name by looking
		for 'config'.

		Args:
			fname: string file name to look for config number in.

		Returns:
			integer config number.
		"""
		_flow_time_list = re.findall("config(\d+)", fname)
		assert len(_flow_time_list) == 1, "error in file name: %s" % fname
		return int(_flow_time_list[0])

	def _create_time_slice_files(self, data_obj, observable):
		"""Create binary time sliced files."""

		# Temporary binary folder to store splitted binary files in.
		temp_bin_folder = os.path.join(data_obj["animation_folder"], "temp")
		check_folder(temp_bin_folder, self.dryrun, self.verbose)

		for flow_time in [ft for ft in data_obj if isinstance(ft, int)]:

			# Creates temporary flow time folder
			temp_flow_time_folder = os.path.join(temp_bin_folder, str(flow_time))
			check_folder(temp_flow_time_folder, self.dryrun, self.verbose)

			for it in xrange(self.NT):
				f_path = os.path.join(temp_flow_time_folder, "file%03d.splitbin" % it)

				with open(f_path, "wb") as f:
					f.write(data_obj[flow_time][:, :, :, it].tobytes())

	def _remove_folder_tree(self, folder):
		"""Deletes folder and its files."""

		for frame in os.listdir(folder):
			frame_path = os.path.join(folder, frame)
			if not self.dryrun:
				os.remove(frame_path)
			if self.verbose or self.dryrun:
				print "> rm %s" % frame_path

		if not self.dryrun:
			os.rmdir(folder)

		if self.verbose or self.dryrun:
			print "> rmdir %s" % folder

	def animate(self, observable, time_type, time_slice, vmin=None, vmax=None,
		plot_type="iso_surface", figure_size=(640, 640), cgif=True,
		cmovie=True, clean_up=True, n_contours=20, camera_distance=1.0,
		file_type="png"):
		"""
		Method for animating in flow time or euclidean time.

		Args:
			observable: string name of observable we are looking at.
			time_type: "euclidean" or "flow". Will plot evolution in provided
				time type.
			time_slice: integer in euclidean time we are looking at.
			plot_type: optional argument for what kind of animation to be
				performed., default is 'iso_surface'. Choose between
				'iso_surface', 'points3d' and 'volume'.
			figure_size: tuple of the figure size to be plotted. Default is
				640x640.
			cgif: bool, create gif.
			cmovie: bool, create avi movie.

		Raises:
			IndexError: if the selected time slice is out of bounds.
			KeyError: if we are trying to plot neither Euclidean nor Flow time,
				if plot type is not recognized, or if the plotting module is
				not recognized.
		"""

		# Sets up all of the available flow time in a sorted list
		flow_times = sorted(
		    [key for key in self.data[observable].keys() if isinstance(key, int)])

		# Sets up folders
		time_type_folder = os.path.join(
		    self.data[observable]["animation_folder"], time_type)
		check_folder(time_type_folder, self.dryrun, verbose=self.verbose)

		if time_type == "flow":
			# For plotting evolution in flow time

			field = []

			if time_slice >= self.data[observable][0].shape[-1]:
				raise IndexError(("Out of bounds for plotting flow at Euclidean time point %d"
					" in data with points %d" % (time_slice, self.data[observable][0].shape[-1])))

			# Sets up data to be plotted
			for t in flow_times:
				field.append(cp.deepcopy(self.data[observable][t][:, :, :, time_slice]))
			field = np.asarray(field)
			field = np.rollaxis(field, 0, 4)

			# Creates the folder to store the different flowed lattice figures in
			time_slice_folder = os.path.join(
			    time_type_folder, "t_eucl" + str(time_slice))

		elif time_type == "euclidean":
			# For plotting evolution in euclidean time
			if time_slice not in sorted(self.data[observable].keys()):
				print("Out of bounds for plotting Euclidean time "
					"evolution at flow time %d with available points as %s" %
					 (time_slice, ", ".join([str(i) for i in sorted(self.data[observable].keys()) if isinstance(i, int)])))
				return

			field = cp.deepcopy(self.data[observable][time_slice])

			# Creates folder for different times to store the figures in
			time_slice_folder = os.path.join(
			    time_type_folder, "t_flow" + str(time_slice))

		else:
			raise KeyError("Cannot plot in %s." % time_type)

		# Checks that the sub time slice folder exists
		check_folder(time_slice_folder, self.dryrun, verbose=self.verbose)

		# Creates folder of where to store frames
		self.frame_folder = os.path.join(time_slice_folder, "frames")
		check_folder(self.frame_folder, self.dryrun, verbose=self.verbose)

		# Creates folder of where to store the animations
		self.time_slice_folder = time_slice_folder

		if vmin == None:
			vmin = np.min(field)
		if vmax == None:
			vmax = np.max(field)

		# if observable == "energy":
		# 	vmin = np.log(vmin)
		# 	vmax = np.log(vmax)

		if plot_type == "iso_surface":
			plot_iso_surface(field, observable, self.frame_folder,
				self.time_slice_folder, vmin=vmin, vmax=vmax,
				title=self.data[observable]["title"],
				n_contours=n_contours, verbose=self.verbose,
				camera_distance=camera_distance, figsize=figure_size,
				file_type=file_type)

		elif plot_type == "volume":
			plot_scalar_field(field, observable, self.frame_folder,
				self.time_slice_folder, vmin=vmin, vmax=vmax,
				title=self.data[observable]["title"], verbose=self.verbose,
				camera_distance=camera_distance, figsize=figure_size,
				file_type=file_type)

		elif plot_type == "points3d":
			plot_points3d(field, observable, self.frame_folder,
				self.time_slice_folder, vmin=vmin, vmax=vmax,
				title=self.data[observable]["title"], verbose=self.verbose,
				camera_distance=camera_distance, figsize=figure_size,
				file_type=file_type)

		else:
			raise KeyError("Plot type %s not recognized" % plot_type)

		if cgif:
			create_animation(self.frame_folder, self.time_slice_folder,
				observable, time_slice, plot_type, "gif", file_type)

		if cmovie:
			create_animation(self.frame_folder, self.time_slice_folder,
				observable, time_slice, plot_type, "mp4", file_type)

		if clean_up:
			self._remove_folder_tree(self.frame_folder)


def plot_iso_surface(F, observable, frame_folder, output_animation_folder,
	file_type="png", vmin=None, vmax=None, cgif=True, cmovie=True,
	n_contours=20, camera_distance=1.0, xlabel="x", ylabel="y",
	zlabel="z", title=None, figsize=(640, 640), verbose=False):
	"""
	Function for plotting iso surfaces and animate the result.

	Args:
		F: field array of size (N,N,N,n_time_points) to plot. The number of
			points to animate over is always the last dimension.
		observable: str of observable we are plotting.
		frame_folder: location of where to temporary store frames.
		output_animation_folder: full folder path of where to store animations.
		file_type: string of file extension type. Default is 'png'.
		vmin: float lower cutoff value of the field. Default is None.
		vmax: float upper cutoff value of the field. Default is None.
		cgif: bool if we are to create a gif. Default is True.
		cmovie: bool if we are to create a movie. Default is True.
		n_contours: optional integer argument for number of contours.
			Default is 15.
		verbose: default is False
	"""

	N, _, _, n_time_points = F.shape

	if title != None:
		title += ", "
	else:
		title = ""

	if observable == "energy":
		# contour_list = np.logspace(vmin, vmax, n_contours)
		# vmin = np.log(vmin)
		# vmax = np.log(vmax)
		contour_list = np.logspace(np.log(vmin), np.log(vmax), n_contours)
	else:
		contour_list = np.linspace(vmin, vmax, 30)

	contour_list = contour_list.tolist()

	f = mlab.figure(size=figsize, bgcolor=(0.8, 0.8, 0.8), fgcolor=(1, 1, 1))

	# Render options
	f.scene.render_window.point_smoothing = True
	f.scene.render_window.line_smoothing = True
	f.scene.render_window.polygon_smoothing = True
	f.scene.render_window.multi_samples = 8  # Try with 4 if you think this is slow

	for it in xrange(n_time_points):
		mlab.clf(figure=f)

		source = mlab.pipeline.scalar_field(F[:, :, :, it], figure=f)
		mlab.pipeline.iso_surface(source, vmin=vmin, vmax=vmax,
			contours=contour_list, reset_zoom=False, opacity=0.5,
			figure=f)

		mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
				focalpoint=(N/2.0, N/2.0, N/2.0), figure=f)

		# mlab.draw(f)

		mlab.scalarbar(title=" ")
		mlab.title(title + "t=%d" % (it + 1), size=0.4, height=0.94)
		mlab.xlabel(xlabel)
		mlab.ylabel(ylabel)
		mlab.zlabel(zlabel)

		fpath = os.path.join(frame_folder, "iso_surface_t%02d.%s" % (it, file_type))

		mlab.savefig(fpath, figure=f, magnification='auto', size=None)

		if verbose:
			print "file created at %s" % fpath

	mlab.close()


def plot_scalar_field(F, observable, frame_folder, output_animation_folder,
	file_type="png", vmin=None, vmax=None, cgif=True, cmovie=True,
	camera_distance=1.0, xlabel="x", ylabel="y", zlabel="z", title=None,
	figsize=(640, 640), verbose=False):
	"""
	Function for plotting a scalar field.

	Args:
		F: field array of size (N,N,N,n_time_points) to plot. The number of
			points to animate over is always the last dimension.
		observable: str of observable we are plotting.
		frame_folder: location of where to temporary store frames.
		output_animation_folder: full folder path of where to store animations.
		file_type: string of file extension type. Default is 'png'.
		vmin: float lower cutoff value of the field. Default is None.
		vmax: float upper cutoff value of the field. Default is None.
		cgif: bool if we are to create a gif. Default is True.
		cmovie: bool if we are to create a movie. Default is True.
		verbose: default is False

	"""

	N, _, _, n_time_points = F.shape

	if title != None:
		title += ", "
	else:
		title = ""

	f = mlab.figure(size=figsize, bgcolor=(0.8, 0.8, 0.8), fgcolor=(1, 1, 1))

	# Render options
	f.scene.render_window.point_smoothing = True
	f.scene.render_window.line_smoothing = True
	f.scene.render_window.polygon_smoothing = True
	f.scene.render_window.multi_samples = 8  # Try with 4 if you think this is slow

	for it in xrange(n_time_points):

		mlab.clf(figure=f)

		source = mlab.pipeline.scalar_field(F[:, :, :, it], figure=f)
		vol = mlab.pipeline.volume(source, vmin=vmin, vmax=vmax)

		mlab.scalarbar(title=" ")
		mlab.title(title + "t=%d" % (it + 1), size=0.4, height=0.94)
		mlab.xlabel(xlabel)
		mlab.ylabel(ylabel)
		mlab.zlabel(zlabel)

		mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
				focalpoint=(N/2.0, N/2.0, N/2.0), figure=f)

		fpath = os.path.join(frame_folder, "volume_t%02d.%s" % (it, file_type))

		mlab.savefig(fpath, figure=f, magnification='auto', size=None)

		if verbose:
			print "file created at %s" % fpath

	mlab.close()


def plot_points3d(F, observable, frame_folder, output_animation_folder,
	file_type="png", vmin=None, vmax=None, cgif=True, cmovie=True,
	camera_distance=1.0, xlabel="x", ylabel="y", zlabel="z", title=None,
	figsize=(640, 640), verbose=False, use_scale_factor=False):
	"""
	Function for plotting points3d of the field.

	Args:
		F: field array of size (N,N,N,NT) to plot.
		n_time_points: integer of time points NT to animate over.
		observable: str of observable we are plotting.
		time_point: int time point we are looking at.
		file_type: string of file extension type. Default is 'png'.
		vmin: float lower cutoff value of the field. Default is None.
		vmax: float upper cutoff value of the field. Default is None.
		cgif: bool if we are to create a gif.
		cmovie: bool if we are to create a movie.
	"""
	raise DeprecationWarning(__name__)

	mlab.figure(size=figsize)

	if not use_scale_factor:
		factor = 1
	else:
		factor = 100

	F *= factor
	const = 0.25  # Lower limit on spheres

	for it in xrange(n_time_points):
		mlab.clf()

		mlab.points3d(F[:, :, :, it], vmin=vmin*factor, vmax=vmax *
		              factor, scale_factor=scale_factor, scale_mode="scalar")

		mlab.scalarbar(title="")
		mlab.title(title[observable] + ", t=%d" % it, size=0.4, height=0.94)
		mlab.xlabel(xlabel)
		mlab.ylabel(ylabel)
		mlab.zlabel(zlabel)

		if not use_scale_factor:
			scale_factor = 1.0
		else:
			scale_factor = (np.min(F[:, :, :, it]) - vmin) / \
			                (vmax - vmin) * (1 - const) + const

		mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
				focalpoint=(N/2.0, N/2.0, N/2.0))

		fpath = os.path.join(
		    self.frame_folder, "points3d_t%02d.%s" % (it, file_type))

		mlab.savefig(fpath, figure=f)

		if verbose:
			print "file created at %s" % fpath

	mlab.close()


def main():
	N_list = [24, 28, 32]
	observable_list = ["energy", "topc"]
	observable_list = ["topc"]
	data_set_list = [""]
	camdist = 0.75
	figure_size = (1280, 1280)

	# N_list = [4]
	# NT_list = [8]
	# data_set_list = ["lattice_field_density4x8"]

 # 	../GluonAction/scalar_fields_data/freq10/field_density_freq10_NF400_beta62/scalar_fields/
	# base_path_mac = "/Users/hansmathiasmamenvege/Programming/LQCD/GluonAction/"
	# base_path_mac += "scalar_fields_data/freq25"
	# input_folder_list = [os.path.join(base_path_mac, "output", f) for f in data_set_list]
	# output_folder_list = [os.path.join(base_path_mac, "figures", f) for f in data_set_list]


	# dataSetList = ["prodRunBeta6_0", "prodRunBeta6_1", "prodRunBeta6_2"] # redundant
	dataSetList = ["field_density_freq10_NF400_beta60", 
				   "field_density_freq10_NF400_beta61",
				   "field_density_freq10_NF400_beta62"]
	# dataSetList = ["b60", "b61", "b62"]
	dataSetList = [""]

	# base_path = "/Users/hansmathiasmamenvege/Programming/LQCD/GluonAction"
	base_path = "/Users/hansmathiasmamenvege/Programming/LQCD/LatViz/input/"


	# inputFolderLocation = "output" # redundant, use freq25(exact same data)
	# inputFolderLocation = "scalar_fields_data/freq25"
	inputFolderLocation = "scalar_fields_data/freq10"
	outputFolderLocation = "figures"

	joinPaths = lambda a, b: os.path.join(base_path, a, b)
	input_folder_list = [joinPaths(inputFolderLocation, f) for f in dataSetList]
	output_folder_list = [joinPaths(outputFolderLocation, f) for f in dataSetList]


	verbose = True
	dryrun = False

	vmin = None
	vmax = None

	# Command for plotting with visit
	# /Applications/VisIt.app/Contents/Resources/bin/visit -cli -no-win -s visitPlot.py

	for N, input_folder, output_folder in zip(N_list, input_folder_list, output_folder_list):

		if N != 32:
			continue

		FieldAnimationObj = FieldAnimation(input_folder, output_folder, N, verbose=verbose, dryrun=dryrun)

		for observable in observable_list:
			# FieldAnimationObj.animate(observable, "euclidean", 0, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 50, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 100, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 200, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 400, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 600, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 800, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			# FieldAnimationObj.animate(observable, "euclidean", 1000, camera_distance=camdist, vmax=vmax, vmin=vmin, figure_size=figure_size)
			FieldAnimationObj.animate(observable, "flow", 0, camera_distance=camdist)
			FieldAnimationObj.animate(observable, "flow", 7, camera_distance=camdist)
			# FieldAnimationObj.animate(observable, "flow", 0, plot_type="volume", camera_distance=camdist)
			# FieldAnimationObj.animate(observable, "flow", 7, plot_type="volume", camera_distance=camdist)

	print "\n\nDone"


if __name__ == '__main__':
	main()
