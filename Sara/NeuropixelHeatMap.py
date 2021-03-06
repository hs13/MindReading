# -*- coding: utf-8 -*-
"""
Heat map generation of neuropixel probe responses

Created on Fri Aug 24 22:17:38 2018

@author: sarap
"""

from __future__ import print_function
import numpy as np
import pandas as pd
import os
import sys
import matplotlib.pyplot as plt

# %% Settings
pre_time = 0.1
bin_width = 0.005
probe_spacing = 20  # Microns
bins = [x*bin_width for x in range(-20,51)]

# %% Run once to load in the data
drive_path = os.path.normpath('d:/visual_coding_neuropixels')
sys.path.append(os.path.normpath('d:/resources/swdb_2018_neuropixels/'))
from swdb_2018_neuropixels.ephys_nwb_adapter import NWB_adapter
manifest_file = os.path.join(drive_path,'ephys_manifest.csv')

# Create experiment dataframe
expt_info_df = pd.read_csv(manifest_file)
#make new dataframe by selecting only multi-probe experiments
multi_probe_expt_info = expt_info_df[expt_info_df.experiment_type == 'multi_probe']
multi_probe_example = 1 # index to row in multi_probe_expt_info
multi_probe_filename  = multi_probe_expt_info.iloc[multi_probe_example]['nwb_filename']

nwb_file = os.path.join(drive_path, multi_probe_filename)
print('Importing data file from {}'.format(nwb_file))
image_path = os.path.normpath('D:\\Images\\AvgOverImages\\' + multi_probe_filename[:-4])
print('Saving output to {}'.format(image_path))

data_set = NWB_adapter(nwb_file)

ns_table = data_set.get_stimulus_table('natural_scenes')

# %% Re-run each time you change the probe name
fig_name = 'Probe{}_AllNaturalImages'.format(probe_name[-1])
probe_spikes = data_set.spike_times[probe_name]
# Subset of dataframe corresponding to chosen probe
probe_df = data_set.unit_df[(data_set.unit_df['probe']==probe_name)]

all_counts = []  # List to hold the PSTHs of each electrode
for i, unit_row in probe_df.iterrows():
    spike_train = probe_spikes[unit_row['unit_id']]
    stim_train = []
    for image_id in np.unique(ns_table['frame']):
        frame_table = ns_table[ns_table.frame == image_id]
        for j, stim_row in frame_table.iterrows():
            current_train = spike_train[(spike_train > stim_row['start'] - pre_time) & (spike_train <= stim_row['end'])] - stim_row['start']
            stim_train.append(current_train)
    counts, edges = np.histogram(np.hstack(stim_train), bins=bins)
    all_counts.append(counts)
# Centers of each time bin
centers = edges[1:]-(edges[1]-edges[0])/2
# %% Make a copy of the probe dataframe 
analysis_df = probe_df.copy()
analysis_df['counts'] = all_counts

# Get a list of unique depths
depth_list = analysis_df['depth'].unique()
xdepth = np.arange(np.min(depth_list), 0, probe_spacing)

# Create the count matrix
count_matrix = np.zeros([len(xdepth), len(all_counts[0])])

for i, row in analysis_df.iterrows():
    count_matrix[np.where(xdepth == row['depth'])] = row['counts']

# %% New Heatmap
fig, ax = plt.subplots(1, 1, figsize=(10,20))
ax.imshow(count_matrix)
x_pts = np.shape(count_matrix)[1]
y_pts = np.shape(count_matrix)[0]
xfac = ax.get_xticks()/x_pts*350
xfac = xfac - 100
ax.set_xticklabels([str(np.round(x)) for x in xfac], fontsize=19)
yfac = ax.get_yticks()/y_pts*np.max(np.abs(xdepth))
ax.set_yticklabels([str(-np.round(y)) for y in yfac], fontsize=20)
ax.set_xlabel('Time (ms)', fontsize=30)
ax.vlines(np.where(centers == np.min(np.abs(centers))),ax.get_ylim()[1],ax.get_ylim()[0], 'white', alpha=0.6)
ax.set_ylabel('Depth (microns)', fontsize=30)
ax.set_title(fig_name, fontsize=30)
ax.set_title('ProbeE - all natural images', fontsize=30)
# %% Save the heatmap
fig.savefig(os.path.normpath('D:\\Images\\AvgOverImages\\' + fig_name + '_heatmap.png'))