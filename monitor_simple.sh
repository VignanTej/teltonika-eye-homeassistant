#!/bin/bash

# Simple Continuous Monitoring Script for Teltonika EYE Sensors
# Optimized for temperature and humidity monitoring

# Configuration
SCAN_DURATION=5        # Seconds per scan cycle
SCAN_INTERVAL=30       # Seconds between scans
OUTPUT_FILE="sensor_readings.json"
LOG_FILE="monitor.log"

# Create output directory if it doesn't exist
mkdir -p "$(dirname "$OUTPUT_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to handle cleanup on exit
cleanup() {
    log_message "Monitoring stopped by user"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

log_message "Starting continuous monitoring..."
log_message "Scan duration: ${SCAN_DURATION}s, Interval: ${SCAN_INTERVAL}s"
log_message "Output file: $OUTPUT_FILE"
log_message "Log file: $LOG_FILE"

# Initialize counters
cycle_count=0
total_readings=0

while true; do
    cycle_count=$((cycle_count + 1))
    
    log_message "Starting scan cycle $cycle_count"
    
    # Run scanner and capture output
    scan_output=$(python3 teltonika_eye_scanner.py --duration "$SCAN_DURATION" 2>/dev/null)
    
    # Count readings in this cycle
    if [ -n "$scan_output" ]; then
        cycle_readings=$(echo "$scan_output" | wc -l)
        total_readings=$((total_readings + cycle_readings))
        
        # Append to output file
        echo "$scan_output" >> "$OUTPUT_FILE"
        
        log_message "Cycle $cycle_count completed: $cycle_readings sensors found (total: $total_readings)"
    else
        log_message "Cycle $cycle_count completed: no sensors found"
    fi
    
    # Print status every 10 cycles (5 minutes with 30s intervals)
    if [ $((cycle_count % 10)) -eq 0 ]; then
        runtime=$((cycle_count * SCAN_INTERVAL))
        log_message "Status: $cycle_count cycles, $total_readings total readings, ${runtime}s runtime"
    fi
    
    # Wait for next cycle
    sleep "$SCAN_INTERVAL"
done