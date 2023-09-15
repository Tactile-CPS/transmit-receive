#!/home/venv/bin/python3

# Date - 14 May 2023
# Author - Joydeep Pal
# Description - Analyse pcap-json-csv file which has raw packet data to find metadata
# at specific positions and analyse time difference of our two TSN switches.

import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

Plotting = "Subplots"  # "Separate"
flierprops = dict(marker='o', markersize=1)  # Define outlier properties of boxplots
sns.set_theme(style='white', context='poster',
              font_scale=1.2, rc={'figure.figsize': (16, 9)})

FileDate = datetime.datetime.now().strftime("%Y_%m_%d_%H")

# csv file has 5 rows of which only the 1st column is useful for us
df = pd.read_csv('~/Documents/tsn-project/data-pcap_csv/exp_rtt_packetdata_pcap_to_json.csv', names=('frame_raw', 'a', 'b', 'c', 'd'))
# Build index as another column for convenient handling of plotting functions
df['time_s'] = df.index
# Clean data
df['frame_raw'] = df['frame_raw'].str.replace("[", "", regex=True)

# Extract hex of your Metadata Header
df['sw2_ME_ts_counter_raw'] = df['frame_raw'].str[93:109]           # timestamp1
df['sw1_ME_ts_counter_raw'] = df['frame_raw'].str[125:141]          # timestamp3
df['sw1_ME_ts_counter_return_raw'] = df['frame_raw'].str[157:173]   # timestamp5
# Convert hex string to int
df['sw1_ME_ts_counter'] = df['sw1_ME_ts_counter_raw'].apply(lambda u: int(u, 16))
df['sw1_ME_ts_counter_return'] = df['sw1_ME_ts_counter_return_raw'].apply(lambda u: int(u, 16))
df['sw2_ME_ts_counter'] = df['sw2_ME_ts_counter_raw'].apply(lambda u: int(u, 16))

# Conversion from counter to timestamp (in nanoseconds) for 633 MHz ME freq
conv_value_ns = 16000/633
df['sw1_ME_ts'] = df['sw1_ME_ts_counter'] * conv_value_ns
df['sw1_ME_ts_return'] = df['sw1_ME_ts_counter_return'] * conv_value_ns
df['sw2_ME_ts'] = df['sw2_ME_ts_counter'] * conv_value_ns

# Converison variable for milliseconds
ns_to_us = 10**-3
ns_to_ms = 10**-6
ns_to_s = 10**-9
ms_to_s = 10**-3

# Difference between counter values
df['counter_sync_diff'] = df['sw2_ME_ts_counter'] - df['sw1_ME_ts_counter']
df['counter_RTT_diff_using_same_switch'] = df['sw1_ME_ts_counter_return'] - df['sw1_ME_ts_counter']
# Difference between timestamp values - Synchronisation error and Propagation delay with time
df['Sync_error_ns'] = df['sw2_ME_ts'] - df['sw1_ME_ts'] - (df['sw2_ME_ts'][0] - df['sw1_ME_ts'][0])
df['RTT_ns'] = df['sw1_ME_ts_return'] - df['sw1_ME_ts']

# Difference between consecutive switch ME timestamp values (sw1_ME_ts/sw2_ME_ts)
# values (i.e. variation of jitter of switch ME timestamps, with time)
df['jitter_sw1'] = df['sw1_ME_ts'].diff()
df['jitter_sw2'] = df['sw2_ME_ts'].diff()
df['jitter_sw1_normalized'] = df['jitter_sw1'] - 1/ns_to_s  # Converting 1s to nanoseconds
df['jitter_sw2_normalized'] = df['jitter_sw2'] - 1/ns_to_s

