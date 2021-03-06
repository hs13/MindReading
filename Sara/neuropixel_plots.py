# -*- coding: utf-8 -*-
"""
Plotting functions for neuropixel probe data

Created on Sat Aug 25 09:08:57 2018

@author: sarap
"""
import os 
import sys 
import numpy as np
import matplotlib.pyplot as plt 
import seaborn as sns
sns.set_context('notebook', font_scale=1.4)

__all__ = ['probe_heatmap', 'image_raster', 'image_psth', 'plot_psth',
           'receptive_field_map', 'depth_latency_map', 'depth_latency_hist',
           'smooth_depth_latency', 'depth_latency_scatter', 'region_color', 'rgb2hex']


def probe_heatmap(psth_matrix, depth, edges, pre_time):
	"""
	Parameters
	----------
	psth_matrix : np.array
		Matrix of PSTHs ([number of neurons x time])

	depths : list/np.array
		electrode depths corresponding to the rows of psth_matrix

	edges : list/np.array
		time bin edges returned by np.histogram in seconds

    Returns
    -------
    fig, ax : matplotlib figure handles
    
    Notes
    -----
    The time axis will be converted to milliseconds
	"""
	fig, ax = plt.subplots(1, 1, figsize=(15,20))
	bin_centers = edges[:-1]-(edges[1]-edges[0])/2

	# Plot the firing rate heatmap
	plt.imshow(psth_matrix, cmap='jet', interpolation='gaussian')
	# Add the stimulus onset, if necessary
	if pre_time > 0:
		ax.vlines(np.where(bin_centers == np.min(np.abs(bin_centers))), ax.get_ylim()[1], ax.get_ylim()[0], 'white', alpha=0.4)

	x_pts, y_pts = np.shape(psth_matrix)
	# Correct the x-axis (and convert to milliseconds)
	xfac = 1e3*((ax.get_xticks()/x_pts*np.max(bin_centers))-pre_time)
	ax.set_xticklabels([str(int(np.round(x))) for x in xfac])

	# Correct the y-axis
	yfac = ax.get_yticks()/y_pts*np.max(np.abs(depth))
	ax.set_yticklabels([str(int(-np.round(y))) for y in yfac])

	# Plot labels
	ax.set_xlabel('Time (ms)', fontsize=20)
	ax.set_ylabel('Depth (microns)', fontsize=20)

	return fig, ax


def image_raster(img, unit_spikes, ax):
    """
    Plot the raster for an image and unit
    
    Parameters
    ----------
    img : stimulus table for 1 image
    unit_spikes : spike times for 1 unit
    ax : axis handle
    """
    
    #Default params
    if not ax:
        fig,ax = plt.subplots(1,1,figsize=(6,3))

    pre_time = .5
    post_time = .75

    all_trials = []
    # Get spike train for each trial and append to all_trials
    for i, start in enumerate(img.start):
        # Extract spikes around stim time
        spikes_each_trial = unit_spikes[
            (unit_spikes > start-pre_time) &
            (unit_spikes <= start+post_time)]
        # Subtract start time of stimulus presentation
        spikes_each_trial = spikes_each_trial - start
        
        # Add spikes to the main list
        all_trials.append(list(spikes_each_trial))

    # Plot raster for each trial
    for i, tr_spikes in enumerate(all_trials):
        ax.plot(tr_spikes, i*np.ones_like(tr_spikes), '|', color='b')
        ax.invert_yaxis()      
    
    return ax


def plot_psth(psth, centers, ax=[]):
    """
    Plot a PSTH
    
    Parameters
    ----------
    psth : array_like
        Post-stimulus time histogram
    centers : array_like
        Bin centers
    ax : optional, matplotlib axis handle
    """
    if not ax:
        fig, ax = plt.subplots(1,1,figsize=(6,3))
    
    plt.plot(centers, psth)
    
    if np.min(centers) < 0:
        ax.axvspan(np.min(centers), 0, color='gray', alpha=0.2)
    ax.set_ylabel('Firing rate (Hz)', fontsize=16)
    ax.set_xlabel('Time (s)', fontsize=16)
    ax.set_xlim([np.min(centers), np.max(centers)])
    plt.show()
    
    return fig, ax


def receptive_field_map(rf_map, cmap=[]):
    """
    Map a single xy receptive field or a series of receptive fields
    
    Parameters
    ----------
    rf_map : np.array (x,y) or (t,x,y)
        Receptive field(s) 
    cmap : optional
        Colormap for figure
    
    Returns
    -------
    fig, ax : matplotlib handles
    """
    if not cmap:
        cmap = sns.cubehelix_palette(8, as_cmap=True)
        
    if rf_map.ndim == 2:
        fig, ax = plt.subplots(1, 1, figsize=(4, 4))
        sns.heatmap(rf_map, ax=ax, cmap=cmap, square=True, cbar=False, xticklabels=False, yticklabels=False)    
    elif rf_map.ndim > 2:
        fig, ax = plt.subplots(1, rf_map.shape[0], figsize=(12, 4))
        ax = ax.flatten()
        for i in range(rf_map.shape[0]):
            sns.heatmap(rf_map[i,:,:], ax=ax[i], square=True, cbar=False, xticklabels=False, yticklabels=False, cmap=cmap)
    
    return fig, ax


