# monitoring\_tool
Monitoring cpu and memory consumption by system processes with nmon and python

## Prerequisites
- nmon (version 16n) 
- python

## Quick start
```bash
# 1. Run process_monitor.sh in the machine where you want to monitor the cpu and mem consumption by the processes
./process_monitor.sh processes 86400 30 # it takes samples every 30 seconds during 1 day and produces processes.dat and processes.nmon files

# 2. Run analyze_cpu_mem.py with that files.
./analyze_cpu_mem.py processes.nmon processes.dat
```