Sync_error_diff = df['Sync_error_ns'][len(df)-1] - df['Sync_error_ns'][0]
Switch1_duration = df['sw1_ME_ts'][len(df)-1] - df['sw1_ME_ts'][0]
Switch2_duration = df['sw2_ME_ts'][len(df)-1] - df['sw2_ME_ts'][0]
Switch1_return_duration = df['sw1_ME_ts_return'][len(df)-1] - df['sw1_ME_ts_return'][0]
print(' ')
print(f'Synchronisation error varies for {Sync_error_diff*ns_to_ms:.9f} ms over a time duration of {round(len(df)/3600)} hr')
print(f'Switch1 time difference between first and last value - {Switch1_duration*ns_to_s:.9f} s')
print(f"Switch2 time difference between first and last value - {Switch2_duration*ns_to_s:.9f} s")
print(f"Switch1 return packet's time difference              - {Switch1_return_duration*ns_to_s:.9f} s")

if Plotting == "Subplots":

    # fig, axes = plt.subplots(4, 1, sharex='col', tight_layout=True, figsize=(9, 5))
    # df['Sync_error_ms'] = df['Sync_error_ns']*ns_to_ms
    # df['jitter_sw1_normalized_us'] = df['jitter_sw1_normalized']*ns_to_us
    # df['jitter_sw2_normalized_us'] = df['jitter_sw2_normalized']*ns_to_us
    # df['Sync_error_ms_diff'] = df['Sync_error_ms'].diff()
    # sns.scatterplot(ax=axes[0], data=df, x='time_s', y='Sync_error_ms', s=20)  # palette='dark'
    # sns.scatterplot(ax=axes[1], data=df, x='time_s', y='RTT_ns', s=20)
    # sns.scatterplot(ax=axes[2], data=df, x='time_s', y='jitter_sw1_normalized_us', s=5)
    # sns.scatterplot(ax=axes[3], data=df, x='time_s', y='jitter_sw2_normalized_us', s=5)
    # axes[0].set(title='Synchronisation error (ms) vs time')
    # axes[1].set(title='RTT (ns) vs time', ylabel=None)
    # axes[2].set(title='Switch 1 - Jitter(us) vs time', ylabel=None)
    # axes[3].set(title='Switch 2 - Jitter(us) vs time', ylabel=None)
    # axes[0].grid()
    # axes[1].grid()
    # axes[2].grid()
    # axes[3].grid()

    ''' Used for plotting the graph on the P4TAS paper '''
    fig, axes = plt.subplots(3, 1, sharex='col', tight_layout=True, figsize=(9, 5))
    df['Sync_error_ms'] = df['Sync_error_ns']*ns_to_ms
    df['jitter_sw1_normalized_us'] = df['jitter_sw1_normalized']*ns_to_us
    df['jitter_sw2_normalized_us'] = df['jitter_sw2_normalized']*ns_to_us
    df['Sync_error_us_diff'] = df['Sync_error_ns'].diff()*ns_to_us
    df['RTT_us'] = df['RTT_ns']*ns_to_us
    sns.scatterplot(ax=axes[0], data=df, x='time_s', y='Sync_error_ms', s=10)  # palette='dark'
    sns.scatterplot(ax=axes[1], data=df, x='time_s', y='Sync_error_us_diff', s=15)  # palette='dark'
    sns.scatterplot(ax=axes[2], data=df, x='time_s', y='RTT_us', s=15)
    # sns.scatterplot(ax=axes[2], data=df, x='time_s', y='jitter_sw1_normalized_us', s=5)
    # sns.scatterplot(ax=axes[3], data=df, x='time_s', y='jitter_sw2_normalized_us', s=5)
    axes[0].set(title='(a) Synchronisation error (ms) vs time', ylabel=None)
    axes[1].set(title='(b) Synchronisation error difference (us) vs time', ylabel=None)
    axes[2].set(title='(c) RTT (us) vs time', ylabel=None)
    # axes[2].set(title='Switch 1 - Jitter(us) vs time', ylabel=None)
    # axes[3].set(title='Switch 2 - Jitter(us) vs time', ylabel=None)
    axes[0].grid()
    axes[1].grid()
    axes[2].grid()
    # axes[3].grid()

    plt.show()
