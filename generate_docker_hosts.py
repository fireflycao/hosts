import urllib.request
import re
from datetime import datetime, timezone

# 社区开源 Docker Hosts 上游源列表
UPSTREAM_SOURCES = [
    "https://raw.githubusercontent.com/yeyingorg/docker-hosts/main/hosts",
    "https://raw.githubusercontent.com/mianwo/Docker-Hosts/main/hosts"
]

def fetch_upstream_hosts(url):
    """抓取上游源的 hosts 内容"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"Fetch {url} failed: {e}")
        return ""

def parse_and_clean_hosts(raw_text):
    """解析并提取有效的 Docker 域名映射"""
    docker_domains = (
        'registry-1.docker.io', 'auth.docker.io', 
        'production.cloudflare.docker.com', 'cloudflare.docker.com', 
        'hub.docker.com', 'd28j15727ai5wa.cloudfront.net'
    )
    records = {}
    
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = re.split(r'\s+', line)
        if len(parts) >= 2:
            ip, domain = parts[0], parts[1]
            if domain in docker_domains:
                records[domain] = ip
    return records

def main():
    merged_records = {}
    for source in UPSTREAM_SOURCES:
        content = fetch_upstream_hosts(source)
        records = parse_and_clean_hosts(content)
        merged_records.update(records)

    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    output_lines = [
        "# ==========================================",
        "# Auto Generated Docker Hosts Source",
        f"# Updated At: {now_utc}",
        "# Source: Aggregated from Community Docker Repos",
        "# ==========================================\n"
    ]

    for domain, ip in merged_records.items():
        output_lines.append(f"{ip:<18} {domain}")

    output_lines.append("\n# Docker Hosts End")

    with open("hosts_Docker", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("hosts_Docker file generated successfully.")

if __name__ == "__main__":
    main()
