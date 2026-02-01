# hardware.py - Enhanced version with disk I/O and swap support + improved CPU usage sources

import os
import subprocess
import json
import time

from utils import get_state


def _read_int(path):
    try:
        with open(path) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _cpufreq_info(cpu_path):
    """Return (cur_khz, max_khz) if available, else (None, None)."""
    cur = _read_int(os.path.join(cpu_path, "cpufreq", "scaling_cur_freq"))
    max_f = _read_int(os.path.join(cpu_path, "cpufreq", "cpuinfo_max_freq"))
    return cur, max_f


def _cpuidle_total_time(cpu_path):
    """
    Sum cpuidle time counters for one CPU.

    Many kernels expose:
      /sys/devices/system/cpu/cpuX/cpuidle/state*/time

    Units vary (often microseconds; sometimes nanoseconds).
    Returns int summed time as reported by sysfs, or None if not available.
    """
    base = os.path.join(cpu_path, "cpuidle")
    try:
        if not os.path.isdir(base):
            return None
        total = 0
        any_state = False
        for name in os.listdir(base):
            if not name.startswith("state"):
                continue
            any_state = True
            t = _read_int(os.path.join(base, name, "time"))
            if t is not None:
                total += t
        if not any_state:
            return None
        return total if total > 0 else None
    except Exception:
        return None


def _usage_from_cpuidle(cpu_id, idle_now, now_s, cpu_state):
    """
    Convert cpuidle idle-time delta to busy%.

    We don't know if idle_now is in microseconds or nanoseconds, so try both
    denominators (dt*1e6 and dt*1e9) and pick the one that looks plausible.
    """
    idle_time = cpu_state.setdefault("cpu_idle_time", {})
    idle_t = cpu_state.setdefault("cpu_idle_t", {})

    idle_prev = idle_time.get(cpu_id)
    t_prev = idle_t.get(cpu_id)

    idle_time[cpu_id] = idle_now
    idle_t[cpu_id] = now_s

    if idle_prev is None or t_prev is None:
        return None

    dt = now_s - t_prev
    if dt <= 0:
        return None

    idle_delta = idle_now - idle_prev
    if idle_delta < 0:
        # Counter reset/wrap; ignore this sample
        return None

    den_us = dt * 1_000_000.0
    den_ns = dt * 1_000_000_000.0

    frac_us = idle_delta / den_us if den_us > 0 else 999.0
    frac_ns = idle_delta / den_ns if den_ns > 0 else 999.0

    # Choose plausible idle fraction (allowing slight slack).
    if 0.0 <= frac_us <= 1.2:
        idle_frac = frac_us
    elif 0.0 <= frac_ns <= 1.2:
        idle_frac = frac_ns
    else:
        return None

    idle_frac = max(0.0, min(1.0, idle_frac))
    usage = 100.0 * (1.0 - idle_frac)
    return max(0.0, min(100.0, usage))


