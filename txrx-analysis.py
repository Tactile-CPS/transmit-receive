#!/usr/bin/env python
"""
Packet Flow Statistics Analyzer

Author        : Joydeep Pal
Date Created  : Nov-2022
Date Modified : May-2023, Nov-2023, 06-Dec-2023, 05-Jun-2024, Jul-2024

Description:
This script reads csv files containing packet dump data for unique flows.
Iperf sends packets with sequence numbers and timestamps.
Packets captured in both tx and rx, and converted to csv.
It extracts statistics related to latency, jitter, packet loss, and out-of-order packets.
The script then presents the statistics in numerical format and
generates plots using seaborn.
Flows can be ST and BE flows.

Usage:
1. Place the tx and rx CSV files in /tmp/tmpexp/.
2. Run the script
3. It infers the no_of_flows and proceeds accordingly.
"""

import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

file_date = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def read_csv_files():
    """
    Returns a list of dataframes
    """
    # List of required csv file names, modify according to number of flows
    csv_directory = "/tmp/tmpexp/"
    # It also automatically includes the tx counterpart such as 'expt-tx1.csv'
    file_names = ['expt-rx1.csv', 'expt-rx2.csv']
    # Create a dictionary to hold dataframes
    df_dict = {}

    # Read each file (tx & rx) and create a dataframe
    for file_name in file_names:
        file_name_tx = file_name.replace('rx', 'tx')
        file_path = os.path.join(csv_directory, file_name)
        file_path_tx = os.path.join(csv_directory, file_name_tx)

        # Read the files into dataframe names df_tx1, df_tx2 etc.
        df_name_tx = "df_" + file_name_tx.split(".")[0].split("-")[1]
        df_name = "df_" + file_name.split(".")[0].split("-")[1]
        df_dict[df_name_tx] = pd.read_csv(file_path_tx)
        df_dict[df_name] = pd.read_csv(file_path)
        # Remove the last two rows
        df_dict[df_name_tx] = df_dict[df_name_tx].iloc[:-2]  #[1000:51000]
        df_dict[df_name] = df_dict[df_name].iloc[:-2]

    return df_dict


def extract_statistics(df_dict):
    """
    Extracts statistics related to latency, jitter, packet loss, and out-of-order packets.
    Returns a dictionary containing the statistics.
    """
    stats_dict = {}

    # Iterate over each pair of dataframes
    # Pick the 1st, 3rd etc. items based on their order
    selected_keys = list(df_dict)[::2]  # This will get every second key starting from the first
    selected_items = {key: df_dict[key] for key in selected_keys}
    for filename, df_tx in selected_items.items():
        # Get the corresponding rx dataframe
        filename_rx = filename.replace('tx', 'rx')
        df_rx = df_dict[filename_rx]

        # Merge the dataframes on 'iperf.id' and 'iperf.id2'
        df = pd.merge(df_tx, df_rx, on=['iperf.id', 'iperf.id2'], how='right')

        # Write txtime (in microseconds) using frame.epoch tx time/iperf.sec and .usec
        df['time_tx'] = df['iperf.sec_x'] * 1e6 + df['iperf.usec_x']  #df['frame.time_epoch_x'] * 1e6

        # Calculate the latency (in microseconds)
        # rx capture - iperf tx
        df['latency2'] = (df['frame.time_epoch_y'] - df['iperf.sec_x']) * 1e6 - df['iperf.usec_x']
        # rx capture - tx capture
        df['latency'] = (df['frame.time_epoch_y'] - df['frame.time_epoch_x']) * 1e6

        # Rolling jitter - Calculate the rolling standard deviation (jitter) for the previous 20 rows
        df['jitter'] = df.sort_values(by='iperf.id')['latency'].rolling(window=20).std()

        # Also, extract number of lost packets
        # Calculate the difference between consecutive 'iperf.id' values
        diff_values = df.sort_values(by='iperf.id')['iperf.id'].diff()
        # Identify where the difference is greater than 1 (packet loss occurred)
        lost_packets = diff_values > 1
        # Calculate the cumulative sum of lost packets, subtracting 1 for the current packet
        df['lost'] = (diff_values - 1).where(lost_packets, 0).cumsum()

        # Detect out-of-order packets
        # Initialize the 'out-of-order' column with zeros
        df['out-of-order'] = 0
        # Calculate the difference between consecutive 'iperf.id' values
        diff_values = df['iperf.id'].diff()
        # Identify where the 'iperf.id' value of the subsequent row is less than the current row
        out_of_order_conditions = diff_values < 0
        # Increment the 'out-of-order' column value by 1 each time the condition is met
        df['out-of-order'] = out_of_order_conditions.cumsum()

        # Store the stats values in the dictionary
        columns_to_keep = ['time_tx', 'frame.time_epoch_x', 'iperf.id', 'latency', 'jitter', 'lost', 'out-of-order']
        stats_dict[filename] = df[columns_to_keep]

    return stats_dict


