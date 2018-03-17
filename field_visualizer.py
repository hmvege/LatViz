import numpy as np
import os
from mayavi import mlab
import subprocess
import copy as cp
import re
import mayaviPlot as mplot

def check_folder(folder_name, dryrun, verbose=False):
	# Checks that figures folder exist, and if not will create it
	if not os.path.isdir(folder_name):
		if dryrun or verbose:
			print "> mkdir %s" % folder_name
		if not dryrun:
			os.mkdir(folder_name)

def create_animation(frame_folder, animation_folder, observable, time_point, method, anim_type):
	"""
	Method for created gifs and movies from generated 3D figures.

	Args:
		frame_folder: folder path to figures that will be be stiched together.
		animation_folder: folder path to place animations in.
		observable: observable we are creating a gif or a movie for.
		method: type of 3D plot.
		anim_type: format of animation. Avaliable: 'gif', 'avi'

	Raises:
		AssertionError: if anim_type is not recognized.
	"""

	assert anim_type in ["gif", "avi"], "%s is not a recognized animation type." % anim_type

	animation_path = os.path.join(animation_folder, '%s_%s_t%d.%s' % (observable, method, time_point, "avi"))
	if anim_type == "gif":
		input_paths = os.path.join(frame_folder, '%s_t*.png' % method)
		cmd = ['convert', '-delay', '1', '-loop', '0', input_paths, animation_path]
	else:
		frame_rate = 8

		input_paths = os.path.join(frame_folder, '%s_t%%02d.png' % method)
		cmd = ['ffmpeg', '-framerate', '10', '-i', input_paths, '-y',
			'-qscale', '0', '-r', str(frame_rate), animation_path]
	
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	read_out = proc.stdout.read()
	# print read_out()

	print "%s animation %s created." % (anim_type, animation_path)


