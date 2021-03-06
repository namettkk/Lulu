#!/usr/bin/env python

import re
import json
import time
import hashlib


from lulu.util import log
from lulu.common import (
    match1,
    print_info,
    get_content,
    download_urls,
    download_url_ffmpeg,
    general_m3u8_extractor,
    playlist_not_supported,
)


__all__ = ['douyutv_download']
site_info = '斗鱼 douyu.com'


def douyutv_video_download(
    url, output_dir='.', merge=True, info_only=False, **kwargs
):
    ep = 'http://vmobile.douyu.com/video/getInfo?vid='
    patt = r'show/([0-9A-Za-z]+)'
    title_patt = r'<h1>(.+?)</h1>'

    hit = re.search(patt, url)
    if hit is None:
        log.wtf('Unknown url pattern')
    vid = hit.group(1)

    page = get_content(url)
    hit = re.search(title_patt, page)
    if hit is None:
        title = vid
    else:
        title = hit.group(1)

    meta = json.loads(get_content(ep + vid))
    if meta['error'] != 0:
        log.wtf('Error from API server')
    m3u8_url = meta['data']['video_url']
    print_info(site_info, title, 'm3u8', 0, m3u8_url=m3u8_url)
    if not info_only:
        urls = general_m3u8_extractor(m3u8_url)
        download_urls(
            urls, title, 'ts', 0, output_dir=output_dir, merge=merge, **kwargs
        )


def douyutv_download(
    url, output_dir='.', merge=True, info_only=False, **kwargs
):
    if 'v.douyu.com/show/' in url:
        douyutv_video_download(
            url, output_dir=output_dir, merge=merge, info_only=info_only,
            **kwargs
        )
        return
    url = re.sub(r'[\w.]*douyu.com', 'm.douyu.com', url)
    html = get_content(url)
    room_id_patt = r'room_id\s*:\s*(\d+),'
    room_id = match1(html, room_id_patt)
    if room_id == '0':
        room_id = url[url.rfind('/')+1:]

    api_url = 'http://www.douyutv.com/api/v1/'
    args = 'room/{}?aid=wp&client_sys=wp&time={}'.format(
        room_id, int(time.time())
    )
    auth_md5 = (args + 'zNzMV1y4EMxOHS6I5WKm').encode('utf-8')
    auth_str = hashlib.md5(auth_md5).hexdigest()
    json_request_url = '{}{}&auth={}'.format(api_url, args, auth_str)

    content = get_content(json_request_url)
    json_content = json.loads(content)
    data = json_content['data']
    server_status = json_content.get('error', 0)
    if server_status is not 0:
        raise ValueError('Server returned error: {}'.format(server_status))

    title = data.get('room_name')
    show_status = data.get('show_status')
    if show_status is not '1':
        raise ValueError('The live stream is not online! (Errno: {})'.format(
            server_status
        ))

    real_url = '{}/{}'.format(
        data.get('rtmp_url'), data.get('rtmp_live')
    )
    print_info(site_info, title, 'flv', float('inf'))
    if not info_only:
        download_url_ffmpeg(
            real_url, title, 'flv', None, output_dir=output_dir,
            merge=merge
        )


download = douyutv_download
download_playlist = playlist_not_supported(site_info)
