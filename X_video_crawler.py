from bs4 import BeautifulSoup as bs
import requests
import re
import os
import threading
import datetime

# 时间限制
timeout = 5
# 重试次数
retry = 5
# 当前的page
cur_page = 0
# 线程的数量
num_thread = 10
# 下载的视频的质量 可选为360p 720p 1080p
quality = "720p"
# 视频的至少时间长度 单位:min
least_time = 58
# 进度计数
count = 0


def headers_make(url_str):
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36Name', 'Referer': url_str}


def get_pron_time(duration):
    if 'h' in duration:
        time = re.findall(r'\d+', duration)
        if 'm' in duration:
            time = int(time[0])*60 + int(time[1])
        else:
            time = int(time[0])*60
    elif 'm' in duration:
        time = re.findall(r'\d+', duration)
        time = int(time[0])
    else:
        time = re.findall(r'\d+', duration)
        time = int(time[0]) // 60
    return time


def thread_Handler(start, end, part, ts_url_list):
    list_len = len(ts_url_list)
    for ts_url in ts_url_list[start:end]:
        download_ts_file(ts_url, str(start // part) + ".ts", list_len)


status_ok = 1


def download_ts_file(ts_url, title, list_len):
    retry_times = 0
    global count
    global status_ok
    while retry_times < retry:
        try:
            ts_file = requests.get(
                ts_url, headers={'Connection': 'close'}, timeout=timeout)
            with open(title, 'ab') as f:
                f.write(ts_file.content)
                f.flush()
            count = count+1
            print("\r下载进度：%.2f%%" % (count/list_len*100), end='')
            status_ok = 1
            break
        except:
            # emmmmm为的是打断进度打印的时候第一次可以换行从而不挨着人家进度
            if(status_ok):
                print()
                status_ok = 0
            print(ts_url[:ts_url.find(".ts?")].split("/")[-1] +
                  " fail and retry %d" % retry_times)  # 打印是哪个ts fail
            pass
        retry_times += 1
    else:
        try:
            os.system('del /Q *.ts')  # 只要有ts文件下载失败则表示这个视频gg了所以把所有缓存的ts文件删除
            print("Failed to retrieve video from this website")
        except OSError:
            print("OSError")
            pass
        print("Failed to retrieve video from this website")


def download_porn_file(porn_url, porn_title, duration):
    pass


def txt_cut(txt, begin, end):
    return txt[txt.find(begin):txt.find(end, txt.find(begin))]


Xvideo_page = 'https://www.xvideos.com/lang/japanese/'
base_page = Xvideo_page
while cur_page < 100:
    print("we are at page " + str(cur_page+1))
    get_base = requests.get(base_page, headers=headers_make(base_page))
    soup = bs(get_base.content, 'lxml')
    for content in soup.select('.thumb-block .thumb-under'):
        video_url = 'https://www.xvideos.com' + content.a['href']  # 得到每个视频的地址
        title = content.a['title']+".mp4"  # 得到每个视频的title
        # 没有办法，它就是有的会是none，比如480p的就没有标出来
        if content.previous_sibling.span != None:
            if content.previous_sibling.span.string == quality:
                time = get_pron_time(content.select('.duration')[0].string)
                if time > least_time:
                    video_respon = requests.get(
                        video_url, headers=headers_make(video_url))  # 打开当前视频的地址
                    # 得到包含所有清晰度m3u8的指向文件
                    m3u8_url = re.findall(
                        r".setVideoHLS.*?'(.*?)'", video_respon.content.decode('utf-8'))
                    base_m3u8_url = re.findall(
                        r"(.*?)hls.m3u8", m3u8_url[0])  # 得到base_url
                    HD_m3u8_url = m3u8_url[0].replace(
                        'hls.', 'hls-'+quality+'.')  # 选取出要下载的quality的m3u8文件文件地址
                    print("begin to download %s quality: %s video duration:%d min" % (
                        title, quality, time))
                    time_start = datetime.datetime.now().replace(microsecond=0)
                    HD_m3u8_respon = requests.get(
                        HD_m3u8_url, headers=headers_make(HD_m3u8_url))  # 打开HD的m3u8文件地址
                    ts_url_list = []
                    for line in HD_m3u8_respon.content.decode('utf-8').split('\n'):
                        if '.ts' in line:  # 逐行把ts地址拿出来
                            ts_url = base_m3u8_url[0] + line
                            ts_url_list.append(ts_url)  # 并放到ts_url_list中
                    file_size = len(ts_url_list)
                    if file_size < num_thread:
                        num_thread = file_size
                    else:
                        num_thread = 10
                    part = file_size // num_thread  # 如果不能整除，最后一块应该多几个字节
                    for i in range(num_thread):
                        start = part * i
                        if i == num_thread - 1:   # 最后一块
                            end = file_size
                        else:
                            end = start + part

                        t = threading.Thread(target=thread_Handler, kwargs={
                                             'start': start, 'end': end, 'part': part, 'ts_url_list': ts_url_list})
                        t.setDaemon(True)
                        t.start()

                    # 等待所有线程下载完成
                    main_thread = threading.current_thread()
                    for t in threading.enumerate():
                        if t is main_thread:
                            continue
                        t.join()
                    print('%s 下载完成' % title)
                    count = 0
                    shell_str = [
                        str(each)+".ts" for each in list(range(num_thread))]
                    shell_str = '+'.join(shell_str)
                    shell_str = 'copy /b ' + shell_str + ' ' + \
                        title.replace(' ', '').replace("\u3000", "")
                    os.system(shell_str)
                    os.system('del /Q *.ts')
                    time_end = datetime.datetime.now().replace(microsecond=0)
                    print("用时: %s" % (str(time_end-time_start)))

    cur_page += 1
    base_page = Xvideo_page + str(cur_page)
print("done")
