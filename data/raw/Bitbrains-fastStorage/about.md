GWA-T-12 BitBrains

Grid Description
The dataset contains the performance metrics of 1,750 VMs from a distributed datacenter from Bitbrains, which is a service provider that specializes in managed hosting and business computation for enterprises. Customers include many major banks (ING), credit card operators (ICS), insurers (Aegon), etc. Bitbrains hosts applications used in the solvency domain; examples of application vendors are Towers Watson and Algorithmics. These applications are typically used for financial reporting, which is used predominately at the end of financial quarters.

Each file contains the performance metrics of a VM. These files are organized according by traces: fastStorage and Rnd.

The first trace, fastStorage, consists of 1,250 VMs that are connected to fast storage area network (SAN) storage devices. The second trace, Rnd, consists of 500 VMs that are either connected to the fast SAN devices or to much slower Network Attached Storage (NAS) devices. The fastStorage trace includes a higher fraction of application servers and compute nodes than the Rnd trace, which is due to the higher performance of the storage attached to the fastStorage machines. Conversely, for the Rnd trace we observe a higher fraction of management machines, which only require storage with lower performance and less frequent access.

In the Rnd directory, the files are organized into 3 sub-directories by the month that the metrics are recorded.

The format of each file is row-based, each row represent an observation of the performance metrics. Each column of a row is separate by “;\t” The format of each row is

Timestamp: number of milliseconds since 1970-01-01.
CPU cores: number of virtual CPU cores provisioned.
CPU capacity provisioned (CPU requested): the capacity of the CPUs in terms of MHZ, it equals to number of cores x speed per core.
CPU usage: in terms of MHZ.
CPU usage: in terms of percentage
Memory provisioned (memory requested): the capacity of the memory of the VM in terms of KB.
Memory usage: the memory that is actively used in terms of KB.
Disk read throughput: in terms of KB/s
Disk write throughput: in terms of KB/s
Network received throughput: in terms of KB/s
Network transmitted throughput: in terms of KB/s

Siqi Shen, Vincent van Beek, Alexandru Iosup, Statistical Characterization of Business-Critical Workloads Hosted in Cloud Datacenters, the 15th IEEE/ACM International Symposium on Cluster, Cloud and Grid Computing (CCGrid), 2015, ShenZhen, China