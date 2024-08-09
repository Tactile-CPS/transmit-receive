#!/home/joy/.virtualenvs/venv/bin/python3
"""
Packet Flow Statistics Analyzer

Author        : Joydeep Pal
Date Created  : Jul-2024

Description:
This script reads csv files containing packet dump data for unique flows.
Iperf sends packets with sequence numbers and timestamps.
Packets captured in rx, and converted to csv.
It extracts statistics related to latency, jitter, packet loss, and out-of-order packets.
The script then presents the statistics in numerical format and
generates plots using seaborn.
Flows can be ST and BE flows.

Usage:
1. Place the rx CSV files in /tmp/tmpexp/.
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
    file_names = ['capture-experiment-rx1.csv', 'capture-experiment-rx2.csv']
    # Create a dictionary to hold dataframes
    df_dict = {}

    # Read each file and create a dataframe
    for file_name in file_names:
        file_path = os.path.join(csv_directory, file_name)

        # Create dataframe name like df_rx1, df_rx2, etc.
        df_name = "df_" + file_name.split(".")[0].split("-")[2]
        df_dict[df_name] = pd.read_csv(file_path)
        # Remove the last two rows
        df_dict[df_name] = df_dict[df_name].iloc[:-2]

    return df_dict


def extract_statistics(df_dict):
    """
    Extracts statistics related to latency, jitter, packet loss, and out-of-order packets.
    Returns a dictionary containing the statistics.
    """
    stats_dict = {}

    # Iterate over each pair of dataframes
    for filename, df in df_dict.items():

        # Write txtime (in microseconds) using iperf.sec and .usec
        df['time_tx'] = df['iperf.sec'] * 1e6 + df['iperf.usec']

        # Calculate the latency (in microseconds)
        # rx capture - iperf tx
        df['latency'] = (df['frame.time_epoch'] - df['iperf.sec']) * 1e6 - df['iperf.usec']

        # Rolling jitter - Calculate the rolling standard deviation (jitter) for the previous 20 rows
        df['jitter'] = df['latency'].rolling(window=20).std()

        # Also, extract number of lost packets and out-of-order packets
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
        columns_to_keep = ['time_tx', 'frame.time_epoch', 'iperf.id', 'latency', 'jitter', 'lost', 'out-of-order']
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
                       in ['time_tx', 'frame.time_epoch_x', 'iperf.id']] #, 'lost', 'out-of-order']]

    ' Time-Series & CDF plot for each flow '
    # for file, df in stats_dict.items():
    #     # Create a figure and a list of subplots
    #     fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6), sharex=True)
    #     # Plot each column on a separate subplot
    #     for i, column in enumerate(columns_to_plot):
    #         sns.lineplot(ax=axes[i], data=df, x=df.index, y=column)
    #         axes[i].set_ylabel(column)
    #         axes[i].set_title(f'Time Series of {column}')
    #
    #     # CDF plot
    #     # # Create a figure and a list of subplots
    #     # fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6))
    #     # # Plot each column on a separate subplot
    #     # for i, column in enumerate(columns_to_plot):
    #     #     sns.ecdfplot(ax=axes[i], data=df, x=column, lw=2, stat='count', log_scale=(False, False))
    #     #     axes[i].set_title(f'CDF of {column}')
    #
    #     # Adjust the layout
    #     plt.suptitle("Packet Flow Statistics", y=1.02)
    #     plt.tight_layout()

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

    # Adjust the layout
    plt.suptitle("Packet Flow Statistics", y=1.02)
    plt.tight_layout()


def main():
    # Read the files
    df_dict = read_csv_files()

    # Extract the statistics of each flow
    stats_dict = extract_statistics(df_dict)

    # Print the number of flows
    print(f"Number of flows: {len(df_dict)}")

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
