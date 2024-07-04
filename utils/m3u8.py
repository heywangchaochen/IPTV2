from urllib.parse import urlparse
import os

def get_m3u8_content(play_url: str, m3u8_content: str) -> str:
    parsed_url = urlparse(play_url)
    port = parsed_url.port if parsed_url.port else (443 if parsed_url.scheme == 'https' else 80)
    domain_port = f"{parsed_url.hostname}:{port}"
    path = "/".join(parsed_url.path.split('/')[:-1])

    lines = m3u8_content.strip().splitlines()
    modified_lines = []

    for line in lines:
        if line and not line.startswith("#") and not urlparse(line).netloc:
            modified_line = f"{os.getenv('PROXY_URL', '')}/data/{domain_port}{path}/{line}"
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)

    return "\n".join(modified_lines)