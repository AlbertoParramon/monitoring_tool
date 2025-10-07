# monitoring\_tool
Monitoring cpu and memory consumption by system processes with nmon and python

## Prerequisites
- nmon (version 16n) 
- python

## Quick start
```bash
# 1. Run process_monitor.sh in the machine where you want to monitor the cpu and mem consumption by the processes
./process_monitor.sh -b processes -t 86400 -i 30 # it takes samples every 30 seconds during 1 day and produces processes.dat and processes.nmon files

# 2. Run analyze_cpu_mem.py with those files.
python3 analyze_cpu_mem.py processes.nmon processes.dat
python3 analyze_cpu_mem.py processes.nmon processes.dat T0010 T0090
python3 analyze_cpu_mem.py  --help
```

## Examples
After you have the files, you can first run the Python script without timestamp arguments.
```bash
python3 analyze_cpu_mem.py processes.nmon processes.dat
```
This allows you to check which timestamps show higher CPU or memory consumption.

<img width="585" height="534" alt="captura1" src="https://github.com/user-attachments/assets/b6266796-7fef-4b85-9a18-0eec5beecbf7" />

After that, you can choose an interval that includes a specific timestamp for further analysis.

<img width="1250" height="694" alt="captura2" src="https://github.com/user-attachments/assets/c6bffb38-aee8-4a5c-aa03-827d759a9904" />

You can also view a summary of all timestamps directly in your terminal.

<img width="465" height="771" alt="captura3" src="https://github.com/user-attachments/assets/650119eb-951c-464c-a53f-2ab697eb9c9d" />