class FieldAnimation:
	"""
	Class for handling the animation of lattice fields.
	"""

	_PLOT_PARAMETERS = {
		"title": {
			"energy": "Energy Density",
			"topc": "Topological Charge Density",
		},
		"xlabel": "X",
		"ylabel": "Y",
		"zlabel": "Z",
	}

	def __init__(self, input_folder, output_folder, N, NT, animation_module,
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
		self.NT = NT
		self.data = {}
		self.animation_module = animation_module

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

		# Location of the scalar fields:
		# {input_folder}/scalar_fields/{observable}/{*.bin field data}

		# Output of the animation:
		# {output_folder}/field_animations/{observable}/{animations}

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

			if self.animation_module == "visit":
				self._create_time_slice_files(self.data[obs], obs)

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

		# Goes through flow observables in observable folder
		for flow_obs_file in sorted(os.listdir(obs_folder)):
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
					f.write(data_obj[flow_time][:,:,:,it].tobytes())

				# if self.verbose:
				# 	print "Written binary %s to file." % f_path

				# print np.sum(data_obj[flow_time][:,:,:,it])
				# print np.sum(np.fromfile(f_path))
				# print np.fromfile(f_path).reshape(self.N, self.N, self.N)
				# exit(1)

		# exit(1)


	def _remove_folder_tree(self, folder):
		"""Deletes folder and its files."""

		for frame in os.listdir(folder):
			frame_path = os.path.join(folder, frame)
			if not self.dryrun:
				os.remove(frame_path)
			if self.verbose or self.dryrun:
				print ">rm %s" % frame_path

		if not self.dryrun:
			os.rmdir(folder)

		if self.verbose or self.dryrun:
			print ">rmdir %s" % folder


	def animate(self, observable, time_type, time_slice, mayavi_plot_type="iso_surface", figure_size=(640, 640), **kwargs):
		"""
		Method for animating in flow time or euclidean time.

		Args:
			observable: string name of observable we are looking at.
			time_type: "euclidean" or "flow". Will plot evolution in provided
				time type.
			time_slice: integer in euclidean time we are looking at.
			mayavi_plot_type: optional argument for what kind of animation to
				be performed., default is 'iso_surface'. Choose between 
				'iso_surface', 'points3d' and 'volume'.
			figure_size: tuple of the figure size to be plotted. Default is
				640x640.
			**kwargs passed to the animation function.

		Raises:
			IndexError: if the selected time slice is out of bounds.
			KeyError: if we are trying to plot neither Euclidean nor Flow time,
				if plot type is not recognized, or if the plotting module is 
				not recognized.
		"""

		# Sets up all of the available flow time in a sorted list
		flow_times = sorted([key for key in self.data[observable].keys() if isinstance(key, int)])

		# Sets up folders
		time_type_folder = os.path.join(self.data[observable]["animation_folder"], time_type)
		check_folder(time_type_folder, self.dryrun, verbose=self.verbose)

		if time_type == "flow":
			# For plotting evolution in flow time

			field = []
			
			if time_slice >= self.data[observable][0].shape[-1]:
				raise IndexError(("Out of bounds for plotting flow at Euclidean time point %d"
					" in data with points %d" % (time_slice, self.data[observable][0].shape[-1])))

			# Sets up data to be plotted			
			for t in flow_times:
				field.append(cp.deepcopy(self.data[observable][t][:,:,:,time_slice]))
			field = np.asarray(field)
			field = np.rollaxis(field, 0, 4)

			# Creates the folder to store the different flowed lattice figures in
			time_slice_folder = os.path.join(time_type_folder, "t_eucl" + str(time_slice))

		elif time_type == "euclidean":
			# For plotting evolution in euclidean time
			if time_slice not in sorted(self.data[observable].keys()):
				raise IndexError(("Out of bounds for plotting Euclidean time "
					"evolution at flow time %d with available points as %s" %
					 (time_slice, ", ".join(self.data[observable][t].keys()))))

			field = cp.deepcopy(self.data[observable][time_slice])

			# Creates folder for different times to store the figures in
			time_slice_folder = os.path.join(time_type_folder, "t_flow" + str(time_slice))

		else:
			raise KeyError("Cannot plot in %s." % time_type)

		# Checks that the sub time slice folder exists
		check_folder(time_slice_folder, self.dryrun, verbose=self.verbose)

		# Creates folder of where to store frames
		self.frame_folder = os.path.join(time_slice_folder, "frames")
		check_folder(self.frame_folder, self.dryrun, verbose=self.verbose)

		# Creates folder of where to store the animations
		self.time_slice_folder = time_slice_folder 
		
		max_val = np.max(field)
		min_val = np.min(field)

		if self.animation_module == "mayavi":
			if mayavi_plot_type == "iso_surface":
				if observable == "topc":
					n_contours = 30
				else:
					n_contours = 15

				mplot.plot_iso_surface(field, observable, self.frame_folder, 
					self.time_slice_folder, vmin=min_val, vmax=max_val,
					title=self.data[observable]["title"], 
					n_contours=n_contours, verbose=self.verbose)

			elif mayavi_plot_type == "volume":
				mplot.plot_scalar_field(field, observable, self.frame_folder, 
					self.time_slice_folder, vmin=min_val, vmax=max_val,
					title=self.data[observable]["title"], verbose=self.verbose)

			elif mayavi_plot_type == "points3d":
				mplot.plot_points3d(field, observable, self.frame_folder, 
					self.time_slice_folder, vmin=min_val, vmax=max_val,
					title=self.data[observable]["title"], verbose=self.verbose)

			else:
				raise KeyError("Plot type %s not recognized" % mayavi_plot_type)

			if cgif:
				create_animation(frame_folder, output_animation_folder, observable,
					time_point, mayavi_plot_type, "gif")

			if cmovie:
				create_animation(frame_folder, output_animation_folder, observable,
					time_point, mayavi_plot_type, "avi")

		elif self.animation_module == "visit":
			raise NotImplementedError("Visit module not implemented yet.")

		else:
			raise KeyError("No animation module by the name of %s" % self.animation_module)

		self._remove_folder_tree(self.frame_folder)

	def _launch_visit(self):
		pass

"""
TODO:

antialiasing:
f = mlab.gfc()
f.scene.render_window.aa_frames = 8
mlab.draw() # trigger redraw

"""

def main():
	N_list = [24, 28, 32]
	NT_list = [48, 56, 64]
	observable_list = ["energy", "topc"]
	data_set_list = ["prodRunBeta6_0", "prodRunBeta6_1", "prodRunBeta6_2"]

	animation_method = "mayavi"

	# N_list = [4]
	# NT_list = [8]
	# data_set_list = ["lattice_field_density4x8"]

	base_path_mac = "/Users/hansmathiasmamenvege/Programming/FYSSP100/GluonAction"
	input_folder_list = [os.path.join(base_path_mac, "output", f) for f in data_set_list]
	output_folder_list = [os.path.join(base_path_mac, "figures", f) for f in data_set_list]

	verbose = True
	dryrun = False

	# Command for plotting with visit
	# /Applications/VisIt.app/Contents/Resources/bin/visit -cli -no-win -s visitPlot.py

	for N, NT, input_folder, output_folder in zip(N_list, NT_list, input_folder_list, output_folder_list):

		FieldAnimationObj = FieldAnimation(input_folder, output_folder, N, NT, animation_method, verbose=verbose, dryrun=dryrun)

		for observable in observable_list:
			# FieldAnimationObj.animate(observable, "euclidean", 0)
			# FieldAnimationObj.animate(observable, "euclidean", 50)
			# FieldAnimationObj.animate(observable, "euclidean", 100)
			# FieldAnimationObj.animate(observable, "euclidean", 200)
			FieldAnimationObj.animate(observable, "euclidean", 400)
			# FieldAnimationObj.animate(observable, "euclidean", 800)
			# FieldAnimationObj.animate(observable, "euclidean", 1000)
			# FieldAnimationObj.animate(observable, "flow", 0)
			# FieldAnimationObj.animate(observable, "flow", 7)
			# FieldAnimationObj.animate(observable, "flow", 0, mayavi_plot_type="volume")
			# FieldAnimationObj.animate(observable, "flow", 7, mayavi_plot_type="volume")

		exit("Done temporarely @ ~600")

	print "\n\nDone"

if __name__ == '__main__':
	main()