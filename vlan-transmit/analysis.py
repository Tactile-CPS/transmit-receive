#!/opt/venv/bin/python3

# Author        : Joydeep Pal
# Date          : Nov-2022
# Date Modified : May-2023
# Description   : Plots latency for ST snd BE flows

import sys
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

Plotting = "Subplots" # "Subplots"  # "Separate"
flierprops = dict(marker='o', markersize=1)  # Define outlier properties of boxplots
sns.set_theme(style='white', context='notebook',
              font_scale=0.75, rc={'figure.figsize': (16, 9)})

BinSize = 20
FileDate = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

dftx = pd.read_csv("/tmp/TXv1.csv")
dfrx = pd.read_csv("/tmp/RXv1.csv")
dftx.rename(columns={"vlan.id": "Flows", 'frame.time_epoch': 'Epoch Time (Tx)'}, inplace=True)
dfrx.rename(columns={"vlan.id": "Flows", 'frame.time_epoch': 'Epoch Time (Rx)'}, inplace=True)
dftx['Flows'].replace({2: 'ST', 3: 'BE', 4: 'ST2'}, inplace=True)
dfrx['Flows'].replace({2: 'ST', 3: 'BE', 4: 'ST2'}, inplace=True)
# dftx.rename(columns={"udp.dstport": "Flows"}, inplace=True)
# Time_Data['Flows'] = Time_Data['Flows'].replace([3001], 'ST')
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

    FigureName = ('/home/zenlab/Documents/tsn-project/Results/temp-figures/' +
                  'S_' + bandwidth[0] + '_B_' + bandwidth[1] +
                  '_Dur_' + duration + 's_' +
                  FileDate + '.png')
    MergedDatasetFilename = ('/home/zenlab/Documents/tsn-project/data-pcap-csv/csv-temp/' +
                             'S_' + bandwidth[0] + '_B_' + bandwidth[1] +
                             '_Dur_' + duration + 's_' +
                             FileDate + '.csv')
    # plt.savefig(FigureName)

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
# CumulativeSumOfLostPackets = Time_Data['Missed'].cumsum()
# CumulativeSumOfReceivedPackets = (~Time_Data['Missed']).cumsum()
# Time_Data[Time_Data['Flows']=='BE']['Missed'].cumsum()

# Time_Data['Epoch Time (Tx)'] = pd.to_datetime(Time_Data['Epoch Time (Tx)'], unit='s')
# Time_Data['Epoch Time (Rx)'] = pd.to_datetime(Time_Data['Epoch Time (Rx)'], unit='s')
# Time_Data['Latency (ms)'] = pd.to_datetime(Time_Data['Latency (ms)'], unit='s')
Time_Data['Missed'] = Time_Data["Epoch Time (Rx)"].isnull()

# Define min and max limits and use them to plot graph over whole range
PacketNumberMin = Time_Data['Packet Number'].min()
PacketNumberMax = Time_Data['Packet Number'].max()
TxTimeMin = Time_Data['Epoch Time (Tx)'].min()
TxTimeMax = Time_Data['Epoch Time (Tx)'].max()

# Show min and max latency using graphs

# df['Count'] = df.groupby(['Medicine'])['Dosage'].transform('count')
# Time_Data.groupby(['Flows'])['Latency (ms)'].describe()
# gfh = Time_Data.groupby(['Time Axis'])
# A = (TxPacketCount['Flows']['ST'] - RxPacketCount['Flows']['ST']) * 100 / TxPacketCount['Flows']['ST']

# BinsNo = len(Time_Data)/BinSize
# Time_Data['Time Axis'] = Time_Data['Packet Number']/BinsNo
Time_Data['Time Axis'] = pd.cut(Time_Data['Packet Number'], bins=BinSize, labels=False)
Time_Data = Time_Data.astype({'Packet Number': 'uint64'})

''' Data divided to bins '''
# Aggregated_Data = Time_Data.groupby(['Time Axis', 'Flows', 'Missed'], as_index=False)
Aggregated_Data = Time_Data.groupby(['Time Axis', 'Flows'], as_index=False)
AggregatedCount = Aggregated_Data.count()
AggregatedCount['Loss'] = AggregatedCount['Packet Number'] - AggregatedCount['Latency (ms)']
AggregatedCount['Loss %'] = AggregatedCount['Loss'] * 100 / AggregatedCount['Packet Number']
''' Lost packets '''
LostPacketsList = Time_Data[Time_Data['Missed']]
# LostPacketsList = Time_Data[Time_Data['Missed']][[
#     "frame.time_epoch_x", "Packet Number", "Flows", "Time Axis"]]


