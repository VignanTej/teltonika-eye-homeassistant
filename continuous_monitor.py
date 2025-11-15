#!/usr/bin/env python3
"""
Continuous Teltonika EYE Sensor Monitor

Designed for long-term temperature and humidity monitoring with optimal
scan intervals, error recovery, and data logging capabilities.
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from teltonika_eye_scanner import TeltonikaEYEScanner


class ContinuousMonitor:
    """Continuous monitoring system for Teltonika EYE sensors."""
    
    def __init__(
        self,
        scan_duration: float = 5.0,
        scan_interval: float = 30.0,
        output_file: Optional[str] = None,
        max_log_size_mb: int = 100,
        sensor_timeout_minutes: int = 10
    ):
        self.scan_duration = scan_duration
        self.scan_interval = scan_interval
        self.output_file = output_file
        self.max_log_size_bytes = max_log_size_mb * 1024 * 1024
        self.sensor_timeout = timedelta(minutes=sensor_timeout_minutes)
        
        self.logger = logging.getLogger(__name__)
        self.running = True
        self.scanner = TeltonikaEYEScanner(scan_duration=scan_duration)
        
        # Track sensor states
        self.known_sensors: Dict[str, Dict] = {}
        self.last_seen: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            "scan_cycles": 0,
            "total_readings": 0,
            "unique_sensors": 0,
            "start_time": datetime.now(),
            "errors": 0
        }
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _setup_logging(self, log_file: Optional[str] = None):
        """Setup logging with rotation."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if log_file:
            from logging.handlers import RotatingFileHandler
            handler = RotatingFileHandler(
                log_file, 
                maxBytes=self.max_log_size_bytes, 
                backupCount=5
            )
            handler.setFormatter(logging.Formatter(log_format))
            self.logger.addHandler(handler)
        
        # Also log to stderr for monitoring
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(console_handler)
        
        self.logger.setLevel(logging.INFO)
    
    def _rotate_output_file(self):
        """Rotate output file if it gets too large."""
        if not self.output_file or not Path(self.output_file).exists():
            return
        
        file_size = Path(self.output_file).stat().st_size
        if file_size > self.max_log_size_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.output_file}.{timestamp}"
            Path(self.output_file).rename(backup_name)
            self.logger.info(f"Rotated output file to {backup_name}")
    
    def _update_sensor_tracking(self, device_address: str, sensor_data: Dict):
        """Update sensor tracking and statistics."""
        now = datetime.now()
        
        # Update last seen time
        self.last_seen[device_address] = now
        
        # Track unique sensors
        if device_address not in self.known_sensors:
            self.known_sensors[device_address] = {
                "first_seen": now,
                "device_name": sensor_data.get("device", {}).get("name", "Unknown"),
                "reading_count": 0
            }
            self.stats["unique_sensors"] += 1
            self.logger.info(f"New sensor discovered: {device_address}")
        
        # Update reading count
        self.known_sensors[device_address]["reading_count"] += 1
        self.stats["total_readings"] += 1
    
    def _check_sensor_timeouts(self):
        """Check for sensors that haven't been seen recently."""
        now = datetime.now()
        timeout_sensors = []
        
        for address, last_time in self.last_seen.items():
            if now - last_time > self.sensor_timeout:
                timeout_sensors.append(address)
        
        for address in timeout_sensors:
            sensor_info = self.known_sensors.get(address, {})
            device_name = sensor_info.get("device_name", "Unknown")
            self.logger.warning(
                f"Sensor timeout: {address} ({device_name}) - "
                f"last seen {(now - self.last_seen[address]).total_seconds():.0f}s ago"
            )
    
    def _output_reading(self, reading: Dict):
        """Output sensor reading to file and/or stdout."""
        json_line = json.dumps(reading, separators=(',', ':'))
        
        # Always output to stdout for piping
        print(json_line)
        sys.stdout.flush()
        
        # Also write to file if specified
        if self.output_file:
            try:
                with open(self.output_file, 'a') as f:
                    f.write(json_line + '\n')
                    f.flush()
            except Exception as e:
                self.logger.error(f"Failed to write to output file: {e}")
    
    def _print_status(self):
        """Print monitoring status."""
        runtime = datetime.now() - self.stats["start_time"]
        
        status = {
            "status": "monitoring",
            "runtime_seconds": int(runtime.total_seconds()),
            "scan_cycles": self.stats["scan_cycles"],
            "total_readings": self.stats["total_readings"],
            "unique_sensors": self.stats["unique_sensors"],
            "active_sensors": len([
                addr for addr, last_time in self.last_seen.items()
                if datetime.now() - last_time < self.sensor_timeout
            ]),
            "errors": self.stats["errors"],
            "next_scan_in": max(0, int(self.scan_interval - (time.time() % self.scan_interval)))
        }
        
        self.logger.info(f"Status: {json.dumps(status)}")
    
    async def _scan_cycle(self):
        """Perform a single scan cycle."""
        try:
            self.logger.debug(f"Starting scan cycle {self.stats['scan_cycles'] + 1}")
            
            # Perform scan
            devices = await self.scanner.scan()
            
            # Process results
            for device_data in devices:
                device_address = device_data["device"]["address"]
                
                # Update tracking
                self._update_sensor_tracking(device_address, device_data)
                
                # Output reading
                self._output_reading(device_data)
            
            self.stats["scan_cycles"] += 1
            
            if devices:
                self.logger.debug(f"Scan cycle completed: {len(devices)} sensors found")
            
        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Error during scan cycle: {e}")
    
    async def run(self):
        """Run continuous monitoring."""
        self.logger.info("Starting continuous monitoring...")
        self.logger.info(f"Scan duration: {self.scan_duration}s, Interval: {self.scan_interval}s")
        
        last_status_time = time.time()
        status_interval = 300  # Print status every 5 minutes
        
        while self.running:
            cycle_start = time.time()
            
            # Perform scan cycle
            await self._scan_cycle()
            
            # Check for sensor timeouts
            self._check_sensor_timeouts()
            
            # Rotate output file if needed
            self._rotate_output_file()
            
            # Print status periodically
            if time.time() - last_status_time > status_interval:
                self._print_status()
                last_status_time = time.time()
            
            # Calculate sleep time to maintain interval
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, self.scan_interval - cycle_duration)
            
            if sleep_time > 0:
                self.logger.debug(f"Sleeping for {sleep_time:.1f}s until next scan")
                await asyncio.sleep(sleep_time)
            else:
                self.logger.warning(f"Scan cycle took {cycle_duration:.1f}s, longer than interval {self.scan_interval}s")
        
        # Print final statistics
        self._print_final_stats()
    
    def _print_final_stats(self):
        """Print final monitoring statistics."""
        runtime = datetime.now() - self.stats["start_time"]
        
        final_stats = {
            "monitoring_completed": True,
            "total_runtime_seconds": int(runtime.total_seconds()),
            "total_scan_cycles": self.stats["scan_cycles"],
            "total_readings": self.stats["total_readings"],
            "unique_sensors_discovered": self.stats["unique_sensors"],
            "total_errors": self.stats["errors"],
            "average_readings_per_cycle": (
                self.stats["total_readings"] / max(1, self.stats["scan_cycles"])
            )
        }
        
        self.logger.info("Monitoring session completed")
        self.logger.info(f"Final statistics: {json.dumps(final_stats, indent=2)}")