def image_psth(img, unit_spikes, ax=[]):
    """
    Parameters
    ----------
    img : stimulus table for one image
    unit_spikes : spike times for 1 unit
    ax : handle of matplotlib axes object
    
    Returns
    -------
    fig, ax : matplotlib object handles
    """
    
    #Default params
    if not ax:
        fig,ax = plt.subplots(1,1,figsize=(6,3))

    pre_time = 1.
    post_time = 1.

    all_trials = []
    # Get spike train for each trial
    for i, start in enumerate(img.start):
        trial_spikes = unit_spikes[(unit_spikes > start-pre_time) & (unit_spikes < start+post_time)]
        trial_spikes = trial_spikes - start
        all_trials.append(list(trial_spikes))

    # Make PSTH for each trial with 5 ms bins
    bin_width = 0.005  # 5 ms  
    bins = np.arange(-pre_time,post_time+bin_width,bin_width)
    fr_per_trial = []
    for trial_spikes in all_trials:
        counts, edges = np.histogram(trial_spikes, bins)
        counts = counts/bin_width
        fr_per_trial.append(counts)
    centers = edges[:-1] + np.diff(bins)/2
    
    mean_fr = np.mean(fr_per_trial, axis=0)
    
    # Plot mean PSTH across trials
    fig, ax = plt.subplots(1,1)
    plt.plot(centers, mean_fr)
    
    ax.axvspan(0,0.25,color='gray',alpha=0.1)
    ax.set_ylabel('Firing rate (spikes/second)')
    ax.set_xlabel('Time (s)')
    plt.show()   

    return fig, ax


def depth_latency_hist(depth_df, bins=10, save_path=[]):
    """
    Parameters
    ----------
    depth_df : dataframe
        DataFrame from latency analysis
    bins : optional, integer
        Number of bins for histogram (default = 10)        
    save_path : optional, str
        If provided, figure will be saved as .png  
    
    Returns
    -------
    fig, ax : matplotlib handles
    """

    counts, edges = np.histogram(depth_df['depth'], bins=bins)
    plt.plot(edges[:-1], counts)

    latency_mean = np.zeros_like(counts)
    latency_median = np.zeros_like(counts)
    latency_std = np.zeros_like(counts)
    
    depths = depth_df['depth'].values
    latencies = depth_df['latency'].values
    # Remove the NaNs
    depths = depths[depth_df['latency'].notna()]
    latencies = latencies[depth_df['latency'].notna()]

    for i in range(len(edges)-1):
        ind = np.where((depths >= edges[i]) & (depths < edges[i+1]))
        latency_mean[i] = np.mean(latencies[ind])
        latency_median[i] = np.median(latencies[ind])
        latency_std[i] = np.std(latencies[ind])
    latency_sem = latency_std/len(latency_std)
    
    fig, ax = plt.subplots()
    # Scatter plot of individual points
    ax.plot(depths, latencies, marker='o', linestyle='none', color='k', alpha=0.2)
    # Mean latency with errorbars
    ax.errorbar(edges[:-1], latency_mean, yerr=latency_std, marker='o', label='mean')
    # Median latency
    ax.plot(edges[:-1], latency_median, marker='o', label='median')
    ax.set_ylabel('Latency (ms)')
    ax.set_xlabel('Depth (um)')
    if save_path is not None:
        fig.savefig(save_path)
    
    return fig, ax


def depth_latency_map(depth_df, save_path):
    """
    Parameters
    ----------
    depth_df : dataframe
        DataFrame from latency analysis
    save_path : optional, str
        If provided, figure will be saved as .png
    
    Returns
    -------
    g : seaborn.axisgrid.JointGrid
    """
    g = sns.jointplot(depth_df['latency'], depth_df['depth']*1e-3, kind='kde', space=0, stat_func=None, color=region_color(region))
    g.plot_marginals(sns.rugplot, height=0.12, color="k")
    g.set_axis_labels(xlabel='{} latency (ms)'.format(region), ylabel='{} depth (mm) '.format(region))
    if save_path is not None:
        g.savefig(save_path)
    return g