def print_all_info():
    print('Tx Count = ' + str(TxCountTotal))
    # print('TxCountOfEachFlow', TxCountOfEachFlow)
    # dftx['Flows'].value_counts()[3.0]

    # Printing errrors thgen use below code
    # if 'ST' in RxPacketCount.index:
    #     A = RxPacketCount['ST'] * 100 / TxPacketCount['ST']
    #     print(f"VLAN ST Rx % = {A:.2f}")
    # else:
    #     print(f'VLAN ST Rx % = 0')
    # if 'BE' in RxPacketCount.index:
    #     B = RxPacketCount['BE'] * 100 / TxPacketCount['BE']
    #     print(f"VLAN BE Rx % = {B:.2f}")
    # else:
    #     print(f'VLAN BE Rx % = 0')
    # rte = dftx.groupby(['ip.id', 'udp.dstport']).size().reset_index().rename(columns={0: 'count'})


print(Time_Data['Latency (ms)'].describe())

if Plotting == "Subplots":

    # Separate the flow dataframes for now, until you find a better
    # way of representation without doing this separation
    FlowST = Time_Data[Time_Data['Flows'] == 'ST']
    FlowBE = Time_Data[Time_Data['Flows'] == 'BE']
    FlowST2 = Time_Data[Time_Data['Flows'] == 'ST2']

    fig, axes = plt.subplots(3, 3)  # , sharex='col', tight_layout=True)
    # fig.suptitle('Latency vs Time - for Scheduled Traffic and Best Effort flows - [Scheduled Traffic (ST)]', y=1)

    ''' Latency - Separate - Aggregate plot '''
    sns.boxplot(ax=axes[0, 0], data=FlowST, x='Time Axis',
                y="Latency (ms)", showfliers=False, flierprops=flierprops).set_title('Latency vs Time (ST)')
    sns.boxplot(ax=axes[1, 0], data=FlowBE, x='Time Axis',
                y="Latency (ms)", showfliers=False, flierprops=flierprops).set_title('Latency vs Time (BE)')

    # sns.despine()

    ''' Latency - Separate - Packet plot - CDF(Latency) '''
    sns.ecdfplot(ax=axes[0, 2], data=FlowST, x="Latency (ms)",
                 stat='count', log_scale=(False, False)).set_title('CDF (ST)')
    sns.ecdfplot(ax=axes[0, 2], data=FlowST2, x="Latency (ms)",
                 stat='count', log_scale=(False, False))
    sns.ecdfplot(ax=axes[1, 2], data=FlowBE, x="Latency (ms)",
                 stat='count', log_scale=(False, True)).set_title('CDF (BE)')
    axes[0, 2].grid()
    axes[1, 2].grid()

    ''' Latency - One - Aggregate plot '''
    sns.boxplot(ax=axes[2, 0], data=Time_Data, x='Time Axis', y='Latency (ms)',
                hue='Flows', flierprops=flierprops).set_title('Latency vs Time')
    # sns.boxplot(ax=axes[2, 0], data=Time_Data, x='Time Axis', y='Latency (ms)',
    #             hue='Flows', showfliers=False)

    ''' Latency - One - Packet plot '''
    sns.scatterplot(ax=axes[0, 1], data=Time_Data, x="Packet Number", y="Latency (ms)",
                    hue='Flows', style='Flows', size='Flows',
                    palette='dark').set_title('Latency vs Time')

    ''' Count - One - Aggregate plot - Loss and Loss %age'''
    sns.scatterplot(ax=axes[2, 2], data=AggregatedCount, x='Time Axis', y='Loss',
                    hue='Flows', style='Flows', size='Flows',
                    palette='dark').set_title('Loss vs Time')
    ax1 = axes[2, 2].twinx()
    # sns.scatterplot(ax=ax1, data=AggregatedCount, x='Time Axis', y='Loss %',
    # hue='Flows', style='Flows', size='Flows', palette='dark')
    sns.lineplot(ax=ax1, data=AggregatedCount, x='Time Axis', y='Loss %',
                 hue='Flows', style='Flows', size='Flows',
                 palette='dark', legend=True)

    ''' Count - One - Packet plot - Received and Lost packets'''
    # Horizontal packets vs time
    sns.scatterplot(ax=axes[1, 1], data=Time_Data, x='Epoch Time (Rx)', y='Missed',
                    hue='Flows', style='Flows', size='Flows',
                    palette='dark').set_title('Rx & Lost vs Time')
    # Diagnol packets vs time
    # LostPacketPlot = sns.scatterplot(ax=axes[2, 2], data=LostPacketsList, x='Epoch Time (Tx)',
    #                                  y='Packet Number', hue='Time Axis', size='Flows')('Lost vs Time')
    sns.scatterplot(ax=axes[2, 1], data=LostPacketsList, x='Packet Number', y='Packet Number',
                    hue='Time Axis', size='Flows').set_title('Lost vs Time')
    axes[2, 1].set_ylim(PacketNumberMin, PacketNumberMax)
    # axes[2, 1].set_xlim(TxTimeMin, TxTimeMax)
    axes[2, 1].set_xlim(PacketNumberMin, PacketNumberMax)
    # CDF of lost packets
    # sns.ecdfplot(data=Time_Data, x='Missed', hue='Flows')
    # sns.scatterplot(data=Time_Data, x='Packet Number', y=(~Time_Data['Missed']).cumsum())
    # sns.scatterplot(data=Time_Data, x='frame.time_epoch_x', y=(~Time_Data['Missed']).cumsum(), hue='Flows')
    plt.tight_layout()

