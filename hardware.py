# hardware.py - Enhanced version with disk I/O and swap support
import os
import subprocess
import json
from utils import get_state

def get_cpu_data():
    """Enhanced CPU monitoring with fallback methods."""
    cores = []
    path = "/sys/devices/system/cpu/"
    
    # Try frequency-based first
    try:
        cpu_dirs = sorted([d for d in os.listdir(path) if d.startswith("cpu") and d[3:].isdigit()])
        for cpu in cpu_dirs:
            try:
                with open(f"{path}{cpu}/cpufreq/scaling_cur_freq") as f:
                    cur = int(f.read().strip())
                with open(f"{path}{cpu}/cpufreq/cpuinfo_max_freq") as f:
                    max_f = int(f.read().strip())
                usage = (cur / max_f) * 100
                cores.append({"id": cpu, "cur": cur//1000, "max": max_f//1000, "usage": usage})
            except:
                continue
    except:
        pass
    
    # Fallback: parse /proc/stat for per-core CPU percentage
    if not cores:
        try:
            cpu_stat_state = get_state()["cpu"]
            with open('/proc/stat') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith('cpu') and not line.startswith('cpu '):
                    parts = line.split()
                    cpu_id = parts[0]
                    fields = [int(x) for x in parts[1:]]
                    total = sum(fields)
                    idle = fields[3] if len(fields) > 3 else 0
                    
                    # Calculate usage based on delta from previous reading
                    key = f"{cpu_id}_total"
                    key_idle = f"{cpu_id}_idle"
                    
                    if key in cpu_stat_state:
                        total_delta = total - cpu_stat_state[key]
                        idle_delta = idle - cpu_stat_state[key_idle]
                        usage = 100.0 * (1.0 - idle_delta / total_delta) if total_delta > 0 else 0
                    else:
                        usage = 0
                    
                    cpu_stat_state[key] = total
                    cpu_stat_state[key_idle] = idle
                    
                    cores.append({"id": cpu_id, "cur": 0, "max": 0, "usage": usage})
        except:
            pass
    
    return cores

def get_temps():
    """Read SoC temperature zones."""
    temps = []
    try:
        thermal_path = "/sys/class/thermal/"
        zones = sorted([z for z in os.listdir(thermal_path) if z.startswith("thermal_zone")])
        
        for zone in zones[:4]:  # Limit to first 4
            try:
                with open(f"{thermal_path}{zone}/temp") as f:
                    temp = int(f.read().strip()) / 1000
                with open(f"{thermal_path}{zone}/type") as f:
                    name = f.read().strip()
                
                # Only add if temperature is reasonable (not 0 or error values)
                if 0 < temp < 150:
                    temps.append({"name": name, "temp": temp})
            except:
                continue
    except:
        pass
    
    return temps

def get_battery():
    """Uses Termux API if available."""
    try:
        result = subprocess.run(['termux-battery-status'],
                                capture_output=True, text=True, timeout=1)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "level": data.get("percentage", 0),
                "status": data.get("status", "Unknown"),
                "temp": data.get("temperature", 0),
                "health": data.get("health", "Unknown")
            }
    except:
        pass
    
    return None

def get_mem():
    """Reads RAM usage from /proc/meminfo with swap support."""
    try:
        with open('/proc/meminfo') as f:
            m = {l.split(':')[0]: int(l.split()[1]) for l in f if ':' in l}
        
        total = m['MemTotal'] / 1024
        avail = m.get('MemAvailable', m['MemFree'] + m.get('Cached', 0)) / 1024
        used = total - avail
        buffers = m.get('Buffers', 0) / 1024
        cached = m.get('Cached', 0) / 1024
        
        # Swap information
        swap_total = m.get('SwapTotal', 0) / 1024
        swap_free = m.get('SwapFree', 0) / 1024
        swap_used = swap_total - swap_free
        
        result = {
            "used": used,
            "total": total,
            "buffers": buffers,
            "cached": cached,
            "percent": (used / total) * 100 if total > 0 else 0
        }
        
        if swap_total > 0:
            result["swap_total"] = swap_total
            result["swap_used"] = swap_used
            result["swap_free"] = swap_free
        
        return result
    except:
        return {"used": 0, "total": 1, "buffers": 0, "cached": 0, "percent": 0}

def get_storage():
    """Reads disk usage from the root filesystem."""
    try:
        st = os.statvfs('/')
        total = (st.f_blocks * st.f_frsize) / (1024**3)
        free = (st.f_bavail * st.f_frsize) / (1024**3)
        used = total - free
        
        return {
            "used": used,
            "total": total,
            "percent": (used / total) * 100 if total > 0 else 0
        }
    except:
        return {"used": 0, "total": 1, "percent": 0}

def get_disk_io():
    """
    Get disk I/O statistics from /proc/diskstats.
    Returns read/write speeds in MB/s.
    """
    try:
        disk_state = get_state()["disk_io"]
        
        # Read diskstats
        total_read = 0
        total_write = 0
        
        with open('/proc/diskstats') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 14:
                    # Skip loop and ram devices
                    device_name = parts[2]
                    if device_name.startswith('loop') or device_name.startswith('ram'):
                        continue
                    
                    # Sectors read (field 5), sectors written (field 9)
                    # Each sector is typically 512 bytes
                    read_sectors = int(parts[5])
                    write_sectors = int(parts[9])
                    
                    total_read += read_sectors * 512
                    total_write += write_sectors * 512
        
        # Calculate speed
        import time
        now = time.time()
        dt = now - disk_state["time"]
        
        if dt > 0:
            read_speed = (total_read - disk_state["read"]) / dt / (1024**2)  # MB/s
            write_speed = (total_write - disk_state["write"]) / dt / (1024**2)  # MB/s
            
            disk_state.update({
                "read": total_read,
                "write": total_write,
                "time": now
            })
            
            return {
                "read_speed": max(0, read_speed),
                "write_speed": max(0, write_speed)
            }
        
        return None
    except:
        return None
