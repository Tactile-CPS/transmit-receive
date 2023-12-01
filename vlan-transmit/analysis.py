#!/opt/venv/bin/python3

# Description   : Plots latency for ST snd BE flows
# Author        : Joydeep Pal
# Date          : Nov-2022
# Date Modified : May-2023, Nov-2023

import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

Plotting = "Subplots"  # "Subplots", "Separate"
flierprops = dict(marker='o', markersize=1)  # Define outlier properties of boxplots
sns.set_theme(style='whitegrid', context='notebook',
              font_scale=0.5, rc={'figure.figsize': (16, 9)})

BinSize = 20
FileDate = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

dftx = pd.read_csv("/tmp/TXv1.csv")
dfrx = pd.read_csv("/tmp/RXv1.csv")
dftx.rename(columns={"vlan.id": "Flows", 'frame.time_epoch': 'Epoch Time (Tx)'}, inplace=True)
dfrx.rename(columns={"vlan.id": "Flows", 'frame.time_epoch': 'Epoch Time (Rx)'}, inplace=True)
dftx['Flows'].replace({2: 'ST', 3: 'BE', 4: 'ST2'}, inplace=True)
dfrx['Flows'].replace({2: 'ST', 3: 'BE', 4: 'ST2'}, inplace=True)
TxCountTotal = dftx['Flows'].count()
RxCountTotal = dfrx['Flows'].count()

''' To remove few datapoints'''
# Time_Data = Time_Data.iloc[40:]


def summary_to_csv():
    TestMetadata = pd.DataFrame()

    # bandwidth = []
    if len(sys.argv) > 1:
        bandwidth = [sys.argv[1], sys.argv[2]]
        duration = sys.argv[3]
    else:
        bandwidth = ['Trial', 'Trial']
        duration = 'Trial'

    TestMetadata['bandwidth'] = {'ST': bandwidth[0], 'BE': bandwidth[1], 'ST2': bandwidth[0]}
    TestMetadata['Timestamp'] = FileDate
    TestMetadata['Duration'] = duration

    TestMetadata['TxCountOfEachFlow'] = dftx['Flows'].fillna('Others').value_counts()
    # TxCountOfEachFlow = dftx['Flows'].value_counts(dropna=False)
    RxCountOfEachFlow = dfrx['Flows'].fillna('Others').value_counts()
    TestMetadata['RxCountOfEachFlow'] = RxCountOfEachFlow
    TestMetadata['TxCountTotal'] = TxCountTotal
    TestMetadata['RxCountTotal'] = RxCountTotal
    TestMetadata['bandwidth'] = {'ST': bandwidth[0], 'BE': bandwidth[1]}
    TestMetadata['Timestamp'] = FileDate
    TestMetadata['Duration'] = duration

    # Count of relevant data only
    TestMetadata['TxPacketCount'] = Time_Data['Flows'].value_counts()
    TestMetadata['RxPacketCount'] = Time_Data[~Time_Data["Epoch Time (Rx)"].isnull()]['Flows'].value_counts()
    TestMetadata['PacketLoss'] = TestMetadata['TxPacketCount'] - TestMetadata['RxPacketCount']
    TestMetadata['PacketLoss%'] = (TestMetadata['PacketLoss'] * 100 / TestMetadata['TxPacketCount']).round(2)
    TestMetadata['LatencyMin'] = (Time_Data.groupby(['Flows']).min()['Latency (ms)']).round(2)
    TestMetadata['LatencyMax'] = (Time_Data.groupby(['Flows']).max()['Latency (ms)']).round(2)

    ''' Write data analysis numbers for this test to csv '''
    TestMetadata.to_csv('/home/zenlab/Documents/tsn-project/Results/Experimental.csv', mode='a')


# Clean data to keep only our data and remove arp, dns and other irrelevant data
dftx = dftx[~dftx['Flows'].isnull()]
dfrx = dfrx[~dfrx['Flows'].isnull()]
# dfrx = dfrx.loc[dfrx['Flows'].isin([3001, 3002])]

# Merge Tx and Rx data to one dataframe
Time_Data = pd.merge(dftx, dfrx[['ip.src', 'ip.id', 'Flows', 'Epoch Time (Rx)']],
                     on=['ip.src', 'ip.id', 'Flows'],
                     how='left')
# Time_Data.to_csv(MergedDatasetFilename, mode='w')

# This dataframe has all Tx packets and hence can be used to number the packets
Time_Data["Packet Number"] = Time_Data.index
Time_Data['Latency (ms)'] = (Time_Data["Epoch Time (Rx)"] - Time_Data["Epoch Time (Tx)"]) * 1000
Time_Data['Loss'] = Time_Data["Epoch Time (Rx)"].isnull()