elif Plotting == "Separate":

    ''' Latency - Separate - Aggregate plot '''
    # Plot catplot(boxplot) without outliers for Latency experienced by the ST and BE flows
    # LatencyCol = sns.FacetGrid(Time_Data, row='Flows', sharex=True, sharey=False)
    # LatencyCol.map(sns.boxplot, 'Time Axis', 'Latency (ms)', showfliers=False)

    ''' Latency - Separate - Packet plot - CDF(Latency) '''
    # plt.figure()
    # LatencyCDF = sns.FacetGrid(Time_Data, col='Flows', sharex=False)
    # LatencyCDF.map(sns.ecdfplot, "Latency (ms)")
    # LatencyCDF.set_ylabels("CDF/Proportion")
    # LatencyCountCDF = sns.FacetGrid(Time_Data, col='Flows', sharex=False)
    # LatencyCountCDF.map(sns.ecdfplot, "Latency (ms)", stat="count")

    ''' Latency - One - Aggregate plot '''
    # sns.catplot(data=Time_Data, x='Time Axis',
    # y="Latency (ms)", hue="Flows", kind='box', flierprops=flierprops) # ,showfliers=False)

    ''' Latency - One - Packet plot '''
    # sns.relplot(x="Packet Number", y="Latency (ms)", hue='Flows', kind='scatter', data=Time_Data)
    # sns.stripplot(x='Flows', y='Latency (ms)', data=Time_Data)
    # ax1=ax.twinx()
    # Plot of received timestamp for these flows shows clear demarcation
    # sns.scatterplot(data=Time_Data, x='Packet Number', y= 'Epoch Time (Rx)', hue='Flows')
    # plt.savefig(FigureName)
    # plt.grid()

    ''' Count - One - Aggregate plot - Received and Lost Packets '''
    # plt.figure()
    # LostPacketPlotAggregate = sns.countplot(data=Time_Data, x='Time Axis', hue='Flows')

    ''' Count - One - Packet plot - Received and Lost Packets Plot '''
    # plt.figure()
    # PacketPlot_v0 = sns.scatterplot(data=Time_Data, x='Packet Number', y='Missed', hue='Flows')
    # plt.figure()
    # LostPacketPlot = sns.scatterplot(data=LostPacketsList, x='Epoch Time (Tx)',
    #                                 y='Packet Number', hue='Time Axis', size='Flows')
    # LostPacketPlot.set_ylim(PacketNumberMin, PacketNumberMax)
    # LostPacketPlot.set_xlim(TxTimeMin, TxTimeMax)
    # sns.displot(Time_Data, x='Packet Number', bins=33, hue='Flows', multiple="dodge", discrete=True)
    # plt.savefig(FigureNameLostCount)
    # if LostPacketsList.shape[0] > 0:
    #     sns.countplot(data=LostPacketsList, x='Time Axis', hue="Flows")


plt.show()

''' To optimize the code '''
# If you want to optimize the python code, you can do the below line and other things
# Such as do strongly-typed code (convert some things to signed int) etc.
# dftx = dftx.astype({'Flows': 'uint8'})
# Time_Data = Time_Data.astype({'Latency (ms)': 'float'})
