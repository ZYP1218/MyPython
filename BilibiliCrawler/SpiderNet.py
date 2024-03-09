# 导入所需的库
import json
import re
from bs4 import BeautifulSoup
import subprocess
import requests
import tkinter as tk
from tkinter import ttk  # 导入ttk模块，用于更现代化的组件外观
from tkinter import messagebox, filedialog
from threading import Thread

# 定义Bilibili视频下载与合并音视频的类
class BilibiliVideoAudio:
    def __init__(self, bvid):
        # 初始化时保存BV号，并创建一个用于发送网络请求的Session
        self.bvid = bvid
        self.session = requests.Session()
        # 设置请求头部信息，模拟浏览器访问，防止被网站屏蔽
        self.session.headers.update({
            "referer": "https://www.bilibili.com",
            "origin": "https://www.bilibili.com",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
        })

    def get_play_info(self):
        # 根据传入的BV号拼接出视频页面的URL并获取页面HTML内容
        url = f'https://www.bilibili.com/video/{self.bvid}'
        response = self.session.get(url)
        response.raise_for_status()  # 如果响应状态码不是200，则抛出异常
        html = response.text

        # 使用BeautifulSoup解析HTML，提取视频的标题
        soup = BeautifulSoup(html, 'html.parser')
        meta_tag = soup.find('meta', {'property': 'og:title'})
        title = meta_tag['content'] if meta_tag else self.bvid  # 如果没有提取到标题就使用BV号代替

        # 使用正则表达式提取视频和音频的URL信息
        pattern = r'window\.__playinfo__=(\{.*?\})</script>'
        match = re.search(pattern, html)
        if not match:
            raise Exception('未能找到播放信息')
        play_info_json = match.group(1)
        play_info = json.loads(play_info_json)  # 将JSON格式的字符串解析为Python字典对象

        # 从解析出的信息中提取视频和音频的URL
        video_url = play_info['data']['dash']['video'][0]['baseUrl']
        audio_url = play_info['data']['dash']['audio'][0]['baseUrl']

        return title, video_url, audio_url

    def download_file(self, url, file_path, progress_callback):
        # 通过流式请求下载大文件，如视频或音频
        with self.session.get(url, stream=True) as response:
            response.raise_for_status()  # 确保请求成功
            total_length = int(response.headers.get('content-length', 0))  # 获取内容的总长度

            # 打开文件进行写入
            with open(file_path, 'wb') as file:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # 过滤掉keep-alive的新chunk
                        file.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:  # 如果有进度回调函数，则调用它更新进度
                            progress_callback(downloaded, total_length)
        print(f'下载完成：{file_path}')

    def merge_video_audio(self, video_path, audio_path, output_path):
        # 使用环境变量中的ffmpeg进行调用，这样不需要指定具体路径
        FFMPEG_CMD = 'ffmpeg'  # 假设ffmpeg已经在环境变量中设置好了

        # 构造ffmpeg命令以合并视频和音频文件
        cmd = [FFMPEG_CMD, '-y', '-i', video_path, '-i', audio_path, '-c', 'copy', output_path]

        # 执行命令并等待完成
        subprocess.run(cmd, check=True)
        print(f'合并文件完成：{output_path}')

