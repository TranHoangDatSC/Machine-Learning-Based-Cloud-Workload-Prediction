Alibaba Cluster Trace v2018 (cluster-trace-v2018)

Trace Description
The trace is sampled from one of Alibaba's production clusters and describes the activity of about 4,000 machines over a period of 8 days. Unlike the 2017 release, this trace records both long-running online services (containers) and batch workloads co-located on the same machines, which makes it representative of a production co-location environment.

The trace is released as six tables: machine_meta, machine_usage, container_meta, container_usage, batch_task and batch_instance. This directory contains machine_usage, the machine-level resource utilisation table.

The format of machine_usage.csv is row-based and comma-separated. The file has NO header row. Each row represents one utilisation sample of one machine. The format of each row is

machine_id: uid of the machine.
time_stamp: time stamp of the sample, in seconds, relative to the start of the trace.
cpu_util_percent: CPU utilisation, in percent, [0, 100].
mem_util_percent: memory utilisation, in percent, [0, 100].
mem_gps: normalized memory bandwidth, [0, 100].
mkpi: cache miss per thousand instructions.
net_in: normalized incoming network traffic, [0, 100].
net_out: normalized outgoing network traffic, [0, 100].
disk_io_percent: disk I/O utilisation, in percent, [0, 100]. Abnormal values are of -1 or 101.

Notes on the released data
The mem_gps and mkpi columns are only populated for a subset of the samples and are empty for the majority of rows.
Sampling is nominally every 10 seconds per machine, but the interval is irregular and gaps occur.
disk_io_percent contains the sentinel values -1 and 101 to mark abnormal readings, as documented in the official schema.

Copyright note
This trace was released by Alibaba Group. To use this trace, you must include an acknowledgement to the source of the data in any published material that refers to the data. Please refer to the schema and documentation in the official repository.

Jing Guo, Zihao Chang, Sa Wang, Haiyang Ding, Yihui Feng, Liang Mao, Yungang Bao, Who Limits the Resource Efficiency of My Datacenter: An Analysis of Alibaba Datacenter Traces, the 27th IEEE/ACM International Symposium on Quality of Service (IWQoS), 2019, Phoenix, USA

Source => https://github.com/alibaba/clusterdata/tree/master/cluster-trace-v2018
