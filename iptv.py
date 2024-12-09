import logging
import os
import re
import time
from hashlib import md5
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from datetime import datetime

import requests

from iptv.config import OUTPUT_DIR

logger = logging.getLogger(__name__)

IPTV_URL = "https://gh-proxy.com/https://raw.githubusercontent.com/heywangchaochen/IPTV2/refs/heads/main/fanmingming_ipv6.m3u"
M3U_DIR = "m3u"
TXT_DIR = "txt"
SALT = os.getenv("SALT", "")
PROXY_URL = os.getenv("PROXY_URL", "")


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def write_to_file(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")


def extract_ids(url):
    match = re.search(r"/([^/]+)/([^/]+)\.[^/]+$", url)
    return match.groups() if match else (None, None)


def get_sign_url(url):
    if PROXY_URL:
        url = url.replace("https://127.0.0.1:8080", PROXY_URL)

    channel_id, video_id = extract_ids(url)
    if not channel_id or not video_id:
        raise ValueError("Invalid URL format")

    timestamp = str(int(time.time()))
    key = md5(f"{channel_id}{video_id}{timestamp}{SALT}".encode("utf-8")).hexdigest()

    parsed_url = urlparse(url)
    query = dict(parse_qsl(parsed_url.query))
    query.update({"t": timestamp, "key": key})

    return urlunparse(parsed_url._replace(query=urlencode(query)))


def txt_to_m3u(content):
    result = ""
    genre = ""

    for line in content.split("\n"):
        line = line.strip()
        if "," not in line:
            continue

        channel_name, channel_url = line.split(",", 1)
        if channel_url == "#genre#":
            genre = channel_name
        else:
            if "127.0.0.1:8080" in channel_url:
                channel_url = get_sign_url(channel_url)

            result += (
                f'#EXTINF:-1 tvg-logo="https://ghp.ci/https://raw.githubusercontent.com/linitfor/epg/main/logo/{channel_name}.png" '
                f'group-title="{genre}",{channel_name}\n{channel_url}\n'
            )

    return result


def m3u_to_txt(m3u_content):
    lines = m3u_content.strip().split("\n")[1:]
    output_dict = {}
    group_name = ""

    url_pattern = re.compile(r'\b(?:http|https|rtmp)://[^\s]+', re.IGNORECASE)

    for line in lines:
        if line.startswith("#EXTINF"):
            group_name = line.split('group-title="')[1].split('"')[0]
            channel_name = line.split(",")[-1]
        elif url_pattern.match(line):
            channel_link = line
            output_dict.setdefault(group_name, []).append(f"{channel_name},{channel_link}")

    output_lines = [f"{group},#genre#\n" + "\n".join(links) for group, links in output_dict.items()]
    return "\n".join(output_lines)


def main():
    os.makedirs(M3U_DIR, exist_ok=True)
    os.makedirs(TXT_DIR, exist_ok=True)

    update_local_iptv_txt()

    # iptv_response = requests.get(IPTV_URL)
    # m3u_content = iptv_response.text

    # write_to_file(os.path.join(M3U_DIR, "ipv6.m3u"), m3u_content)

    # m3u_content = read_file_content(os.path.join(M3U_DIR, "ipv6.m3u"))

    live_m3u_content = '#EXTM3U\n'

    write_to_file(os.path.join(M3U_DIR, 'Live.m3u'), live_m3u_content)
    logger.info("Successfully merged and saved Live.m3u file")


    playlists = {
        "TIME": file_to_m3u("TIME.txt"),
        "CCTV": file_to_m3u("CCTV.txt"),
        "CNTV": file_to_m3u("CNTV.txt"),
        "Shuzi": file_to_m3u("Shuzi.txt"),
        "NewTV": file_to_m3u("NewTV.txt"),
        "iHOT": file_to_m3u("iHOT.txt"),
        "SITV": file_to_m3u("SITV.txt"),
        "Movie": file_to_m3u("Movie.txt"),
        "Sport": file_to_m3u("Sport.txt"),
        "HK": file_to_m3u("hk.txt"),
        "Local": file_to_m3u("Local.txt"),
    }

    iptv_m3u = "".join(playlists.values()) + '\n'
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_m3u = txt_to_m3u(f"更新时间,#genre#\n{update_time},\n")

    live_m3u = '\n'.join(live_m3u_content.split('\n')[1:]) + '\n'

    write_m3u_to_file(os.path.join(M3U_DIR, "IPTV.m3u"), update_m3u + iptv_m3u)

    iptv_txt = m3u_to_txt(read_file_content(os.path.join(M3U_DIR, "IPTV.m3u")))
    write_to_file(os.path.join(TXT_DIR, "IPTV.txt"), update_m3u + iptv_txt)


def file_to_m3u(file_name):
    file_path = os.path.join(TXT_DIR, file_name)
    content = read_file_content(file_path)
    return txt_to_m3u(content)


def write_m3u_to_file(file_path, content):
    header = (
        '#EXTM3U x-tvg-url="https://gh-proxy.com/https://raw.githubusercontent.com/heywangchaochen/IPTV2/refs/heads/main/e.xml"\n'
    )
    write_to_file(file_path, header + content.strip())

def update_local_iptv_txt():
    logging.info("Starting to update local IPTV txt files.")

    try:
        # Fetch and convert IPTV M3U content to TXT format
        iptv_response = requests.get(IPTV_URL)
        iptv_response.raise_for_status()
        iptv_m3u_content = iptv_response.text
        iptv_txt_content = m3u_to_txt(iptv_m3u_content)
        logging.info("Successfully fetched and converted IPTV content.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching IPTV content: {e}")
        return

    def update_line(channel_name, current_url, suffix, suffix_type):
        province = suffix[1:3]
        isp = suffix[3:5]
        file_name = os.path.join(OUTPUT_DIR, suffix_type, f"中国{isp}", f"{province}.txt")
        try:
            udpxy_content = read_file_content(file_name)
        except FileNotFoundError:
            logging.error(f"File not found: {file_name}")
            return None

        pattern = re.compile(rf"^{re.escape(channel_name)},(http[^\s]+)", re.MULTILINE)
        match = pattern.search(udpxy_content)
        if match:
            new_url = match.group(1)
            logging.info(f"Updating URL for {channel_name}: {new_url}")
            return f"{channel_name},{new_url}${province}{isp}{suffix[-2:]}\n"
        return None

    for file_name in os.listdir(OUTPUT_DIR):
        if file_name.endswith('.txt') and file_name not in ['IPTV.txt']:
            file_path = os.path.join(OUTPUT_DIR, file_name)
            logging.info(f"Processing file: {file_name}")

            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    lines = file.readlines()
                logging.info(f"Successfully read {file_name}.")
            except OSError as e:
                logging.error(f"Error reading file {file_name}: {e}")
                continue

            updated_lines = []
            for line in lines:
                parts = line.strip().split(',', 1)
                if len(parts) == 2:
                    channel_name, current_url = parts
                    updated_line = None

                    if current_url.endswith('酒店'):
                        suffix_match = re.search(r'\$(.+)酒店$', current_url)
                        if suffix_match:
                            updated_line = update_line(channel_name, current_url, suffix_match.group(0), "hotel")

                    elif current_url.endswith('组播'):
                        suffix_match = re.search(r'\$(.+)组播$', current_url)
                        if suffix_match:
                            updated_line = update_line(channel_name, current_url, suffix_match.group(0), "udpxy")

                    elif file_name in ['CCTV.txt', 'CNTV.txt', 'Shuzi.txt', 'NewTV.txt']:
                        pattern = re.compile(rf"^{re.escape(channel_name)},(http[^\s]+)", re.MULTILINE)
                        match = pattern.search(iptv_txt_content)
                        if match:
                            new_url = match.group(1)
                            logging.info(f"Updating URL for {channel_name}: {new_url}")
                            updated_line = f"{channel_name},{new_url}\n"

                    if updated_line:
                        line = updated_line

                updated_lines.append(line)

            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.writelines(updated_lines)
                logging.info(f"Successfully updated {file_name}.")
            except OSError as e:
                logging.error(f"Error writing to file {file_name}: {e}")

    logging.info("Finished updating all files.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    main()
