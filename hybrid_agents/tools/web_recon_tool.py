import subprocess
import os
import requests
from urllib.parse import urlparse

def parse_target(target):
    parsed = urlparse(target)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path.split('/')[0]
    base_url = f"{scheme}://{netloc}"
    domain_or_ip = netloc.split(":")[0]
    return base_url, domain_or_ip

def whois_tool(target):
    """Get WHOIS information for a domain or IP."""
    base_url, domain = parse_target(target)

    print(f"[DEBUG] WHOIS TOOL - Target received: {target}")
    print(f"[DEBUG] WHOIS TOOL - Parsed domain/IP: {domain}")

    output_dir = f"recon_output/{domain}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "whois.txt")

    try:
        print(f"[DEBUG] WHOIS TOOL - Running: whois {domain}")
        with open(output_file, "w") as f_out:
            subprocess.run(["whois", domain], stdout=f_out, stderr=subprocess.STDOUT, timeout=60, check=True)

        print(f"[DEBUG] WHOIS TOOL - Output written to: {output_file}")
        with open(output_file) as f:
            content = f.read()
            print(f"[DEBUG] WHOIS TOOL - Output content length: {len(content)}")
            return f"WHOIS RESULT\n{content}"
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] WHOIS TOOL - Process error: {e}")
        return f"Whois subprocess error: {e}"
    except FileNotFoundError as e:
        print(f"[ERROR] WHOIS TOOL - 'whois' not found in PATH: {e}")
        return f"Whois not installed: {e}"
    except Exception as e:
        print(f"[ERROR] WHOIS TOOL - Unexpected error: {e}")
        return f"Whois unknown error: {e}"


def dnsx_tool(target):
    """Enumerate DNS records using DNSX."""
    _, domain = parse_target(target)
    output_dir = f"recon_output/{domain}"
    os.makedirs(output_dir, exist_ok=True)
    input_file = os.path.join(output_dir, "subfinder.txt")
    output_file = os.path.join(output_dir, "dnsx.txt")
    if not os.path.exists(input_file):
        return "subfinder.txt not found. Run subfinder_tool first."
    try:
        subprocess.run(["dnsx", "-l", input_file, "-a", "-resp-only", "-o", output_file], timeout=120, check=True)
        with open(output_file) as f:
            return f"DNSX RESULT\n{f.read()}"
    except Exception as e:
        return f"dnsx error: {e}"


def whatweb_tool(target):
    """Fingerprint web technologies using WhatWeb."""
    _, domain = parse_target(target)
    output_dir = f"recon_output/{domain}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "whatweb.txt")
    try:
        subprocess.run(["whatweb", target, f"--log-verbose={output_file}"], timeout=60, check=True)
        with open(output_file) as f:
            return f"WHATWEB RESULT\n{f.read()}"
    except Exception as e:
        return f"WhatWeb error: {e}"

def sslscan_tool(target):
    """Scan SSL/TLS configuration using SSLScan."""
    _, domain = parse_target(target)
    output_dir = f"recon_output/{domain}"
    os.makedirs(output_dir, exist_ok=True)
    if not target.startswith("https"):
        return "Target is not HTTPS, skip SSLScan."
    output_file = os.path.join(output_dir, "sslscan.txt")
    try:
        subprocess.run(["sslscan", domain], stdout=open(output_file, "w"), timeout=120, check=True)
        with open(output_file) as f:
            return f"SSLSCAN RESULT\n{f.read()}"
    except Exception as e:
        return f"SSLScan error: {e}"


def nuclei_tool(target):
    """Scan for vulnerabilities using Nuclei."""
    _, domain = parse_target(target)
    output_dir = f"recon_output/{domain}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "nuclei.jsonl")
    try:
        subprocess.run(["nuclei", "-u", target, "-c", "100", "-rate-limit", "300", "-timeout", "10", "-jsonl", "-o", output_file], timeout=300, check=True)
        if os.path.exists(output_file):
            with open(output_file) as f:
                return f"NUCLEI RESULT\n{f.read()}"
        else:
            return "No nuclei findings."
    except Exception as e:
        return f"Nuclei error: {e}"

def dirsearch_tool(target):
    """Discover directories and files with Dirsearch."""
    _, domain = parse_target(target)
    output_dir = f"recon_output/{domain}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "dirsearch.txt")
    try:
        subprocess.run(["dirsearch", "-u", target, "-e", "*", "--threads", "100", "-o", output_file, "--timeout", "30", "-i", "200"], timeout=300, check=True)
        found = []
        if os.path.exists(output_file):
            with open(output_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or "http" not in line:
                        continue
                    found.append(line)
        if found:
            return "DIRSEARCH RESULT\n" + "\n".join(found)
        else:
            return "No directories/files found."
    except Exception as e:
        return f"Dirsearch error: {e}"


def http_fetch_tool(target):
    """Send a GET request and return status, content-type, and first 1000 characters."""
    try:
        r = requests.get(target, timeout=10)
        ct = r.headers.get("Content-Type", "")
        if "text" in ct or "json" in ct:
            body = r.text[:1000]
        else:
            body = "[Binary or non-text content]"
        return f"{r.status_code} | {ct}\n{body}"
    except Exception as e:
        return f"HTTP fetch error: {e}"