def get_cpu_data():
    """
    CPU monitoring with multiple methods:
      1) /proc/stat deltas (best; true busy%) if accessible
      2) cpuidle time deltas (good estimate; works on some restricted setups)
      3) cpufreq ratio (proxy only; indicates how hard the governor is pushing)
    """
    cores = []
    base = "/sys/devices/system/cpu/"
    cpu_state = get_state()["cpu"]

    # List CPUs from sysfs
    try:
        cpu_dirs = sorted(
            [d for d in os.listdir(base) if d.startswith("cpu") and d[3:].isdigit()]
        )
    except Exception:
        cpu_dirs = []

    # 1) /proc/stat per-cpu usage (delta-based)
    proc_usage = {}
    try:
        with open("/proc/stat") as f:
            for line in f:
                if line.startswith("cpu") and not line.startswith("cpu "):
                    parts = line.split()
                    cpu_id = parts[0]  # e.g. "cpu0"
                    fields = [int(x) for x in parts[1:]]
                    total = sum(fields)
                    idle = fields[3] if len(fields) > 3 else 0

                    key_t = f"{cpu_id}_total"
                    key_i = f"{cpu_id}_idle"

                    if key_t in cpu_state and key_i in cpu_state:
                        total_delta = total - cpu_state[key_t]
                        idle_delta = idle - cpu_state[key_i]
                        usage = (
                            100.0 * (1.0 - idle_delta / total_delta)
                            if total_delta > 0
                            else 0.0
                        )
                        proc_usage[cpu_id] = max(0.0, min(100.0, usage))

                    cpu_state[key_t] = total
                    cpu_state[key_i] = idle
    except Exception:
        proc_usage = {}

    now_s = time.monotonic()

    for cpu in cpu_dirs:
        cpu_path = os.path.join(base, cpu)

        cur_khz, max_khz = _cpufreq_info(cpu_path)
        cur_mhz = (cur_khz // 1000) if cur_khz else 0
        max_mhz = (max_khz // 1000) if max_khz else 0

        usage = None
        usage_src = "unknown"

        # Prefer /proc/stat if available
        if cpu in proc_usage:
            usage = proc_usage[cpu]
            usage_src = "procstat"
        else:
            # Next best: cpuidle
            idle_now = _cpuidle_total_time(cpu_path)
            if idle_now is not None:
                u = _usage_from_cpuidle(cpu, idle_now, now_s, cpu_state)
                if u is not None:
                    usage = u
                    usage_src = "cpuidle"

        # Last resort: cpufreq ratio proxy
        if usage is None:
            if cur_khz and max_khz and max_khz > 0:
                usage = (cur_khz / max_khz) * 100.0
                usage_src = "cpufreq"
            else:
                usage = 0.0
                usage_src = "unknown"

        cores.append(
            {
                "id": cpu,
                "cur": cur_mhz,
                "max": max_mhz,
                "usage": float(usage),
                "usage_src": usage_src,
            }
        )

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
            except Exception:
                continue
    except Exception:
        pass
    return temps


def get_battery():
    """Uses Termux API if available."""
    try:
        result = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=1
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "level": data.get("percentage", 0),
                "status": data.get("status", "Unknown"),
                "temp": data.get("temperature", 0),
                "health": data.get("health", "Unknown"),
            }
    except Exception:
        pass
    return None


def get_mem():
    """Reads RAM usage from /proc/meminfo with swap support."""
    try:
        with open("/proc/meminfo") as f:
            m = {l.split(":")[0]: int(l.split()[1]) for l in f if ":" in l}

        total = m["MemTotal"] / 1024
        avail = m.get("MemAvailable", m["MemFree"] + m.get("Cached", 0)) / 1024
        used = total - avail

        buffers = m.get("Buffers", 0) / 1024
        cached = m.get("Cached", 0) / 1024

        # Swap information
        swap_total = m.get("SwapTotal", 0) / 1024
        swap_free = m.get("SwapFree", 0) / 1024
        swap_used = swap_total - swap_free

        result = {
            "used": used,
            "total": total,
            "buffers": buffers,
            "cached": cached,
            "percent": (used / total) * 100 if total > 0 else 0,
        }

        if swap_total > 0:
            result["swap_total"] = swap_total
            result["swap_used"] = swap_used
            result["swap_free"] = swap_free

        return result
    except Exception:
        return {"used": 0, "total": 1, "buffers": 0, "cached": 0, "percent": 0}


def get_storage():
    """Reads disk usage from the root filesystem."""
    try:
        st = os.statvfs("/")
        total = (st.f_blocks * st.f_frsize) / (1024**3)
        free = (st.f_bavail * st.f_frsize) / (1024**3)
        used = total - free
        return {
            "used": used,
            "total": total,
            "percent": (used / total) * 100 if total > 0 else 0,
        }
    except Exception:
        return {"used": 0, "total": 1, "percent": 0}


def get_disk_io():
    """
    Get disk I/O statistics from /proc/diskstats.
    Returns read/write speeds in MB/s.
    """
    try:
        disk_state = get_state()["disk_io"]

        total_read = 0
        total_write = 0

        with open("/proc/diskstats") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 14:
                    continue

                device_name = parts[2]
                if device_name.startswith("loop") or device_name.startswith("ram"):
                    continue

                # Field meanings vary slightly by kernel docs, but the common layout:
                # reads completed (3), reads merged (4), sectors read (5), ...
                # writes completed (7), writes merged (8), sectors written (9), ...
                read_sectors = int(parts[5])
                write_sectors = int(parts[9])

                total_read += read_sectors * 512
                total_write += write_sectors * 512

        now = time.time()
        dt = now - disk_state.get("time", now)
        if dt <= 0:
            disk_state.update({"read": total_read, "write": total_write, "time": now})
            return None

        read_speed = (total_read - disk_state.get("read", 0)) / dt / (1024**2)
        write_speed = (total_write - disk_state.get("write", 0)) / dt / (1024**2)

        disk_state.update({"read": total_read, "write": total_write, "time": now})

        return {
            "read_speed": max(0.0, read_speed),
            "write_speed": max(0.0, write_speed),
        }
    except Exception:
        return None
