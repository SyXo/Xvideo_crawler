from bs4 import BeautifulSoup as bs
import requests,re,os
import threading
import datetime
# Setting timeout
TIMEOUT = 5
# Retry times
RETRY = 3

cur_page = 0

num_thread = 10

def save(filename, contents):
	fh = open(filename, 'w', encoding='utf-8')
	fh.write(contents)
	fh.close()
	
def get_pron_time(respon):
	time=re.findall(r'"duration">(.*?)<',respon.content.decode('utf-8'))
	if 'h' in time[0]:
		time=re.findall(r'\d+',time[0])
		if 'm' in time[0]:
			time = int(time[0])*60 + int(time[1])
		else:
			time = int(time[0])*60
	elif 'm' in time[0]:
		time=re.findall(r'\d+',time[0])
		time = int(time[0])
	else:
		time=re.findall(r'\d+',time[0])
		time = int(time[0]) // 60
	return time

def Handler(start, end, part, url, filename):
	for i in filename[start:end]:
		download_porn_file(i,str(start // part) + ".ts")

def download_porn_file(url,title):
	retry_times =0
	while retry_times < RETRY:
		try:
			movie = requests.get(url, headers = {'Connection':'close'}, timeout=TIMEOUT)
			with open(title, 'ab') as f:
				f.write(movie.content)
				f.flush()
			break
		except:
			print(url[:url.find(".ts?")].split("/")[-1] + " fail and retry %d" %retry_times)
			pass
		retry_times += 1
	else:
		try:
			os.remove(title)
		except OSError:
			print("OSError")
			pass
		print("Failed to retrieve video from this website")
	
def headers_make(url_str):
	return {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36Name','Referer':url_str}

def txt_cut(txt,begin,end):
	return txt[txt.find(begin):txt.find(end,txt.find(begin))]

Xvideo_page = 'https://www.xvideos.com/lang/japanese/'
base_page = Xvideo_page
while cur_page < 100:
	get_base = requests.get(base_page,headers=headers_make(base_page))
	soup = bs(get_base.content,'lxml')
	for content in soup.select('.thumb-block .thumb-under'):
		video_url = 'https://www.xvideos.com' + content.a['href']	#得到每个视频的地址
		title = content.a['title']+".mp4"							#得到每个视频的title
		if content.previous_sibling.span != None:
			if content.previous_sibling.span.string == 'HD':
				video_respon = requests.get(video_url,headers=headers_make(video_url))							#打开当前视频的地址
				time = get_pron_time(video_respon)
				if time > 20:
					print("video duration:%d" %time)
					m3u8_url=re.findall(r"html5player.setVideoHLS.*?'(.*?)'",video_respon.content.decode('utf-8'))	#得到包含所有清晰度m3u8的指向文件
					base_m3u8_url = re.findall(r"(.*?)hls.m3u8",m3u8_url[0])										#得到base_url
					HD_m3u8_url = m3u8_url[0].replace('hls.','hls-720p.')											#选取出HD的m3u8文件文件地址
					HD_m3u8_respon = requests.get(HD_m3u8_url,headers=headers_make(HD_m3u8_url))					#打开HD的m3u8文件地址
					print("begin to download %s" %title)
					time_start = datetime.datetime.now().replace(microsecond=0)
					ts_url_list = []
					for line in HD_m3u8_respon.content.decode('utf-8').split('\n'):
						if '.ts' in line:																			#逐行把ts地址拿出来
							ts_url = base_m3u8_url[0] + line
							ts_url_list.append(ts_url)																	#并放到ts_url_list中
						else:
							continue
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
				 
						t = threading.Thread(target=Handler, kwargs={'start': start, 'end': end, 'part': part, 'url': "123", 'filename': ts_url_list})
						t.setDaemon(True)
						t.start()
				 
					# 等待所有线程下载完成
					main_thread = threading.current_thread()
					for t in threading.enumerate():
						if t is main_thread:
							continue
						t.join()
					print('%s 下载完成' %title)
					shell_str = [str(each)+".ts" for each in list(range(num_thread))]
					shell_str = '+'.join(shell_str)
					shell_str = 'copy /b '+ shell_str + ' ' + title.replace(' ','').replace("\u3000","")
					os.system(shell_str)
					os.system('del /Q *.ts')
					time_end = datetime.datetime.now().replace(microsecond=0)
					print("用时: ", end='')
					print(time_end-time_start)
	cur_page += 1
	base_page = Xvideo_page + str(cur_page)
print("done")