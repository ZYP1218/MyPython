import json
import os
import requests
import re
from bs4 import BeautifulSoup
import subprocess


class BilibiliVideoAudio:
	def __init__(self, bvid):
		self.bvid = bvid
		self.session = requests.Session()
		self.session.headers.update({
			"referer": "https://www.bilibili.com",
			"origin": "https://www.bilibili.com",
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
						  '(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
		})

	def get_play_info(self):
		# 获取视频页面的HTML内容
		url = f'https://www.bilibili.com/video/{self.bvid}'
		response = self.session.get(url)
		response.raise_for_status()  # 如果响应状态码不是200，抛出异常
		html = response.text

		# 提取视频标题
		soup = BeautifulSoup(html, 'html.parser')
		meta_tag = soup.find('meta', {'property': 'og:title'})
		title = meta_tag['content'] if meta_tag else self.bvid

		# 提取视频和音频的URL
		pattern = r'window\.__playinfo__=(\{.*?\})</script>'
		match = re.search(pattern, html)
		if not match:
			raise Exception('未能找到播放信息')
		play_info_json = match.group(1)
		play_info = json.loads(play_info_json)

		# 解析出视频和音频的URL
		video_url = play_info['data']['dash']['video'][0]['baseUrl']
		audio_url = play_info['data']['dash']['audio'][0]['baseUrl']

		return title, video_url, audio_url

	def download_file(self, url, file_path):
		# 流式下载大文件
		with self.session.get(url, stream=True) as response:
			response.raise_for_status()  # 如果响应状态码不是200，抛出异常
			with open(file_path, 'wb') as file:
				for chunk in response.iter_content(chunk_size=8192):
					file.write(chunk)
		print(f'下载完成：{file_path}')

	def merge_video_audio(self, video_path, audio_path, output_path):
		# 构造ffmpeg命令以合并视频和音频文件
		cmd = ['ffmpeg', '-y', '-i', video_path, '-i', audio_path, '-c', 'copy', output_path]

		# 执行命令并等待完成
		subprocess.run(cmd, check=True)
		print(f'合并文件完成：{output_path}')


def main():
	# 使用视频ID初始化
	bili = BilibiliVideoAudio(video_bvid)

	# 获取播放信息（视频URL、音频URL、标题）
	title, video_url, audio_url = bili.get_play_info()

	# 为文件名清理标题字符串
	sanitized_title = re.sub(r'[\\/*?:"<>|]', '', title)

	# 准备文件路径
	video_path = f'./{sanitized_title}.mp4'
	audio_path = f'./{sanitized_title}.mp3'
	output_path = f'./{sanitized_title}_合并.mp4'

	# 下载视频和音频
	bili.download_file(video_url, video_path)
	bili.download_file(audio_url, audio_path)

	# 合并视频和音频
	bili.merge_video_audio(video_path, audio_path, output_path)


if __name__ == '__main__':
    video_bvid = input("请输入你要下载的视频BV号:")
    main()
