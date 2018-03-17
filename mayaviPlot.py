from mayavi import mlab
import numpy as np
import os

def plot_iso_surface(F, observable, frame_folder, output_animation_folder, 
	file_type="png", vmin=None, vmax=None, cgif=True, cmovie=True, 
	n_contours=15, camera_distance=1.0, xlabel=r"$x$", ylabel=r"$y$", 
	zlabel=r"$z$", title=None, figsize=(640, 640), verbose=False):
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
		contour_list = np.logspace(np.log(vmin), np.log(vmax), n_contours)
	else:
		contour_list = np.linspace(vmin, vmax, n_contours)

	contour_list = contour_list.tolist()

	f = mlab.figure(size=figsize, bgcolor=(0.8, 0.8, 0.8), fgcolor=(1, 1, 1))

	# Render options	
	f.scene.render_window.point_smoothing = True
	f.scene.render_window.line_smoothing = True
	f.scene.render_window.polygon_smoothing = True
	f.scene.render_window.multi_samples = 8 # Try with 4 if you think this is slow

	for it in xrange(n_time_points):
		mlab.clf()

		source = mlab.pipeline.scalar_field(F[:,:,:,it])
		mlab.pipeline.iso_surface(source, vmin=vmin, vmax=vmax, 
			contours=contour_list, reset_zoom=False, opacity=0.8)

		mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
				focalpoint=(N/2.0, N/2.0, N/2.0))

		mlab.scalarbar(title=" ")
		mlab.title(title + r"$t=%d$" % (it + 1), size=0.4, height=0.94)
		mlab.xlabel(xlabel)
		mlab.ylabel(ylabel)
		mlab.zlabel(zlabel)

		fpath = os.path.join(frame_folder, "iso_surface_t%02d.%s" % (it, file_type))
		mlab.savefig(fpath)
		if verbose:
			print "file created at %s" % fpath

	mlab.close()

def plot_scalar_field(F, observable, frame_folder, output_animation_folder, 
	file_type="png", vmin=None, vmax=None, cgif=True, cmovie=True, 
	camera_distance=1.0, xlabel=r"$x$", ylabel=r"$y$", zlabel=r"$z$", title=None, 
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
	f.scene.render_window.multi_samples = 8 # Try with 4 if you think this is slow

	for it in xrange(n_time_points):
		mlab.clf()

		source = mlab.pipeline.scalar_field(F[:,:,:,it])
		vol = mlab.pipeline.volume(source, vmin=vmin, vmax=vmax)

		mlab.scalarbar(title="")
		mlab.title(title + r"$t=%d$" % it, size=0.4, height=0.94)
		mlab.xlabel(xlabel)
		mlab.ylabel(ylabel)
		mlab.zlabel(zlabel)

		mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
				focalpoint=(N/2.0, N/2.0, N/2.0))

		fpath = os.path.join(frame_folder, "volume_t%02d.%s" % (it, file_type))
		mlab.savefig(fpath)
		if verbose:
			print "file created at %s" % fpath
	
	mlab.close()


def plot_points3d(F, observable, frame_folder, output_animation_folder, 
	file_type="png", vmin=None, vmax=None, cgif=True, cmovie=True, 
	camera_distance=1.0, xlabel=r"$x$", ylabel=r"$y$", zlabel=r"$z$", title=None, 
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

	mlab.figure(size=figsize)

	if not use_scale_factor:
		factor = 1
	else:
		factor = 100
	
	F *= factor
	const = 0.25 # Lower limit on spheres

	for it in xrange(n_time_points):
		mlab.clf()

		mlab.points3d(F[:,:,:,it], vmin=vmin*factor, vmax=vmax*factor, scale_factor=scale_factor, scale_mode="scalar")

		mlab.scalarbar(title="")
		mlab.title(title[observable] + ", t=%d" % it, size=0.4, height=0.94)
		mlab.xlabel(xlabel)
		mlab.ylabel(ylabel)
		mlab.zlabel(zlabel)

		if not use_scale_factor:
			scale_factor = 1.0
		else:
			scale_factor = (np.min(F[:,:,:,it]) - vmin) / (vmax - vmin) * (1 - const)  + const

		mlab.view(45, 70, distance=np.sqrt(N**3)*camera_distance,
				focalpoint=(N/2.0, N/2.0, N/2.0))

		fpath = os.path.join(self.frame_folder, "points3d_t%02d.%s" % (it, file_type))
		mlab.savefig(fpath)
		if verbose:
			print "file created at %s" % fpath

	mlab.close()

