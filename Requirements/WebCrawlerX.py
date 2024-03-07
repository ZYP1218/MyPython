import pprint
import re
import requests

# 设置请求头部，模拟浏览器访问
headers = {
    'referer': 'https://www.bilibili.com/',
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
}
# 定义函数获取网页响应
def get_response(url):

    # 发起GET请求获取网页数据
    response = requests.get(url=url, headers=headers)
    # 如果响应状态码不是200，则抛出异常
    response.raise_for_status()
    # 返回响应内容
    return response

# 定义函数获取视频信息
def get_video_info(url):
    # 获取网页响应
    response = get_response(url)
    # 确保响应状态是成功的
    if response.ok:
        # 使用正则表达式从网页内容中提取视频信息
        cid_match = re.findall('"cid":(\\d+),', response.text)
        session_match = re.findall('"session":"(.*?)"', response.text)
        title_match = re.findall('<h1 title="(.*?)" class="video-title"', response.text)
        # 如果成功提取到信息，则打印
        if cid_match and session_match and title_match:
            cid = cid_match[0]
            session = session_match[0]
            title = title_match[0]
            print("CID（视频ID）:", cid)
            print("Session（会话）:", session)
            print("标题:", title)
            video_info=[cid,session,title]
            return video_info
        else:
            # 如果未能提取信息，打印错误信息
            print("无法提取视频信息。")
    else:
        # 如果获取响应失败，打印错误信息
        print("服务器响应失败。")

def get_video_content(cid, session,bv_id):
    index_url = 'https://api.bilibili.com/x/player/playurl'
    data = {'cid':cid,
            'gn':'0',
            'type':'json',
            'fourk':'1',
            'bvid':bv_id,
            'fnver':'0',
            'session':session,
            }
    json_data = requests.get(url=index_url, params=data ,headers=headers).json()
    pprint.pprint(json_data)
    audio_url = json_data['data']['dash']['audio'][0]['baseUrl']
    video_url = json_data['data']['dash']['video'][0]['baseUrl']
    #print(json_data)
    video_content=[audio_url,video_url]
    return video_content

def save(title, audio_url, video_url):
    """保存数据"""
    audio_content = get_response(audio_url).content
    video_content = get_response(video_url).contentwith
    with open(title +'.mp3', mode='wb') as f:
        f.write(audio_content)
    with open(title +'.mp4', mode='wb') as f:
        f.write(video_content)
    print('保存完成')

def main(bv_id):
    url = f'https://www.bilibili.com/video/{bv_id}'
    print(url)
    video_info = get_video_info(url)
    video_content = get_video_content(video_info[0],video_info[1], bv_id)
    save(video_info[2],video_content[0],video_content[1])


if __name__ == '__main__':
    bv='BV1tA4m1G7H3'
    main(bv)

