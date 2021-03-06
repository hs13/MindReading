from get_run_on_server import get_run_on_server
import numpy as np
import pandas as pd
import os
import datetime
from get_spike_train_values_from_key import get_spike_train_values_from_key
from get_mean_sdf_from_spike_train import get_mean_sdf_from_spike_train
from get_latency_from_sdf_v11 import get_latency_from_sdf_v11
from get_latency_from_sdf_v12 import get_latency_from_sdf_v12
from get_latency_dataframe import get_latency_dataframe
from get_time_window_buffer import get_time_window_buffer
from get_prestimulus_time import get_prestimulus_time
from get_resource_path import get_resource_path
from get_latency_from_sdf_v2 import get_latency_from_sdf_v2
from get_frames_name import get_frames_name

if not get_run_on_server():
    from plot_raster_sdf import plot_raster_sdf

def get_experiment_latency_dataframe(data_set, multi_probe_filename, short_version=False, split_frames=False, stim_type='natural_scenes'):
    latency_dataframe = get_latency_dataframe()

    pre_stimulus_time = float(get_prestimulus_time())/1000
    probe_spikes = {}
    probe_spikes_images = {}
    probe_spikes_times = {}
    time_window_buffer = float(get_time_window_buffer())/1000
    for c_probe in np.unique(data_set.unit_df['probe']):
        probe_units = data_set.unit_df[data_set.unit_df['probe'] == c_probe]
        c_spikes = data_set.spike_times[c_probe]
        for unit_id, unit in probe_units.iterrows():
            unit_spike_train = c_spikes[unit['unit_id']]
            if data_set.stim_tables.has_key(stim_type):
                for ind, stim_row in data_set.stim_tables[stim_type].iterrows():
                    stimulus_train = unit_spike_train[(unit_spike_train > stim_row['start'] - pre_stimulus_time) & (unit_spike_train < stim_row['end'] + time_window_buffer)] - stim_row['start']
                    inner_char_sep = '__'
                    if split_frames:
                        train_id = multi_probe_filename + inner_char_sep + c_probe + inner_char_sep + \
                        unit['structure'] + inner_char_sep + unit['unit_id'] + inner_char_sep + str(unit['depth']) + inner_char_sep + str(int(stim_row[get_frames_name(stim_type)]))
                    else:
                        train_id = multi_probe_filename + inner_char_sep + c_probe + inner_char_sep + \
                        unit['structure'] + inner_char_sep + unit['unit_id'] + inner_char_sep + str(unit['depth'])
                    
                    if not probe_spikes.has_key(train_id):
                        probe_spikes[train_id] = []
                        probe_spikes_images[train_id] = []
                        probe_spikes_times[train_id] = []
                    probe_spikes[train_id].append(stimulus_train)
                    probe_spikes_images[train_id].append(int(stim_row[get_frames_name(stim_type)]))
                    probe_spikes_times[train_id].append(stim_row['start'])
        if short_version:
            break

    output_path = get_resource_path() + 'Latency_results/'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    c_output_path = output_path + str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")) + '/'
    if not os.path.exists(c_output_path):
        os.makedirs(c_output_path)

    for st_ind, spike_train_name in enumerate(probe_spikes.keys()):
        st_vals = get_spike_train_values_from_key(spike_train_name)
        # st_hist = get_hist_from_spike_train(st_vals)
        # hist_latency = get_latency_from_hist(st_hist)
        mean_sdf, spike_raster, all_sdfs = get_mean_sdf_from_spike_train(probe_spikes[spike_train_name])
        sdf_latency, response_type, pre_stim_dict = get_latency_from_sdf_v11(mean_sdf)
        sdf_latency2, response_type2, pre_stim_dict = get_latency_from_sdf_v12(all_sdfs)        
        # sdf_latency3, response_type3 = get_latency_from_sdf_v2(mean_sdf)
        st_vals['latency_psth'] = 0
        st_vals['latency_sdf'] = sdf_latency
        st_vals['response_type'] = response_type
        st_vals['latency_sdf_v2'] = sdf_latency2
        st_vals['response_type_v2'] = response_type2
        latency_dataframe.loc[st_ind] = st_vals

        if not get_run_on_server():
            fig_file_name = c_output_path + spike_train_name
            fig_path = fig_file_name + '_sdf.png'
            plot_raster_sdf(spike_train_name, probe_spikes[spike_train_name], probe_spikes_images[spike_train_name], mean_sdf, st_vals, pre_stim_dict, fig_path)

    return latency_dataframe