# CumulativeSumOfLostPackets = Time_Data['Missed'].cumsum()
# CumulativeSumOfReceivedPackets = (~Time_Data['Missed']).cumsum()
# Time_Data[Time_Data['Flows']=='BE']['Missed'].cumsum()

# Time_Data['Epoch Time (Tx)'] = pd.to_datetime(Time_Data['Epoch Time (Tx)'], unit='s')
# Time_Data['Epoch Time (Rx)'] = pd.to_datetime(Time_Data['Epoch Time (Rx)'], unit='s')
# Time_Data['Latency (ms)'] = pd.to_datetime(Time_Data['Latency (ms)'], unit='s')

# Define min and max limits and use them to plot graph over whole range
PacketNumberMin = Time_Data['Packet Number'].min()
PacketNumberMax = Time_Data['Packet Number'].max()
TxTimeMin = Time_Data['Epoch Time (Tx)'].min()
TxTimeMax = Time_Data['Epoch Time (Tx)'].max()

''' Data divided to bins '''
Time_Data['Time Axis'] = pd.cut(Time_Data['Packet Number'], bins=BinSize, labels=False)
Time_Data = Time_Data.astype({'Packet Number': 'uint64'})
# Aggregated_Data = Time_Data.groupby(['Time Axis', 'Flows', 'Lost'], as_index=False)
Aggregated_Data = Time_Data.groupby(['Time Axis', 'Flows'], as_index=False)
AggregatedCount = Aggregated_Data.count()
AggregatedCount['Loss'] = AggregatedCount['Packet Number'] - AggregatedCount['Latency (ms)']
AggregatedCount['Loss %'] = AggregatedCount['Loss'] * 100 / AggregatedCount['Packet Number']


def print_all_info():
    print('=======> Latency Statistics of each flow and overall')
    print(Time_Data['Latency (ms)'].describe())
    print(Time_Data.groupby('Flows')['Latency (ms)'].describe())
    print('======> Total Packets of each Flow')
    print(Time_Data['Flows'].value_counts())

    print('======> PacketLoss TimeSeries')
    print(AggregatedCount[['Time Axis', 'Flows', 'Loss', 'Loss %']].transpose())


print_all_info()


# Separate the flow dataframes for now, until you find a better
# way of representation without doing this separation
FlowST = Time_Data[Time_Data['Flows'] == 'ST']
FlowBE = Time_Data[Time_Data['Flows'] == 'BE']
FlowST2 = Time_Data[Time_Data['Flows'] == 'ST2']
FlowSTLoss = AggregatedCount[AggregatedCount['Flows'] == 'ST'][['Time Axis', 'Flows', 'Loss', 'Loss %']]
FlowBELoss = AggregatedCount[AggregatedCount['Flows'] == 'BE'][['Time Axis', 'Flows', 'Loss', 'Loss %']]