def smooth_depth_latency(depth_df, show_data=False, ax=[], sg_window=5, sg_order=2, sg_bins=20, use_median=False):
    """
    Parameters
    ----------
    depth_df : pandas.DataFrame
        LatencyAnalysis dataframe with 'depth' and 'latency'
    sg_window : optional, int
        Points for Savitsky-Golay window (default = 5)
    sg_order : optional, int
        Polynomial for Savitsky-Golay window (default = 2)
    sg_bins : optional, int
        Number of bins to divide data (default = 20)
    show_data : optional, bool
        Plot the raw data as well (default = False)
    use_median : optional, bool
        Use median instead of mean (default = False)
    ax : optional, matplotlib axes handle
        Axis to plot to (default = new)
    
    Returns
    -------
    fig, ax : matplotlib figure handles
    """
    
    if not ax:
        fig, ax = plt.subplots()
    else:
        fig = []
    
    # Clip out the NaNs
    depths = depth_df['depth'].values
    latencies = depth_df['latency'].values
    depths = depths[depth_df['latency'].notna()]
    latencies = latencies[depth_df['latency'].notna()]
    
    # not_nan = depth_df['latency'].notna()
    # Need at least as many data points as window for Savitsky-Golay smooth
    if len(np.where(latencies.values == True)[0]) < sg_window:
        print('Skipping smooth curve plot for {}'.format(region))
        return
    # Upsampled histogram
    counts, edges = np.histogram(depth_df['depth'], bins=sg_bins)
    # Get the mean latency for each bin
    latency_mean = np.zeros_like(counts)
    latency_median = np.zeros_like(counts)
    for i in range(len(edges)-1):
        ind = np.where((depths >= edges[i]) & (depths < edges[i+1]))
        latency_mean[i] = np.mean(latencies[ind])
        latency_median[i] = np.median(latencies[ind])
    bin_centers = edges[:-1] - (edges[1]-edges[0])/2

    # Get indices of empty bins
    ind = np.where(latency_mean > 2)
    if len(ind[0]) < sg_window:
        print('Skipping smooth curve plot for {}'.format(region))
        return
    print('{}-{} bin size = {} ms'.format(expt_index, region, (np.max(edges)-np.min(edges))/sg_bins))
    
    # Smooth curve plot    
    fig, ax = plt.subplots()
    ax.plot(bin_centers[ind], scipy.signal.savgol_filter(latency_mean[ind], sg_window, sg_order), linewidth=3)
    # Plot raw data points
    ax.plot(depths, latencies, marker='o', linestyle='none', alpha=0.2, color='k')
    ax.set_ylim(0,)
    ax.set_title('{} - Natural Scenes ({})'.format(region, expt_index))
    ax.set_xlabel('Depth (um)')
    ax.set_ylabel('Latency (ms)')
    fig.savefig(spath + '_smooth.png')
    
    return fig, ax
    

def region_cmap(region_name, rot=0.1, plotme=False):
    """
    Parameters
    ----------
    region_name : str
        Region abbreviation (VISp, TH, SCs, DG, etc)
    rot : float
    plotme : optional, bool
        plot colormap, default = false
    
    Returns
    -------
    cmap : seaborn colormap
    """
    
    starts = np.linspace(0.2, 2.8, 10)
    regions = ('VISam', 'VISpm', 'TH', 'SCs', 'DG', 'CA', 'VISp', 'VISl', 'VISal', 'VISrl')
    try:
        ind = regions.index(region_name)
        ind = starts[ind]
    except ValueError:
        print('Invalid Region {}. Accepted regions: '.format(region_name))
        print(regions)
        return
        
    cmap = sns.cubehelix_palette(start=ind, rot=rot, as_cmap=True)
    
    if plotme:
        sns.palplot(sns.cubehelix_palette(start=ind, rot=rot))
    
    return cmap


def region_color(region_name, light=False, sat=[]):
    """
    Parameters
    ----------
    region_name : str
        Structure recorded from
    light : optional, bool
        Return lightest color of map (default = False)
    sat : optional, float
        Percent to desaturate output color (default = 0)
        
    Returns
    -------
    Hex color value for plotting
    """
    cmap = region_cmap(region_name)
    
    if light:
        c = rgb2hex(cmap.colors[0])
    else:
        c = rgb2hex(cmap.colors[-1])
    
    if sat:
        c = sns.desaturate(c, sat)
    
    return c


def stim_color(stim_name, desat=[], ind=[]):
    """
    Parameters
    ----------
    stim_name : str
        Stimulus name (drifting_gratings, static_gratings, natural_scenes)
    desat : optional, float
        Percent to desaturate colors by (default = 0)
    ind : optional, integer
        Choose just one of the color palette (default = [], returns all )
    """
    
    if stim_name is 'natural_scenes':
        cmap = sns.light_palette((260, 75, 60), input="husl")
    elif stim_name is 'static_gratings':
        cmap = sns.light_palette('seagreen')
    else:
        print('Unrecognized stimulus: {}'.format(stim_name))
        return 
    
    if desat:
        cmap = sns.desaturate(cmap, desat)
        
    if not ind:
        return cmap
    else:
        return cmap[ind]


def rgb2hex(rgb):
    """
    Convert an RGB value to hex
    
    Parameters
    ----------
    rgb : array_like
        Red, green, blue 
    """
    r = rgb[0]
    g = rgb[1]
    b = rgb[2]
    
    if r+g+b < 3:
        r = int(r*255)
        g = int(g*255)
        b = int(b*255)
    hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return hex

