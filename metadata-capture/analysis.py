#!/home/joy/Documents/venv/bin/python3

# Date          : 14-May-2023
# Author        : Joydeep Pal and Kanishak Vaidya
# Description   : Analyse pcap-json-csv file which has raw packet data to find metadata
# at specific positions and analyse time difference of our two TSN switches.

import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

Plotting = "Subplots"  # "Separate"
flierprops = dict(marker='o', markersize=1)  # Define outlier properties of boxplots
sns.set_theme(style='white', context='poster',
              font_scale=1, rc={'figure.figsize': (16, 9)})

FileDate = datetime.datetime.now().strftime("%Y_%m_%d_%H")

csv_path = Path.home().joinpath(r"/media/joy/TeraByte/tsn-project-backup/Results/nfp-tests/time-sync/clock-drift/6hrs")
csv_path = csv_path.joinpath("txrx-metadata-rtt-1hrs.csv")
# csv_path = Path.home().joinpath(r"Documents/tsn-project/data-pcap-csv/csv-temp/")
# csv_path = csv_path.joinpath("txrx-metadata-rtt-6hrs.csv")
df = pd.read_csv(csv_path, names=('timestamp', 'frame_raw'))
df = df.applymap(lambda x: x.replace("[", ""))
df = df.applymap(lambda x: x.replace("]", ""))
df = df.applymap(lambda x: x.replace(":", ""))
# df['timestamp'] = df.str.replace("[", "", regex=True)
df = df[df.timestamp != 'null'].reset_index()
del df['index']

df['PacketSeq'] = df['frame_raw'].apply(lambda x: bytes.fromhex(x[182:206]).decode('utf-8'))
df['PacketSeq'] = df['PacketSeq'].apply(lambda x: int(x, 10))

''' Clean Data '''
# Create a new column for distinguishing the rows within each idx group
df['row_number'] = df.groupby('PacketSeq').cumcount()

# Pivot the DataFrame to the desired format
pivot_df = df.pivot(index='PacketSeq', columns='row_number')

# Flatten the MultiIndex columns and reset index
pivot_df.columns = ['timestamp1', 'timestamp2', 'frame_raw1', 'frame_raw2']
pivot_df.reset_index(inplace=True)

pivot_df['timestamp1'] = pivot_df['timestamp1'].apply(lambda x: x.replace("'", "").replace('"', ''))
pivot_df['timestamp2'] = pivot_df['timestamp2'].apply(lambda x: x.replace("'", "").replace('"', ''))
pivot_df['timestamp1'] = pivot_df['timestamp1'].apply(lambda u: float(u))
pivot_df['timestamp2'] = pivot_df['timestamp2'].apply(lambda u: float(u))

df = pivot_df.copy()
del pivot_df
''' Clean Data '''

# Extract hex of your Metadata Header
df['ts1'] = df['frame_raw2'].str[0:16]
df['ts2'] = df['frame_raw2'].str[16:32]
df['ts3'] = df['frame_raw2'].str[32:48]
df['ts4'] = df['frame_raw2'].str[48:64]
df['ts5'] = df['frame_raw2'].str[64:80]
df['ts6'] = df['frame_raw2'].str[80:96]

# Conversion from counter's hex string format to timestamp (in nanoseconds)
# for 633 MHz ME freq
conv_value_ns = 16000 / 633
df['ts1'] = df['ts1'].apply(lambda u: int(u, 16)) * conv_value_ns
df['ts2'] = df['ts2'].apply(lambda u: int(u, 16)) * conv_value_ns
df['ts3'] = df['ts3'].apply(lambda u: int(u, 16)) * conv_value_ns
df['ts4'] = df['ts4'].apply(lambda u: int(u, 16)) * conv_value_ns
df['ts5'] = df['ts5'].apply(lambda u: int(u, 16)) * conv_value_ns
df['ts6'] = df['ts6'].apply(lambda u: int(u, 16)) * conv_value_ns

# Normalize all timestamps to their system's first timestamp value
# For example, All NFP#1's timestamps (ts1, ts2, ts3, ts4)
# are normalized to ts1's first value
df['timestamp2'] = df['timestamp2'].sub(df['timestamp1'][0])

df['ts2'] = df['ts2'].sub(df['ts1'][0])
df['ts5'] = df['ts5'].sub(df['ts1'][0])
df['ts6'] = df['ts6'].sub(df['ts1'][0])
df['ts4'] = df['ts4'].sub(df['ts3'][0])

df['ts1'] = df['ts1'].sub(df['ts1'][0])
df['ts3'] = df['ts3'].sub(df['ts3'][0])

df['timestamp1'] = df['timestamp1'].sub(df['timestamp1'][0])
# Converting all timestamps to nanoseconds
df['timestamp1'] = df['timestamp1'] * (10 ** 9)
df['timestamp2'] = df['timestamp2'] * (10 ** 9)

# Converison variable for milliseconds
ns_to_us = 10 ** -3
ns_to_ms = 10 ** -6
ns_to_s = 10 ** -9
ms_to_s = 10 ** -3