if Plotting == "Subplots":

    ''' Latency '''
    fig, axes = plt.subplots(3, 3, tight_layout=True)  # , sharex='col')
    # fig.suptitle('Latency vs Time - for Scheduled Traffic and Best Effort flows - [Scheduled Traffic (ST)]', y=1)
    ' Latency TimeSeries '
    sns.boxplot(ax=axes[0, 0], data=FlowST, x='Time Axis', y='Latency (ms)', showfliers=True, flierprops=flierprops)
    sns.boxplot(ax=axes[1, 0], data=FlowBE, x='Time Axis', y='Latency (ms)', showfliers=True, flierprops=flierprops)
    sns.boxplot(ax=axes[2, 0], data=Time_Data, x='Time Axis', y='Latency (ms)', hue='Flows', showfliers=False, flierprops=flierprops)
    #axes[0, 0].grid()
    #axes[1, 0].grid()
    axes[0, 0].set_title('Latency TimeSeries [ST]')
    axes[1, 0].set_title('Latency TimeSeries [BE]')
    axes[2, 0].set_title('Latency TimeSeries [ST, BE]')
    axes[0, 0].set_xlabel('Time')
    axes[1, 0].set_xlabel('Time')
    axes[2, 0].set_xlabel('Time')
    # sns.despine()

    ' Latency TimeSeries - PacketPlot '
    sns.scatterplot(ax=axes[0, 1], data=FlowST, x="Packet Number", y="Latency (ms)")
    sns.scatterplot(ax=axes[1, 1], data=FlowBE, x="Packet Number", y="Latency (ms)")
    sns.scatterplot(ax=axes[2, 1], data=Time_Data, x="Packet Number", y="Latency (ms)", hue='Flows', style='Flows', size='Flows', palette='dark')
    axes[0, 1].set_title('Latency TimeSeries - PacketPlot [ST]')
    axes[1, 1].set_title('Latency TimeSeries - PacketPlot [BE}')
    axes[2, 1].set_title('Latency TimeSeries - PacketPlot [ST, BE]')
    # Important : Plot of received timestamp for these flows shows clear demarcation
    # sns.scatterplot(data=Time_Data, x='Packet Number', y= 'Epoch Time (Rx)', hue='Flows')

    ' Latency CDF '
    sns.ecdfplot(ax=axes[0, 2], data=FlowST, x="Latency (ms)", lw=7, stat='proportion', log_scale=(False, False))
    # sns.ecdfplot(ax=axes[0, 2], data=FlowST2, x="Latency (ms)", lw=7, stat='count', log_scale=(False, False))
    sns.ecdfplot(ax=axes[1, 2], data=FlowBE, x="Latency (ms)", lw=7, stat='proportion', log_scale=(False, False))
    sns.ecdfplot(ax=axes[2, 2], data=Time_Data, x="Latency (ms)", hue='Flows', lw=7, stat='proportion', log_scale=(False, False))
    # sns.stripplot(x='Flows', y='Latency (ms)', data=Time_Data)
    #axes[0, 2].grid()
    #axes[1, 2].grid()
    axes[0, 2].set_title('Latency CDF [ST]')
    axes[1, 2].set_title('Latency CDF [BE]')
    axes[2, 2].set_title('Latency CDF [ST, BE]')

    ''' PacketLoss '''
    fig, axes = plt.subplots(3, 3, tight_layout=True)  # , sharex='col')
    ' PacketLoss TimeSeries '
    sns.scatterplot(ax=axes[0, 0], data=FlowSTLoss, x='Time Axis', y='Loss %')
    sns.scatterplot(ax=axes[1, 0], data=FlowBELoss, x='Time Axis', y='Loss %')
    sns.scatterplot(ax=axes[2, 0], data=AggregatedCount, x='Time Axis', y='Loss %', hue='Flows', style='Flows', size='Flows', palette='dark', legend=True)
    #axes[0, 0].grid()
    #axes[1, 0].grid()
    axes[0, 0].set_title('PacketLoss TimeSeries [ST]')
    axes[1, 0].set_title('PacketLoss TimeSeries [BE]')
    axes[2, 0].set_title('PacketLoss TimeSeries [ST, BE]')
    axes[0, 0].set_xlabel('Time')
    axes[1, 0].set_xlabel('Time')
    axes[2, 0].set_xlabel('Time')
    # sns.despine()

    ' PacketLoss TimeSeries - PacketPlot '
    sns.scatterplot(ax=axes[0, 1], data=FlowST.iloc[len(FlowST)-40:len(FlowST)], x='Packet Number', y='Loss')
    sns.scatterplot(ax=axes[1, 1], data=FlowBE.iloc[len(FlowBE)*2//3 - 100:len(FlowBE)*2//3], x='Packet Number', y='Loss')
    sns.scatterplot(ax=axes[2, 1], data=Time_Data.iloc[len(FlowBE)//3:len(FlowBE)*2//3], x='Packet Number', y='Loss', hue='Flows', style='Flows', size='Flows', palette='dark')
    axes[0, 1].set_title('PacketLoss TimeSeries - PacketPlot [ST]')
    axes[1, 1].set_title('PacketLoss TimeSeries - PacketPlot [BE}')
    axes[2, 1].set_title('PacketLoss TimeSeries - PacketPlot [ST, BE]')

    ' PacketLoss CDF - PacketPlot'
    sns.ecdfplot(ax=axes[0, 2], data=FlowST[FlowST['Loss']], x='Packet Number')
    sns.ecdfplot(ax=axes[1, 2], data=FlowBE[FlowBE['Loss']], x='Packet Number')
    if not Time_Data[Time_Data['Loss']].empty:
        sns.ecdfplot(ax=axes[2, 2], data=Time_Data[Time_Data['Loss']], x='Packet Number', hue='Flows')

elif Plotting == "Separate":

    ''' Latency '''
    ' Latency CDF '
    fig, axes = plt.subplots(1, 2, tight_layout=True)  # , sharex='col')
    sns.ecdfplot(ax=axes[0], data=FlowST, x="Latency (ms)", lw=7, stat='proportion', log_scale=(False, False))
    sns.ecdfplot(ax=axes[1], data=FlowBE, x="Latency (ms)", lw=7, stat='proportion', log_scale=(False, False))
    axes[0].set_ylabel('Latency CDF [ST]')
    axes[1].set_ylabel('Latency CDF [BE]')
    fig.suptitle('Cumulative Distribution Function (CDF) of Latency')  #, y=1)

plt.show()

''' To optimize the code '''
# If you want to optimize the python code, you can do the below line and other things
# Such as do strongly-typed code (convert some things to signed int) etc.
# dftx = dftx.astype({'Flows': 'uint8'})
# Time_Data = Time_Data.astype({'Latency (ms)': 'float'})