async def main():
    """Main function to run continuous monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Continuous monitoring of Teltonika EYE sensors"
    )
    parser.add_argument(
        "--scan-duration", "-d",
        type=float,
        default=5.0,
        help="Duration of each scan cycle in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--scan-interval", "-i",
        type=float,
        default=30.0,
        help="Interval between scan cycles in seconds (default: 30.0)"
    )
    parser.add_argument(
        "--output-file", "-o",
        type=str,
        help="Output file for sensor readings (default: stdout only)"
    )
    parser.add_argument(
        "--log-file", "-l",
        type=str,
        help="Log file for monitoring messages (default: stderr only)"
    )
    parser.add_argument(
        "--max-log-size",
        type=int,
        default=100,
        help="Maximum log file size in MB before rotation (default: 100)"
    )
    parser.add_argument(
        "--sensor-timeout",
        type=int,
        default=10,
        help="Minutes before considering a sensor offline (default: 10)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = ContinuousMonitor(
        scan_duration=args.scan_duration,
        scan_interval=args.scan_interval,
        output_file=args.output_file,
        max_log_size_mb=args.max_log_size,
        sensor_timeout_minutes=args.sensor_timeout
    )
    
    # Setup logging
    monitor._setup_logging(args.log_file)
    
    if args.verbose:
        monitor.logger.setLevel(logging.DEBUG)
    
    # Run monitoring
    try:
        await monitor.run()
    except KeyboardInterrupt:
        monitor.logger.info("Monitoring stopped by user")
    except Exception as e:
        monitor.logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())