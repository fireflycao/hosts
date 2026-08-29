import json
import re
import urllib.request
from datetime import datetime, timezone

# 核心域名列表
DOMAINS = [
    "registry-1.docker.io",
    "auth.docker.io",
    "production.cloudflare.docker.com",
    "cloudflare.docker.com",
    "d28j15727ai5wa.cloudfront.net",
    "hub.docker.com",
]

# 社区上游备用源
UPSTREAM_SOURCES = [
    "https://raw.githubusercontent.com/yeyingorg/docker-hosts/main/hosts",
    "https://raw.githubusercontent.com/mianwo/Docker-Hosts/main/hosts",
]


def fetch_upstream(url):
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Fetch {url} failed: {e}")
        return ""


def query_doh_ip(domain):
    """保底机制：通过 Cloudflare DNS-over-HTTPS 提取真实 IP"""
    url = f"https://1.1.1.1/dns-query?name={domain}&type=A"
    req = urllib.request.Request(
        url, headers={"Accept": "application/dns-json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("Answer", []):
                if item.get("type") == 1:
                    return item.get("data")
    except Exception as e:
        print(f"DoH query for {domain} failed: {e}")
    return None


def main():
    merged_records = {}

    # 1. 尝试从社区上游抓取
    for source in UPSTREAM_SOURCES:
        content = fetch_upstream(source)
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = re.split(r"\s+", line)
            if len(parts) >= 2:
                ip, domain = parts[0], parts[1]
                if domain in DOMAINS:
                    merged_records[domain] = ip

    # 2. 保底处理：未从上游获取到的域名，由 DoH 强行解析补全
    for domain in DOMAINS:
        if domain not in merged_records or not merged_records[domain]:
            doh_ip = query_doh_ip(domain)
            if doh_ip:
                merged_records[domain] = doh_ip

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    output_lines = [
        "# ==========================================",
        "# Auto Generated Docker Hosts Source",
        f"# Updated At: {now_utc}",
        "# Source: Aggregated Community Repos + Cloudflare DoH Backup",
        "# ==========================================\n",
    ]

    for domain, ip in merged_records.items():
        output_lines.append(f"{ip:<18} {domain}")

    output_lines.append("\n# Docker Hosts End")

    with open("hosts_Docker", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"Done. Written {len(merged_records)} records to hosts_Docker.")


if __name__ == "__main__":
    main()
