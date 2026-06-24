#!/usr/bin/env python3
"""Health check tool — with configurable timeout and rate limiting."""
import argparse, json, os, socket, ssl, sys, time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
import http.client

# Config
SERVICES = {
    "backend": {"host": "localhost", "port": 8080, "path": "/health", "timeout": 5},
    "market": {"host": "localhost", "port": 8081, "path": "/health", "timeout": 5},
    "frailbox": {"host": "localhost", "port": 8082, "path": "/health", "timeout": 10},
    "frontend": {"host": "localhost", "port": 3000, "path": "/", "timeout": 5},
}
INFRA = {
    "postgresql": {"host": os.environ.get("DB_HOST","localhost"), "port": int(os.environ.get("DB_PORT","5432")), "timeout": 5},
    "redis": {"host": os.environ.get("REDIS_HOST","localhost"), "port": int(os.environ.get("REDIS_PORT","6379")), "timeout": 5},
    "kafka": {"host": os.environ.get("KAFKA_HOST","localhost"), "port": int(os.environ.get("KAFKA_PORT","9092")), "timeout": 5},
}
DISK_WARN, DISK_CRIT = 80, 90
MEM_WARN, MEM_CRIT = 80, 90

# Rate limiting
RATE_LIMIT_DELAY = 0.1

def check_http(host, port, path, timeout):
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", path)
        r = conn.getresponse()
        s, b = r.status, r.read().decode("utf-8", errors="replace")[:200]
        conn.close()
        if s == 200: return "OK", f"HTTP {s}", s
        elif s < 500: return "WARNING", f"HTTP {s}: {b[:100]}", s
        return "CRITICAL", f"HTTP {s}: {b[:100]}", s
    except Exception as e:
        return "CRITICAL", str(e), 0

def check_tcp(host, port, timeout):
    try:
        start = time.time()
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return "OK", f"Connected ({(time.time()-start)*1000:.1f}ms)", (time.time()-start)*1000
    except socket.timeout:
        return "CRITICAL", f"Timeout ({timeout}s)", 0
    except ConnectionRefusedError:
        return "CRITICAL", "Connection refused", 0
    except Exception as e:
        return "CRITICAL", str(e), 0

def check_disk(path="/"):
    try:
        s = os.statvfs(path)
        t, f = s.f_frsize*s.f_blocks, s.f_frsize*s.f_bavail
        u, p = t-f, (t-f)/t*100
        if p < DISK_WARN: return "OK", f"{p:.1f}% ({u//(1024**3)}GB/{t//(1024**3)}GB)", p
        elif p < DISK_CRIT: return "WARNING", f"{p:.1f}%", p
        return "CRITICAL", f"{p:.1f}%", p
    except: return "WARNING", "Cannot check", 0

def check_mem():
    try:
        with open("/proc/meminfo") as f:
            m = {}
            for l in f:
                p = l.split(":")
                if len(p)==2:
                    try: m[p[0].strip()] = int(p[1].strip().replace(" kB",""))*1024
                    except: pass
        t, a = m.get("MemTotal",0), m.get("MemAvailable",0)
        p = (t-a)/t*100 if t else 0
        if p < MEM_WARN: return "OK", f"{p:.1f}%", p
        elif p < MEM_CRIT: return "WARNING", f"{p:.1f}%", p
        return "CRITICAL", f"{p:.1f}%", p
    except: return "WARNING", "Cannot check", 0

def check_load():
    try:
        with open("/proc/loadavg") as f:
            load = float(f.read().strip().split()[0])
        cpus = os.cpu_count() or 1
        p = load/cpus*100
        if p < 70: return "OK", f"Load: {load}", load
        elif p < 90: return "WARNING", f"Load: {load}", load
        return "CRITICAL", f"Load: {load}", load
    except: return "WARNING", "Cannot check", 0