# Difference between timestamp values
df['rtt'] = df['timestamp2'] - df['timestamp1']
df['rtt1'] = df['ts5'] - df['ts2']
df['rtt2'] = df['ts6'] - df['ts1']
df['processing_delay_1'] = df['ts2'] - df['ts1']
df['processing_delay_2'] = df['ts4'] - df['ts3']
df['processing_delay_3'] = df['ts6'] - df['ts5']
df['sync_error'] = df['ts1'] - df['timestamp1']
df['sync_error1'] = df['ts3'] - df['ts2']
df['sync_error2'] = df['ts5'] - df['ts4']

df['sync_error_drift'] = df['sync_error'].diff() / (df['timestamp1'].diff() / (10 ** 9))
df['sync_error_drift1'] = df['sync_error1'].diff() / (df['timestamp1'].diff() / (10 ** 9))
df['sync_error_drift2'] = df['sync_error2'].diff() / (df['timestamp1'].diff() / (10 ** 9))

# Jitter
df['jitter_tx'] = df['timestamp1'].diff() / (10 ** 6)  # Tx system jitter (in s)
df['jitter_sw1'] = (df['ts1'].diff() - df['timestamp1'].diff())
df['jitter_sw2'] = (df['ts3'].diff() - df['ts1'].diff())

# Old calculation of jitter
# Difference between consecutive switch ME timestamp values (sw1_ME_ts/sw2_ME_ts)
# values (i.e. variation of jitter of switch ME timestamps, with time)
# df['jitter_sw1'] = df['sw1_ME_ts'].diff()
# df['jitter_sw2'] = df['sw2_ME_ts'].diff()

# Total durations
txPC_duration = df['timestamp1'][len(df) - 1] - df['timestamp1'][0]
nfp_sw1_duration = df['ts1'][len(df) - 1] - df['ts1'][0]
nfp_sw2_duration = df['ts3'][len(df) - 1] - df['ts3'][0]
print(f'Samples taken for a duration of '
      f'{txPC_duration} ns (TxPC), '
      f'{nfp_sw1_duration} ns (NFP#1), '
      f'{nfp_sw2_duration} ns (NFP#2)')
txPC_duration = (txPC_duration * (10 ** -9)) / 3600
nfp_sw1_duration = (nfp_sw1_duration * (10 ** -9)) / 3600
nfp_sw2_duration = (nfp_sw2_duration * (10 ** -9)) / 3600
sync_error1_range = df['sync_error1'][len(df) - 1] - df['sync_error1'][0]
sync_error2_range = df['sync_error2'][len(df) - 1] - df['sync_error2'][0]
print(' ')
print(f'Synchronisation (one-way) error varies for '
      f'{sync_error1_range} ns over a time duration of '
      f'{round(txPC_duration, 2)} hrs')
print(f'Synchronisation (other-way) error varies for '
      f'{sync_error2_range} ns over a time duration of '
      f'{round(txPC_duration, 2)} hrs')

summary = df.describe()
print(summary[df.columns[11:26]])

if Plotting == "Subplots":

    ''' Used for plotting the graph on the P4TAS paper '''
    fig, axes = plt.subplots(2, 2)  # figsize=(9, 5)), sharex='col'

    df['rtt1'] = df['rtt1'] * ns_to_us
    df['rtt2'] = df['rtt2'] * ns_to_us
    sns.histplot(ax=axes[0, 0], data=df, x='rtt1')
    sns.histplot(ax=axes[0, 0], data=df, x='rtt2')
    axes[0, 0].grid()
    axes[0, 0].set(title='(a) RTT of inner and outer timestamps(us)', xlabel=None)

    df['sync_error_drift'] = df['sync_error_drift'] * ns_to_ms
    df['sync_error_drift1'] = df['sync_error_drift1'] * ns_to_us
    df['sync_error_drift2'] = df['sync_error_drift2'] * ns_to_us
    # sns.scatterplot(ax=axes[0, 1], data=df, x='timestamp1', y='sync_error_drift', s=10)  # palette='dark'
    sns.histplot(ax=axes[0, 1], data=df, x='sync_error_drift')
    sns.histplot(ax=axes[1, 0], data=df, x='sync_error_drift1')
    sns.histplot(ax=axes[1, 1], data=df, x='sync_error_drift2')
    axes[0, 1].set(title='(b) Clock Drift(ms) b/w NFP#1 and source', xlabel=None)
    axes[1, 0].set(title='(c) Clock Drift(us) b/w NFP#2 and NFP#1', xlabel=None)
    axes[1, 1].set(title='(d) Clock Drift(us) b/w NFP#1 and NFP#2', xlabel=None)
    axes[0, 1].grid()
    axes[1, 0].grid()
    axes[1, 1].grid()
    # sns.scatterplot(ax=axes[0], data=df, x='timestamp1', y='Sync_error_ms', s=10)  # palette='dark'
    # axes[3].set(title='Switch 2 - Jitter(us) vs time', ylabel=None)

    plt.tight_layout()
    plt.show()
