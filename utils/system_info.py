# system_info.py - Enhanced version with top processes support
import os
import platform
import time
from datetime import timedelta

def get_sys_info():
    """Enhanced environment detection."""
    in_proot = os.path.exists("/run/proot") or os.environ.get("PROOT_TMP_DIR")
    distro = "Termux (Native)" if not in_proot else "Proot"
    
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        distro = line.split('=')[1].strip().replace('"', '')
                        break
        except:
            pass
    elif os.path.exists("/etc/lsb-release"):
        try:
            with open("/etc/lsb-release") as f:
                for line in f:
                    if "DISTRIB_DESCRIPTION" in line:
                        distro = line.split('=')[1].strip().replace('"', '')
                        break
        except:
            pass
    
    uname = platform.uname()
    
    try:
        uptime_sec = int(time.clock_gettime(time.CLOCK_BOOTTIME))
    except:
        # Fallback for systems without CLOCK_BOOTTIME
        try:
            with open('/proc/uptime') as f:
                uptime_sec = int(float(f.read().split()[0]))
        except:
            uptime_sec = 0
    
    return {
        "os": distro,
        "kernel": uname.release,
        "arch": uname.machine,
        "uptime": str(timedelta(seconds=uptime_sec)),
        "proot": in_proot
    }

def get_load_info():
    """Get load average and process count."""
    try:
        with open('/proc/loadavg') as f:
            loads = f.read().split()
            load1, load5, load15 = loads[:3]
            running, total = loads[3].split('/')
            
            return {
                "load1": float(load1),
                "load5": float(load5),
                "load15": float(load15),
                "running": int(running),
                "total": int(total)
            }
    except:
        return None

def get_top_processes(limit=10):
    """
    Get top processes by CPU usage.
    Parses /proc to find process information.
    
    Args:
        limit: Maximum number of processes to return
    
    Returns:
        List of dicts with pid, name, cpu, mem
    """
    processes = []
    
    try:
        # Get total memory for percentage calculation
        with open('/proc/meminfo') as f:
            mem_total = 0
            for line in f:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1])
                    break
        
        # Get CPU info for time calculations
        with open('/proc/stat') as f:
            cpu_line = f.readline()
            cpu_times = [int(x) for x in cpu_line.split()[1:]]
            total_cpu_time = sum(cpu_times)
        
        # Iterate through /proc/[pid] directories
        for pid_dir in os.listdir('/proc'):
            if not pid_dir.isdigit():
                continue
            
            pid = int(pid_dir)
            
            try:
                # Get process name from /proc/[pid]/comm
                with open(f'/proc/{pid}/comm') as f:
                    name = f.read().strip()
                
                # Get CPU usage from /proc/[pid]/stat
                with open(f'/proc/{pid}/stat') as f:
                    stat_data = f.read()
                    # Handle process names with spaces/parentheses
                    stat_parts = stat_data.split(')')
                    if len(stat_parts) < 2:
                        continue
                    
                    stat_fields = stat_parts[1].split()
                    if len(stat_fields) < 22:
                        continue
                    
                    utime = int(stat_fields[11])  # User time
                    stime = int(stat_fields[12])  # System time
                    proc_time = utime + stime
                    
                    # Rough CPU percentage (simplified)
                    cpu_percent = (proc_time / total_cpu_time * 100) if total_cpu_time > 0 else 0
                
                # Get memory usage from /proc/[pid]/status
                mem_kb = 0
                with open(f'/proc/{pid}/status') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            mem_kb = int(line.split()[1])
                            break
                
                mem_percent = (mem_kb / mem_total * 100) if mem_total > 0 else 0
                
                processes.append({
                    'pid': pid,
                    'name': name,
                    'cpu': cpu_percent,
                    'mem': mem_percent
                })
            
            except (FileNotFoundError, PermissionError, ValueError):
                # Process may have terminated or we don't have permission
                continue
        
        # Sort by CPU usage (descending) and return top N
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:limit]
    
    except Exception as e:
        # Fallback: return empty list on error
        return []

def check_dependencies():
    """Warn about missing optional dependencies."""
    import shutil
    warnings = []
    
    # Check for termux-api
    if shutil.which('termux-battery-status') is None:
        warnings.append("termux-api not found (battery stats unavailable)")
    
    # Check cpufreq access
    if not os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq"):
        warnings.append("CPU frequency scaling unavailable")
    
    return warnings
