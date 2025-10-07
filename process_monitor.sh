#!/bin/bash

process_cpu_mem() {
   local count_max=$((TIME_MONITORING_SECONDS/TIME_INTERVAL_SECONDS))
   nmon -f -T -s${TIME_INTERVAL_SECONDS} -c ${count_max}
   sleep $TIME_MONITORING_SECONDS

   # Rename the generated automatically file
   latest_nmon=$(ls -t *.nmon 2>/dev/null | head -1)
   if [ -n "$latest_nmon" ]; then
      mv "$latest_nmon" "${BASE_NAME}.nmon"
   fi

   kill -USR1 "$PID_SYSTEM_PROCESSES"
}

process_system_processes() {
   trap 'PROCESS_CPU_RUNNING=false' USR1

   while [[ "$PROCESS_CPU_RUNNING" == true ]]; do
      temp_file=${BASE_NAME}.dat.tmp
      total_temp_file=${BASE_NAME}.dat.tmp.total
    
      # Top 10 CPU and memory processes
      ps aux --sort=-%cpu | head -11 | tail -10 | awk '{
         # Extract PID, user, command
         pid = $2
         user = $1
         cmd = substr($0, index($0, $11))

         # Limit command to 50 characters
         if (length(cmd) > 50) {
             cmd = substr(cmd, 1, 50)
         }

         # Create output line with PID as prefix to sort
         printf "%s|%s,%s - %s\n", pid, pid, user, cmd
      }' > "$temp_file"

      ps aux --sort=-%mem | head -11 | tail -10 | awk '{
         # Extract PID, user, command
         pid = $2
         user = $1
         cmd = substr($0, index($0, $11))

         # Limit command to 50 characters
         if (length(cmd) > 50) {
             cmd = substr(cmd, 1, 50)
         }

         # Create output line with PID as prefix to sort
         printf "%s|%s,%s - %s\n", pid, pid, user, cmd
      }' >> "$temp_file"

      # Eliminate duplicates from new processes based on PID
      sort -t'|' -k1,1 -u "$temp_file" > "${temp_file}".sorted
      mv "${temp_file}.sorted" "$temp_file"; rm -f "${temp_file}.sorted"

      cat "$temp_file" >> "$total_temp_file"
        
      # Eliminate duplicates from combined file based on PID
      sort -t'|' -k1,1 -u "$total_temp_file" > "$total_temp_file".sorted
      mv "${total_temp_file}.sorted" "$total_temp_file"; rm -f "${total_temp_file}.sorted"
        
      # Move combined file to output file
      cat "$total_temp_file" | cut -d'|' -f2- > "${BASE_NAME}.dat"

      rm -f "$temp_file"

      sleep ${TIME_INTERVAL_SECONDS}
   done

   rm -f "$total_temp_file"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Monitors processes and generates metrics in NMON format.

Options:
  -b, --base-name NAME    Base name of the output file (default: "$BASE_NAME")
  -t, --time SECONDS       Total time of monitoring (default: $TIME_MONITORING_SECONDS)
  -i, --interval SECONDS   Interval between measurements (default: $TIME_INTERVAL_SECONDS)
  -h, --help                Shows this help and exits

Examples:
  $(basename "$0") -b output_file
  $(basename "$0") --base-name processes --time 600 --interval 10

EOF
  exit 0
}

# -----------------------------------------
# Process arguments
# -----------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--base-name)
      BASE_NAME="$2"
      shift 2
      ;;
    -t|--time)
      TIME_MONITORING_SECONDS="$2"
      shift 2
      ;;
    -i|--interval)
      TIME_INTERVAL_SECONDS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Error: unknown argument '$1'" >&2
      usage
      ;;
  esac
done

# Get arguments
BASE_NAME="${BASE_NAME:-processes}"
TIME_MONITORING_SECONDS="${TIME_MONITORING_SECONDS:-2880}"
TIME_INTERVAL_SECONDS="${TIME_INTERVAL_SECONDS:-30}"


echo "DEBUG: BASE_NAME: ${BASE_NAME}"
echo "DEBUG: TIME_MONITORING_SECONDS: ${TIME_MONITORING_SECONDS}"
echo "DEBUG: TIME_INTERVAL_SECONDS: ${TIME_INTERVAL_SECONDS}"

PROCESS_CPU_RUNNING=true
process_system_processes &
PID_SYSTEM_PROCESSES=$!

process_cpu_mem &

wait