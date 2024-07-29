#!/home/joy/Documents/tsn-project/venv/bin/python3
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
1. Place the tx and rx CSV files in /tmp/.
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
    csv_directory = "/tmp/tmpexpt/"
    # It also automatically includes the tx counterpart such as 'capture-experiment-tx1.csv'
    file_names = ['capture-experiment-rx1.csv', 'capture-experiment-rx2.csv']
    # Create a dictionary to hold dataframes
    df_dict = {}

    # Read each file (tx & rx) and create a dataframe
    for file_name in file_names:
        file_name_tx = file_name.replace('rx', 'tx')
        file_path = os.path.join(csv_directory, file_name)
        file_path_tx = os.path.join(csv_directory, file_name_tx)

        # Read the files into dataframes names df_tx1, df_tx2 etc.
        df_name_tx = "df_" + file_name_tx.split(".")[0].split("-")[2]
        df_name = "df_" + file_name.split(".")[0].split("-")[2]
        df_dict[df_name_tx] = pd.read_csv(file_path_tx)
        df_dict[df_name] = pd.read_csv(file_path)
        # Remove the last two rows
        df_dict[df_name_tx] = df_dict[df_name_tx].iloc[:-2]
        df_dict[df_name] = df_dict[df_name].iloc[:-2]

    return df_dict


def extract_statistics(df_dict):
    """
    Extracts statistics related to latency, jitter, packet loss, and out-of-order packets.
    Returns a dictionary containing the statistics.
    """
    stats_dict = {}

    # Iterate over each pair of dataframes
    for filename, df_tx in df_dict.items():
        # Get the corresponding rx dataframe
        filename_rx = filename.replace('tx', 'rx')
        df_rx = df_dict[filename_rx]

        # Merge the dataframes on 'iperf.id' and 'iperf.id2'
        df = pd.merge(df_tx, df_rx, on=['iperf.id', 'iperf.id2'], how='left')

        # Write txtime (in microseconds) using iperf.sec and .usec
        df['time_tx'] = df['iperf.sec_x'] * 1e6 + df['iperf.usec_x']

        # Calculate the latency (in microseconds)
        # rx capture - iperf tx
        df['latency'] = (df['frame.time_epoch_y'] - df['iperf.sec_x']) * 1e6 - df['iperf.usec_x']
        # rx capture - tx capture
        df['latency2'] = (df['frame.time_epoch_y'] - df['frame.time_epoch_x']) * 1e6

        # Rolling jitter - Calculate the rolling standard deviation (jitter) for the previous 20 rows
        df['jitter'] = df['latency'].rolling(window=20).std()

        # Also, extract number of lost packets and out-of-order packets
        # Calculate the difference between consecutive 'iperf.id' values
        diff_values = df['iperf.id'].diff()
        # Identify where the difference is greater than 1 (packet loss occurred)
        lost_packets = diff_values > 1
        # Calculate the cumulative sum of lost packets, subtracting 1 for the current packet
        df['lost'] = (diff_values - 1).where(lost_packets, 0).cumsum()

        # Detect out-of-order packets
        # Initialize the 'out-of-order' column with zeros
        df['out-of-order'] = 0
        # Identify where the 'iperf.id' value of the subsequent row is less than the current row
        out_of_order_conditions = diff_values < 0
        # Increment the 'out-of-order' column value by 1 each time the condition is met
        df['out-of-order'] = out_of_order_conditions.cumsum()

        # Store the stats values in the dictionary
        columns_to_keep = ['time_tx', 'frame.time_epoch_x', 'iperf.id', 'latency', 'jitter', 'lost', 'out-of-order']
        stats_dict[filename] = df[columns_to_keep]

    return stats_dict


def plot_statistics(df):
    """
    Generates plots using seaborn.
    Create a time-series line plot for latency, jitter, packet loss, and out-of-order count
    """
    # Set the plotting parameters
    plotting = 'Subplots'  # 'Subplots', 'Separate'
    sns.set_theme(style='whitegrid',
                  context='notebook',
                  font_scale=0.5,
                  rc={'figure.figsize': (16, 9)})
    # Define outlier properties for boxplots
    flierprops = dict(marker='o', markersize=1)
    bin_size = 20

    # Ensure the timestamp column is of datetime type and set as the index
    df['frame.time_epoch_x'] = pd.to_datetime(df['frame.time_epoch_x'], unit='s')
    # Normalize the timestamps to start from 0
    df['time_from_start(s)'] = (df['frame.time_epoch_x'] - df['frame.time_epoch_x'].iloc[0]).dt.total_seconds()
    df.set_index('time_from_start(s)', inplace=True)
    # df.set_index('iperf.id', inplace=True)

    # Define the columns you want to plot (excluding 'frame.time_epoch_x' and 'iperf.id')
    columns_to_plot = [column for column in df.columns if column not
                       in ['time_tx', 'frame.time_epoch_x', 'iperf.id', 'lost', 'out-of-order']]

    # Create a figure and a list of subplots
    fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6), sharex=True)
    # Plot each column on a separate subplot
    for i, column in enumerate(columns_to_plot):
        # Time-series plot
        sns.lineplot(ax=axes[i], data=df, x=df.index, y=column)
        axes[i].set_ylabel(column)
        axes[i].set_title(f'Time Series of {column}')

    # # Create a figure and a list of subplots
    # fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6))
    # # Plot each column on a separate subplot
    # for i, column in enumerate(columns_to_plot):
    #     # CDF plot
    #     # Create a figure and a list of subplots
    #     # fig, axes = plt.subplots(nrows=len(columns_to_plot), ncols=1, figsize=(10, 6))
    #     sns.ecdfplot(ax=axes[i], data=df, x=column, lw=2, stat='count', log_scale=(False, False))
    #     axes[i].set_title(f'CDF of {column}')

    # Important : Plot of received timestamp for these flows shows clear demarcation
    # sns.scatterplot(data=df, x='iperf.id', y= 'frame.time_epoch_y')  #, hue='Flows')

    # Adjust the layout
    plt.suptitle("Packet Flow Statistics", y=1.02)
    plt.tight_layout()


def main():
    # Read the files
    df_dict = read_csv_files()

    # Extract the statistics of each flow
    stats_dict = extract_statistics(df_dict)

    # Print the number of flows
    print(f"Number of flows: {len(df_dict)/2}")

    # Print the latency statistics for each flow
    # Pick the 1st, 3rd etc. items based on their order
    selected_keys = list(stats_dict)[::2]  # This will get every second key starting from the first
    selected_items = {key: stats_dict[key] for key in selected_keys}

    for file, stats_df in selected_items.items():
        print(f"======>Latency statistics for {file}:")
        # Also provides jitter (i.e. latency_values.std())
        print(stats_df['latency'].describe())

        # Plot (optional)
        plot_statistics(stats_df)
    plt.show()


if __name__ == "__main__":
    main()