class BilibiliApp(tk.Tk):
    def __init__(self):
        # 初始化父类构造器
        super().__init__()
        # 加载图标文件
        self.iconbitmap('../ico/Bilibili.ico')
        # 设置窗口标题和大小
        self.title('Bilibili视频下载器')
        self.geometry('500x300')
        # 创建窗口组件
        self.create_widgets()


    def update_progress(self, downloaded, total_length):
        # 根据下载的字节数和总字节数更新进度条的值
        progress = int((downloaded / total_length) * 100)
        # 设置进度条的新值，以更新显示
        self.progress['value'] = progress
        # 更新界面，以反映进度条的变化
        self.update_idletasks()

    def create_widgets(self):
        # 配置应用界面的样式和布局
        self.style = ttk.Style(self)
        # 使用clam风格，你可以试验其他风格如'alt', 'default', 'classic'等
        self.style.theme_use('clam')

        # 创建界面元素并放置它们
        # 设定一些样式
        self.style.configure('TLabel', font=('Arial', 11), padding=5)
        self.style.configure('TButton', font=('Arial', 11), padding=5)
        self.style.configure('TEntry', font=('Arial', 11), padding=5)

        # 输入框标签
        label = ttk.Label(self, text='请输入Bilibili视频BV号:', style='TLabel')
        label.grid(column=0, row=0, padx=10, pady=10, sticky='w')

        # 输入框
        self.bv_input = ttk.Entry(self, width=50, style='TEntry')
        self.bv_input.grid(column=1, row=0, padx=10, pady=10, sticky='ew')

        # 下载按钮
        download_button = ttk.Button(self, text='下载', command=self.start_download_thread, style='TButton')
        download_button.grid(column=2, row=0, padx=10, pady=10, sticky='ew')

        # 保存位置按钮
        save_button = ttk.Button(self, text='选择保存位置', command=self.choose_directory, style='TButton')
        save_button.grid(column=0, row=1, padx=10, pady=10, sticky='ew')

        # 保存路径标签
        self.save_path_label = ttk.Label(self, text='未选择保存位置', style='TLabel')
        self.save_path_label.grid(column=1, row=1, padx=10, pady=10, columnspan=2, sticky='w')

        # 下载进度条
        self.progress = ttk.Progressbar(self, orient='horizontal', length=300, mode='determinate')
        self.progress.grid(column=0, row=2, columnspan=3, padx=10, pady=10, sticky='ew')

        # 下载状态标签
        self.status_label = ttk.Label(self, text='准备下载...', style='TLabel')
        self.status_label.grid(column=0, row=3, columnspan=3, padx=10, pady=10, sticky='w')

        # 使用grid布局管理器来放置组件
        # 列和行的权重设定确保组件间隔均匀，并且随窗口大小调整而调整

    def update_status(self, status):
        # 在GUI中安全地更新状态标签的文本
        # 使用after方法避免线程直接更新GUI，这可能会导致线程问题
        self.status_label.config(text=status)

    def choose_directory(self):
        # 使用文件对话框选择保存下载文件的目录
        self.save_directory = filedialog.askdirectory()
        # 更新标签以显示选择的目录。如果未选择，则显示未选择保存位置
        self.save_path_label.config(text=f'保存位置：{self.save_directory}' if self.save_directory else '未选择保存位置')

    def start_download_thread(self):
        # 启动一个新线程进行下载，避免在下载过程中阻塞GUI
        bv_number = self.bv_input.get()
        if bv_number:
            # 输入框有内容，即BV号不为空，开始下载
            thread = Thread(target=self.download_video, args=(bv_number,))
            thread.start()
        else:
            # BV号为空，显示错误信息
            messagebox.showerror('错误', 'BV号不能为空！')

    def download_video(self, bvid):
        # 实际执行下载工作的函数
        try:
            # 创建下载器实例
            bili = BilibiliVideoAudio(bvid)
            # 获取视频信息
            title, video_url, audio_url = bili.get_play_info()
            # 标题中不合法的字符替换掉，避免创建文件时出错
            sanitized_title = re.sub(r'[\\/*?:"<>|]', '', title)

            # 检查是否已经选择了保存目录
            if hasattr(self, 'save_directory') and self.save_directory:
                save_path = self.save_directory
            else:
                save_path = '.'

            # 拼接出完整的文件保存路径
            video_path = f'{save_path}/{sanitized_title}.mp4'
            audio_path = f'{save_path}/{sanitized_title}.mp3'
            output_path = f'{save_path}/{sanitized_title}_合并.mp4'

            # 依次下载视频和音频，并更新GUI状态
            self.update_status('正在下载视频...')
            bili.download_file(video_url, video_path, self.update_progress)
            self.update_status('正在下载音频...')
            bili.download_file(audio_url, audio_path, self.update_progress)

            # 合并视频和音频文件，并更新状态
            self.update_status('正在合并视频和音频...')
            bili.merge_video_audio(video_path, audio_path, output_path)
            self.update_status('下载和合并完成！')

            # 一切完成，弹出提示窗口告知用户
            messagebox.showinfo('完成', f'视频已下载并合并完成：{output_path}')
        except Exception as e:
            # 发生错误时弹出错误提示
            messagebox.showerror('错误', str(e))

# 主程序入口
if __name__ == '__main__':
    app = BilibiliApp()
    app.mainloop()  # 开始应用的主事件循环
