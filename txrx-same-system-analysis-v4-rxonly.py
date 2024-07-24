#!/home/joy/Documents/tsn-project/venv/bin/python3
"""
Packet Flow Statistics Analyzer

Author        : Joydeep Pal
Date Created  : Jul-2024

Description:
This script reads CSV files containing packet dump data for unique flows.
Iperf sends packets with sequence numbers and timestamps.
Packtets captured only in rx and converted to csv.
It extracts statistics related to latency, jitter, packet loss, and out-of-order packets.
The script then presents the statistics in numerical format and
generates plots using seaborn.

Flows can be ST and BE flows.

Usage:
1. Place the rx CSV files in /tmp/.
2. Run the script
3. It infers the no_of_flows and proceeds accordingly.
"""

import os
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set the plotting parameters
plotting = 'Subplots'  # 'Subplots', 'Separate'
sns.set_theme(style='whitegrid', context='notebook',
              font_scale=0.5, rc={'figure.figsize': (16, 9)})
# Define outlier properties of boxplots
flierprops = dict(marker='o', markersize=1)
bin_size = 20
file_date = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')


def read_csv_files():
    """
    Returns lists of dataframes
    """
    # List of required csv file names, modify according to number of flows
    csv_directory = "/tmp"
    file_names = ['capture-experiment-1-rx.csv', 'capture-experiment-2-rx.csv']
    # Create a dictionary to hold dataframes
    df_dict = {}

    # Read each file in the directory and create a dataframe
    for file_name in file_names:
        file_path = os.path.join(csv_directory, file_name)
        # Create dataframe name like df_rx1, df_rx2, etc.
        df_name = "df_" + file_name.split(".")[0].split("-")[2]
        df_dict[df_name] = pd.read_csv(file_path)
        # Remove the last two rows
        df_dict[df_name] = df_dict[df_name].iloc[:-2]

    return df_dict


def calculate_latency(df_dict):
    """
    Calculates latency for each packet of each flow (tx/rx pair).
    Returns a dict of list of latency values for each flow.
    """
    # Initialize a dictionary to hold latency values
    latency_dict = {}

    # Iterate over each pair of dataframes
    for file, df in df_dict.items():

        # Calculate the latency (in microseonds)
        # Latency = (seconds_rx - seconds_tx) * 1,000,000 + (microseconds_rx - microseconds_tx)
        # Only rx capture - iperf tx
        df['latency'] = (df['frame.time_epoch'] - df['iperf.sec']) * 1e6 - df['iperf.usec']

        # Store the latency values in the dictionary
        latency_dict[file] = df['latency']

        # Also, extract number of lost packets
        df['lost'] = float("nan")
        for i in range(1, len(df)):
            current_value = df.loc[i, "iperf.id"]
            prev_value = df.loc[i - 1, "iperf.id"]
            # Calculate the difference between current and previous values
            diff = current_value - prev_value

            # Update the lost column based on the difference
            if diff == 1:
                df.loc[i, "lost"] = df.loc[i - 1, "lost"]
            else:
                df.loc[i, "lost"] = df.loc[i - 1, "lost"] + diff - 1

        # Detect out-of-order packets
        #df['in_order'] = df['iperf.id'].diff() == 1
        #print(df['in_order'].value_counts())

    return latency_dict


def main():
    # Read the files
    df_dict = read_csv_files()

    # Calculate the latency
    latency_dict = calculate_latency(df_dict)

    # Print the number of flows
    print(f"Number of flows: {len(df_dict)}")

    # Print the latency statistics for each flow
    for file, latency in latency_dict.items():
        print(f"Latency statistics for {file}:")
	# Also provides jitter (i.e. latency_values.std())
        print(latency.describe())


if __name__ == "__main__":
    main()

