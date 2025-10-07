#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script simplificado para generar gráfica de CPU por timestamps
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from matplotlib.patches import Patch

def normalize_pid(pid):
    """
    Normalize a PID by removing leading zeros
    """
    try:
        return str(int(pid))
    except (ValueError, TypeError):
        return pid

def get_cpu_info(filename):
    """
    Get CPU information from the NMON file
    """
    cpu_count = 0
    
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            for line in file:
                line = line.strip()
                # Search for format AAA,cpus,32
                if line.startswith('AAA,cpus,'):
                    parts = line.split(',')
                    if len(parts) >= 3:
                        cpu_count = int(parts[2])
                        break
                # Search for format BBBP,lscpu (alternative format)
                elif line.startswith('BBBP,') and 'lscpu' in line:
                    if 'CPU(s):' in line:
                        parts = line.split(',')
                        if len(parts) >= 3:
                            cpu_info = parts[2].strip()
                            if 'CPU(s):' in cpu_info:
                                cpu_count = int(cpu_info.split(':')[1].strip())
                                break
    except Exception as e:
        print(f"CPU information could not be obtained: {e}")
        sys.exit(1)
    
    return cpu_count

def load_process_details(processes_file="process_details.txt"):
    """
    Load the current processes file and create a mapping PID -> detailed information
    """
    pid_details = {}
    
    if not os.path.exists(processes_file):
        print(f"Advertencia: No se encontró el archivo '{processes_file}'")
        sys.exit(1)
    
    try:
        with open(processes_file, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if line and ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        pid = normalize_pid(parts[0].strip())
                        details = parts[1].strip()
                        pid_details[pid] = details
        
    except Exception as e:
        print(f"Error al cargar '{processes_file}': {e}")
        sys.exit(1)
    
    return pid_details

def parse_monitoring_data(filename):
    """
    Parse the monitoring file and extract the process data
    """
    
    # Verificar que el archivo existe
    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' does not exist")
        sys.exit(1)
    
    processes_data = []
    timestamps = {}
    count = 0

    # First, parse the ZZZZ lines to get the real hours
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            line = line.strip()
            if line.startswith('ZZZZ,'):
                # Parse the ZZZZ line: ZZZZ,TIMESTAMP,HORA,FECHA
                parts = line.split(',')
                if len(parts) >= 4:
                    try:
                        timestamp = parts[1]
                        time_str = parts[2]
                        date_str = parts[3]
                        
                        # Create time label
                        time_label = f"{time_str}-{date_str}"
                        #DELETE timestamp_times[timestamp] = time_label
                        timestamps[count] = {"time_label": time_label, "timestamp": timestamp}
                        count += 1
                        
                    except (ValueError, IndexError) as e:
                        print(f"Error: {e}")
                        continue
    
    # Now parse the TOP lines
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        for line in file:
            line = line.strip()
            if line.startswith('TOP,') and not line.startswith('TOPZZZZ'):
                # Skip header lines
                if '%CPU' in line or '+PID' in line:
                    continue
                
                # Parse the process line
                parts = line.split(',')
                if len(parts) >= 15:
                    try:
                        process_data = {
                            'timestamp': parts[2] if len(parts) > 2 else '',
                            'pid': parts[1] if len(parts) > 1 else '',
                            'cpu_percent': float(parts[3]) if len(parts) > 3 else 0.0,
                            'memory_percent': float(parts[4]) if len(parts) > 4 else 0.0,
                            'command': parts[13] if len(parts) > 13 else 'unknown'
                        }
                        processes_data.append(process_data)
                        
                            
                    except (ValueError, IndexError) as e:
                        print(f"Error: {e}")
                        continue
    
    return processes_data, timestamps

def create_cpu_chart(processes_data, timestamps, pid_details=None, output_filename=None, mode="cpu",max=None):
    """
    Create a unique chart with the CPU consumption of the top 5 processes by timestamp
    """

    if mode == "cpu":
        key_word = "CPU"
        process_data_column = "cpu_percent"
    elif mode == "mem":
        key_word = "Memory"
        process_data_column = "memory_percent"

    # Prepare data for the chart
    _, ax = plt.subplots(figsize=(16, 9))
    
    # Colors for the processes (more colors to handle more processes)
    colors = ['#F5917D','#CEED51','#ED8C13','#93F27C','#6EF5F5','#F5EF78',
    '#62CBF5','#619AFA','#9FC2FC','#6F6BFA','#804E44','#9D6BFA','#EC6BFA',
    '#ED4424','#045959','#780885','#FAA5DC','#C2B906','#F2BD7C','#748F07','#1F8F04','#0CA6A6']
    
    # Positions of the bars
    bar_width = 0.8

    # Set to track all processes that appear in the top 5
    all_top_processes = set()
    pid_to_color = {}  # Mapeo PID -> color
    total_attr_values = []
    color_counter = 0
    
    # For each timestamp, create stacked bars
    df_processes_data = pd.DataFrame(processes_data)
    for i in range(len(timestamps)):
        timestamp_data = df_processes_data[df_processes_data['timestamp'] == timestamps[i]['timestamp']]
        
        # Calculate total attr
        total_attr = timestamp_data[process_data_column].sum()

        # Identify the top 5 processes of this specific timestamp
        top_processes_this_timestamp = timestamp_data.nlargest(5, process_data_column)
        top_processes_this_timestamp = [{'pid': row['pid'], 'command': row['command'], process_data_column: row[process_data_column], 
        'detailed_command': ''} for _, row in top_processes_this_timestamp.iterrows()]
        #print(f"DEBUG: Top processes this timestamp: {top_processes_this_timestamp}")
        total_attr_values.append({"timestamp": timestamps[i]['timestamp'], "time_label": timestamps[i]['time_label'], "total_attr": total_attr, 
                                "top_processes": top_processes_this_timestamp})

        attr_sum = 0
        bottom = 0 # Create stacked bars
        for process in top_processes_this_timestamp:
            pid = process['pid']
            cmd = process['command']
            attr_percent = process[process_data_column]
            # Assign unique colors by PID
            if pid not in pid_to_color:
                pid_to_color[pid] = colors[color_counter % len(colors)]
                color_counter += 1

            # Add to the sum of the attr of the top 5 processes
            attr_sum += attr_percent

            # Draw bars for the top 5 processes of this timestamp
            if attr_percent > 0:
                # Use detailed information if available
                normalized_pid = normalize_pid(pid)
                if pid_details and normalized_pid in pid_details:
                    process['detailed_command'] = pid_details[normalized_pid]
                else:
                    process['detailed_command'] = cmd
                label_text = f"PID {pid} - {process['detailed_command']}"
                
                # Use color based on the PID (consistent)
                color = pid_to_color[pid]
                
                ax.bar(i, attr_percent, bottom=bottom, color=color, width=bar_width, 
                      label=label_text if i == 0 else "")
                bottom += attr_percent

            # Add to the set of all top processes
            all_top_processes.add((pid, cmd, attr_percent, process['detailed_command']))
    
        
        # attr of the rest of the processes
        other_attr = total_attr - attr_sum
        
        # Draw bar for the rest of the processes
        if other_attr > 0:
            ax.bar(i, other_attr, bottom=bottom, color='#cccccc', width=bar_width,
                  label="Other processes" if i == 0 else "")
    
    # Configure graph
    ax.set_xlabel('Timestamps', fontsize=12, fontweight='bold')
    ax.set_ylabel(f'{key_word} Consumption (%)', fontsize=12, fontweight='bold')
    
    # Title with maximum attr information if available
    if max:
        title = f'{key_word} Consumption by Timestamp - Top 5 Processes (Max: {max}%)'
    else:
        title = f'{key_word} Consumption by Timestamp - Top 5 Processes'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xticks(np.arange(len(total_attr_values)))
    
    # Create labels with only the hour (HH:mm)
    x_labels = []
    for i in range(len(total_attr_values)):
        # Extract only the hour from the time information
        time_info = total_attr_values[i]['time_label']
        # The hour is in the first line, before the line break
        full_time = time_info.split('-')[0]
        # Extract only hours and minutes (HH:mm)
        hour_minutes = full_time.split(':')[:2]
        label = f"{hour_minutes[0]}:{hour_minutes[1]}"
        x_labels.append(label)
    
    ax.set_xticklabels(x_labels, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Create legend with all unique processes that appeared in the top 5 
    legend_handles = []
    legend_labels = []
    
    # Create a set of unique PIDs for the legend
    unique_pids = set()
    for pid, cmd, attr_percent, detailed_command in all_top_processes:
        unique_pids.add((pid, detailed_command))

    for pid, detailed_command in unique_pids:
        legend_handles.append(Patch(color=pid_to_color[pid]))
        legend_labels.append(f"PID {pid} - {detailed_command}")
    
    # Add "Other processes" to the legend
    legend_handles.append(Patch(color='#cccccc'))
    legend_labels.append("Other processes")
    
    # Show legend with more columns if there are many processes
    ncol = min(3, len(legend_labels))  # Reduce to 3 columns for better legibility
    ax.legend(legend_handles, legend_labels, loc='upper center', bbox_to_anchor=(0.5, -0.13), ncol=ncol, fontsize=9)
    
    # Add values in the bars
    for i in range(len(total_attr_values)):
        total_attr = total_attr_values[i]['total_attr']
        
        # Show total value on the top of each bar
        ax.text(i, total_attr + 2, f'{total_attr:.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Configure layout
    plt.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.25)
    

    #More consumption attr moments and processes
    print("\n------------------------------------------------------------")
    print(f"- {key_word} Consumption by Timestamp ")
    for i in range(len(total_attr_values)):
        print(f"Timestamp: {total_attr_values[i]['timestamp']} ({total_attr_values[i]['time_label']}) - Total {key_word}: {total_attr_values[i]['total_attr']}")
    print(f"\n- More consumption {key_word} moments and processes:")
    df_total_attr_values = pd.DataFrame(total_attr_values)
    for i, row in df_total_attr_values.nlargest(5, 'total_attr').iterrows():
        print(f"\nTimestamp: {row['timestamp']} ({row['time_label']}) - Total {key_word}: {row['total_attr']}")
        for process in row['top_processes']:
            print(f"\tPID {process['pid']} - {process['command']} - {process[process_data_column]}%")
    print("------------------------------------------------------------")

    if len(timestamps) > 100:
        print(f"\nWARNING: To draw the graph you must choice 100 or less timestamps. ")
        print(f"We recommend you to choice a range of timestamps between more consumption {key_word} moments.")
    else:
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"Graph saved as: {output_filename}")

    return list(all_top_processes)


def show_usage():
    """
    Muestra información de uso del script
    """
    print("USO DEL SCRIPT:")
    print("=" * 50)
    print("python3 analiza_cpu_mem.py <csv_file> <processes_file> [start_timestamp] [end_timestamp]")
    print()
    print("Argumentos:")
    print("  csv_file           - file csv with monitoring data from NMON")
    print("  processes_file     - file with detailed information about processes (PID,user - process)")
    print("  start_timestamp    - start timestamp (example: T0002) (optional)")
    print("  end_timestamp      - end timestamp (example: T0013) (optional)")
    print()
    print("Examples:")
    print("  # With this mode you will see a summary of the analysis but without graphs")
    print("  python3 analiza_cpu_mem.py datos.csv procesos.txt ")
    print("  # With this mode you will see a summary of the analysis with graphs")
    print("  python3 analiza_cpu_mem.py datos.csv procesos.txt T0002 T0013")
    print()

def filter_timestamps(timestamps, start_ts=None, end_ts=None):
    """
    Filter the timestamps according to the specified range
    """
    if start_ts is None and end_ts is None:
        return [timestamps[i] for i in timestamps.keys()]
    
    filtered_timestamps = []
    start_found = start_ts is None
    end_found = False
    
    for i in timestamps.keys():
        # If we haven't found the start, search
        if not start_found:
            if timestamps[i]['timestamp'] == start_ts:
                start_found = True
            else:
                continue
        
        # If we have found the start, add timestamps
        if start_found:
            filtered_timestamps.append(timestamps[i])
            
            # If we have found the end, stop
            if end_ts is not None and timestamps[i]['timestamp'] == end_ts:
                end_found = True
                break
    
    if start_ts is not None and not start_found:
        print(f"Warning: start timestamp not found: '{start_ts}'")
    
    if end_ts is not None and not end_found:
        print(f"Warning: end timestamp not found: '{end_ts}'")
    
    return filtered_timestamps

def main():
    # Verify arguments
    if len(sys.argv) < 3:
        print("Error: You must specify a CSV file and a processes file")
        show_usage()
        sys.exit(1)

    if len(sys.argv) > 5:
        print("Error: Too many arguments")
        show_usage()
        sys.exit(1)
    
    # Get mandatory arguments
    filename = sys.argv[1]
    processes_file = sys.argv[2]
    
    # Optional arguments
    start_timestamp = sys.argv[3] if len(sys.argv) >= 4 else None
    end_timestamp = sys.argv[4] if len(sys.argv) >= 5 else None
    
    # Parse data
    print("\n------------------------------------------------------------")
    print(f"Analizing file: {filename}")
    processes_data, timestamps = parse_monitoring_data(filename)
    print(f"\n- Found {len(timestamps)} timestamps")
    print(f"\t- From {timestamps[0]['timestamp']} at {timestamps[0]['time_label']} ")
    print(f"\t- To {timestamps[len(timestamps)-1]['timestamp']} at {timestamps[len(timestamps)-1]['time_label']}")
    print(f"- Found {len(processes_data)} pieces of information about processes in {len(timestamps)} timestamps")
    
    # Filter timestamps if a range is specified
    original_count = len(timestamps)
    timestamps = filter_timestamps(timestamps, start_timestamp, end_timestamp)
    print(f"\n- Filtering timestamps: {original_count} → {len(timestamps)}")
    print(f"\t- From {timestamps[0]['timestamp']} at {timestamps[0]['time_label']} ")
    print(f"\t- To {timestamps[len(timestamps)-1]['timestamp']} at {timestamps[len(timestamps)-1]['time_label']}")
    #print(f"DEBUG:Timestamps filtered: {timestamps}")
    
    if not timestamps:
        print("No timestamps in the specified range")
        sys.exit(1)

    filtered_timestamps = timestamps
    print(f"DEBUG: Filtered timestamps: {filtered_timestamps}")
    # Filter processes data according to the selected timestamps
    filtered_processes_data = []
    timestamp_list = [item['timestamp'] for item in filtered_timestamps]
    for process in processes_data:
        if process['timestamp'] in timestamp_list:
            filtered_processes_data.append(process)

    print(f"- Found {len(filtered_processes_data)} pieces of information about processes in the {len(filtered_timestamps)} filtered timestamps")
    print("------------------------------------------------------------")

    # Load detailed information about processes
    print("\n------------------------------------------------------------")
    pid_details = load_process_details(processes_file)
    print(f"Analizing file: {processes_file}")
    print(f"\n- Loaded {len(pid_details)} PID processes")
    print("------------------------------------------------------------")
    
    print("\n------------------------------------------------------------")
    print(f"Information about the system:")
    # Get CPU information from the system
    cpu_count = get_cpu_info(filename)
    cpu_max = cpu_count * 100 if cpu_count > 0 else None
    
    if cpu_max:
        print(f"\n- CPU system detected: {cpu_count} CPUs (Maximum: {cpu_max}%)")
    print("------------------------------------------------------------")

    # Create graphs
    top_cpu_process_ids = create_cpu_chart(filtered_processes_data, filtered_timestamps, pid_details, output_filename="cpu_graph.png", mode="cpu", max=cpu_max)
    top_cpu_process_ids = create_cpu_chart(filtered_processes_data, filtered_timestamps, pid_details, output_filename="mem_graph.png", mode="mem")
    
    
if __name__ == "__main__":
    main() 