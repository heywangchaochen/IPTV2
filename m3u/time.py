import datetime

#EXTINF:-1 tvg-name="2024-12-09 19:39:39" tvg-logo="https://live.fanmingming.com/tv/2024-12-09 19:39:39.png" group-title="更新时间",2024-12-09 19:39:39

#EXTINF:-1 tvg-logo="https://gh-proxy.com/https://raw.githubusercontent.com/linitfor/epg/main/logo/2024-12-09 06:42:24.png" group-title="更新时间",2024-12-09 06:42:24


# 获取当前日期和时间
now = datetime.datetime.now()

# 格式化日期和时间为字符串
date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

# 打开文件，读取模式
with open('M3U/IPTV.m3u', 'r') as file:
    # 读取文件内容
    content = file.read()

# 打开文件，写入模式
with open('example.txt', 'w') as file:
    # 写入更新日期
    file.write('#EXTINF:-1 tvg-logo="https://gh-proxy.com/https://raw.githubusercontent.com/linitfor/epg/main/logo/ + date_time_str + .png" + " " + group-title="更新时间", + date_time_str +\n')
    # 写入原始文件内容
    file.write(content)