def plot_statistics(stats_dict):
    """
    Generates plots using seaborn.
    Create a time-series line plot for latency, jitter, packet loss, and out-of-order count
    """
    # Set the plotting parameters
    plotting = 'Subplots'  # 'Subplots', 'Separate'
    sns.set_theme(style='whitegrid',
                  context='notebook',
                  font_scale=1,
                  rc={'figure.figsize': (16, 9)})

    # Prepare data for plots
    for file, df in stats_dict.items():
        # Ensure the timestamp column is of datetime type and set as the index
        df['frame.time_epoch_x'] = pd.to_datetime(df['frame.time_epoch_x'], unit='s')
        # Normalize the timestamps to start from 0
        df['time_from_start(s)'] = (df['frame.time_epoch_x'] - df['frame.time_epoch_x'].iloc[0]).dt.total_seconds()
        df.set_index('time_from_start(s)', inplace=True)
        # df.set_index('iperf.id', inplace=True)

    # Define the columns you want to plot (excluding 'frame.time_epoch_x' and 'iperf.id')
    columns_to_plot = [column for column in stats_dict.get('df_tx1').columns if column not
                       in ['time_tx', 'frame.time_epoch_x', 'iperf.id', 'latency', 'jitter']]  #, 'lost', 'out-of-order']]

    ' Time-Series & CDF plot for each flow '
    for file, df in stats_dict.items():
        # Create a figure and a list of subplots
        fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6), sharex=True)
        # Plot each column on a separate subplot
        for i, column in enumerate(columns_to_plot):
            sns.scatterplot(ax=axes[i], data=df, x=df.index, y=column)
            axes[i].set_ylabel(column)
            axes[i].set_title(f'Time Series of {column}')

        # # CDF plot
        # # Create a figure and a list of subplots
        # fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6))
        # # Plot each column on a separate subplot
        # for i, column in enumerate(columns_to_plot):
        #     sns.ecdfplot(ax=axes[i], data=df, x=column, lw=2, stat='count', log_scale=(False, False))
        #     axes[i].set_title(f'CDF of {column}')
        #
        # # Adjust the layout
        # plt.suptitle("Packet Flow Statistics", y=1.02)
        # plt.tight_layout()

    ' CDF plot - side-by-side latency plot for 1 ST and 1 BE flow '
    # fig, axes = plt.subplots(1, 2, tight_layout=True)  # , sharex='col')
    # sns.ecdfplot(ax=axes[0], data=stats_dict.get('df_tx1'), x='latency', lw=7, stat='proportion', log_scale=(False, False))
    # sns.ecdfplot(ax=axes[1], data=stats_dict.get('df_tx2'), x='latency', lw=7, stat='proportion', log_scale=(False, False))
    # axes[0].set_ylabel('Latency CDF [ST]')
    # axes[1].set_ylabel('Latency CDF [BE]')
    # # ax.set_xlabel('Latency (ms)')
    # # ax.legend(loc='lower right')
    # fig.suptitle('Cumulative Distribution Function (CDF) of Latency')  #, y=1)

    ' All together - Time-Series & CDF for 1 ST and 1 BE flow '
    fig, axes = plt.subplots(3, 3)  # , sharex='col')
    # Latency Time-Series
    sns.scatterplot(ax=axes[0, 1], data=stats_dict.get('df_tx1'), x='time_from_start(s)', y='latency')
    sns.scatterplot(ax=axes[1, 1], data=stats_dict.get('df_tx2'), x='time_from_start(s)', y='latency')
    for i, (key, df) in enumerate(stats_dict.items()):
        sns.scatterplot(ax=axes[2, 1], data=df, x='time_from_start(s)', y='latency', legend=True)
                        # hue='Flows', style='Flows', size='Flows', palette='dark')
    axes[0, 1].set_title('Latency TimeSeries [ST]')
    axes[1, 1].set_title('Latency TimeSeries [BE}')
    axes[2, 1].set_title('Latency TimeSeries [ST, BE]')
    # Important : Plot of received timestamp for these flows shows clear demarcation
    # sns.scatterplot(data=df, x='iperf.id', y= 'frame.time_epoch')

    # Latency CDF
    sns.ecdfplot(ax=axes[0, 2], data=stats_dict.get('df_tx1'), x='latency', lw=7, stat='proportion', log_scale=(False, False))
    sns.ecdfplot(ax=axes[1, 2], data=stats_dict.get('df_tx2'), x='latency', lw=7, stat='proportion', log_scale=(False, False))
    for i, (key, df) in enumerate(stats_dict.items()):
        sns.ecdfplot(ax=axes[2, 2], data=df, x='latency', lw=7, stat='proportion', log_scale=(False, False), label=key)
    axes[0, 2].set_title('Latency CDF [ST]')
    axes[1, 2].set_title('Latency CDF [BE]')
    axes[2, 2].set_title('Latency CDF [ST, BE]')
    axes[2, 2].legend(loc='best')
    # sns.stripplot(x='Flows', y='Latency (ms)', data=Time_Data)

    # Latency Time-Series boxplot
    # Define outlier properties for boxplots
    flierprops = dict(marker='o', markersize=1)
    bin_size = 20
    # Binning the data and create another column which represents each time bin
    for file, df in stats_dict.items():
        df['Time'] = pd.cut(df.index, bins=bin_size, labels=False)
    sns.boxplot(ax=axes[0, 0], data=stats_dict.get('df_tx1'), x='Time', y='latency', showfliers=True, flierprops=flierprops, label='df_tx1')
    sns.boxplot(ax=axes[1, 0], data=stats_dict.get('df_tx2'), x='Time', y='latency', showfliers=True, flierprops=flierprops, label='df_tx2')
    for i, (key, df) in enumerate(stats_dict.items()):
        sns.boxplot(ax=axes[2, 0], data=df, x='Time', y='latency', showfliers=False, flierprops=flierprops, label=key)
    axes[0, 0].grid()
    axes[1, 0].grid()
    axes[2, 0].grid()
    # sns.despine()

    fig.suptitle('Latency vs Time - for Scheduled Traffic and Best Effort flows - [Scheduled Traffic (ST)]', y=1)
    plt.tight_layout()


def main():
    # Read the files
    df_dict = read_csv_files()

    # Extract the statistics of each flow
    stats_dict = extract_statistics(df_dict)

    # Print the number of flows
    print(f"Number of flows: {len(df_dict)/2}")

    # Latency statistics for each flow
    for file, stats_df in stats_dict.items():
        print(f"======>Latency statistics for {file}:")
        # Also provides jitter (i.e. latency_values.std())
        print(stats_df['latency'].describe())

    # Plots for flows
    plot_statistics(stats_dict)

    # plt.show()
    plt.show(block=True)
    # plt.close()


if __name__ == "__main__":
    main()