def run_checks(service=None, global_timeout=None, rate_limit=None):
    """Run all health checks with optional global timeout override and rate limiting."""
    results = {"timestamp": datetime.now().isoformat(), "hostname": socket.gethostname(),
               "services": {}, "infrastructure": {}, "system": {}, "overall_status": "OK"}
    all_ok = True
    delay = rate_limit if rate_limit is not None else 0

    for name, cfg in SERVICES.items():
        if service and name != service: continue
        t = global_timeout if global_timeout else cfg["timeout"]
        s, d, c = check_http(cfg["host"], cfg["port"], cfg["path"], t)
        results["services"][name] = {"status": s, "detail": d, "code": c, "endpoint": f"http://{cfg['host']}:{cfg['port']}{cfg['path']}", "timeout_used": t}
        if s == "CRITICAL": all_ok = False
        if delay: time.sleep(delay)

    for name, cfg in INFRA.items():
        if service and name != service: continue
        t = global_timeout if global_timeout else cfg["timeout"]
        s, d, lat = check_tcp(cfg["host"], cfg["port"], t)
        results["infrastructure"][name] = {"status": s, "detail": d, "endpoint": f"{cfg['host']}:{cfg['port']}", "timeout_used": t}
        if s == "CRITICAL": all_ok = False
        if delay: time.sleep(delay)

    ds, dd, dp = check_disk()
    results["system"]["disk"] = {"status": ds, "detail": dd}
    if ds == "CRITICAL": all_ok = False
    if delay: time.sleep(delay)

    ms, md, mp = check_mem()
    results["system"]["memory"] = {"status": ms, "detail": md}
    if ms == "CRITICAL": all_ok = False
    if delay: time.sleep(delay)

    ls, ld, lv = check_load()
    results["system"]["load"] = {"status": ls, "detail": ld}

    results["overall_status"] = "OK" if all_ok else "DEGRADED"
    if global_timeout: results["global_timeout"] = global_timeout
    if rate_limit: results["rate_limit_delay"] = rate_limit
    return results

def print_report(r):
    print(f"\n{'='*60}\n  HEALTH CHECK REPORT\n  Host: {r['hostname']}\n  Time: {r['timestamp']}\n  Overall: {r['overall_status']}")
    if 'global_timeout' in r: print(f"  Global timeout: {r['global_timeout']}s")
    if 'rate_limit_delay' in r: print(f"  Rate limit: {r['rate_limit_delay']}s")
    print(f"{'='*60}")
    for cat, items in [("Services",r["services"]), ("Infrastructure",r["infrastructure"]), ("System",r["system"])]:
        if items:
            print(f"\n  {cat}:")
            for n, c in items.items():
                if isinstance(c, dict) and "status" in c:
                    icon = {"OK":"✓","WARNING":"⚠","CRITICAL":"✗"}.get(c["status"],"?")
                    extra = f" (timeout:{c.get('timeout_used','?')}s)" if 'timeout_used' in c else ""
                    print(f"    {icon} {n}: {c['detail']}{extra}")
    print()

def main():
    p = argparse.ArgumentParser(description="Health check tool")
    p.add_argument("--service", "-s", help="Check specific service")
    p.add_argument("--json", "-j", action="store_true", help="JSON output")
    p.add_argument("--watch", "-w", action="store_true", help="Continuous monitoring")
    p.add_argument("--interval", "-i", type=int, default=30, help="Check interval")
    p.add_argument("--timeout", "-t", type=int, help="Global timeout override for all probes (seconds)")
    p.add_argument("--rate-limit", "-r", type=float, default=0, help="Delay between checks in seconds (prevents overwhelming services)")
    p.add_argument("--output", "-o", help="Output file")
    args = p.parse_args()

    if args.watch:
        print(f"Monitoring (interval:{args.interval}s). Ctrl+C to stop.")
        try:
            while True:
                r = run_checks(args.service, args.timeout, args.rate_limit)
                if args.json: print(json.dumps(r,indent=2))
                else: print_report(r)
                time.sleep(args.interval)
        except KeyboardInterrupt: print("\nStopped")
    else:
        r = run_checks(args.service, args.timeout, args.rate_limit)
        if args.json: print(json.dumps(r,indent=2))
        else: print_report(r)
        if args.output:
            with open(args.output,"w") as f: json.dump(r,f,indent=2)

if __name__ == "__main__":
    main()
