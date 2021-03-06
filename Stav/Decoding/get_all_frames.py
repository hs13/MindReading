import numpy as np

def get_all_frames(stim_type):
	if stim_type == 'natural_scenes':
		# return np.array(range(118)).astype(float)
		return np.array(range(1, 10)).astype(float)
	if stim_type == 'flash_250ms':
		return [1.]
	if stim_type == 'drifting_gratings':
		# return [0., 45., 90.]
		return [0., 45., 90., 135.] #  180.  225.  270.  315.
	if stim_type == 'static_gratings':
		# return [0., 45., 90.]
		return [0., 30., 60., 90.] #  120.  150.