import os
import csv
import re
import time
import json
import math
import requests
import numpy as np
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def merge_csv(input_filename, output_filename):
    """
    读取csv文件内容，并写入新的文件
    :param input_filename: 传入的文件名称
    :param output_filename: 写入的新文件的名称
    :return: 向新文件中写入input_filename中的内容
    """
    # 读取文件
    csv_data_read = pd.read_csv(input_filename)
    # 获取文件总行数
    number_of_row = len(csv_data_read)
    # 循环该csv文件中的所有行，并写入信息
    with open(output_filename, mode='a', encoding='utf-8', newline='')  as csvfile:
        fieldnames = ['BV号']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if csvfile.tell() == 0:
            writer.writeheader()

        for i in range(number_of_row):
            row_content = csv_data_read.iloc[i, 0]
            writer.writerow({'BV号': row_content})

    # 打印进度
    print(f'成功向{output_filename}中写入了{input_filename}的全部信息')

def write_to_csv_bvid(input_filename, bvid):
    """
    写入新的csv文件，若没有则创建，须根据不同程序进行修改
    :param input_filename: 写入的文件名称
    :param bvid: BV号
    :return: 生成写入的input_filename文件
    """
    # 判断路径是否存在
    file_exists = os.path.isfile(input_filename)
    # 设置最大尝试次数
    max_retries = 50
    retries = 0

    while retries < max_retries:
        try:
            with open(input_filename, mode='a', encoding='utf-8', newline='')  as csvfile:
                fieldnames = ['BV号']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({'BV号': bvid})
            break  # 如果成功写入，跳出循环
        except PermissionError as e:
            retries += 1
            print(f"将爬取到的数据写入csv时，遇到权限错误Permission denied，文件可能被占用或无写入权限: {e}")
            print(f"等待3s后重试，将会重试50次... (尝试 {retries}/{max_retries})")
            time.sleep(3)  # 等待3秒后重试
    else:
        print("将爬取到的数据写入csv时遇到权限错误，且已达到最大重试次数50次，退出程序")

def spider_bvid(keyword):
    """
    利用selenium获取搜索结果的bvid，供给后续程序使用
    :param keyword: 搜索关键词
    :return: 生成去重的output_filename = f'{keyword}BV号.csv'
    """
    # 保存的文件名
    input_filename = f'{keyword}BV号.csv'

    # 启动爬虫
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(options=options)  # 设置无界面爬虫
    browser.set_window_size(1400, 900)  # 设置全屏，注意把窗口设置太小的话可能导致有些button无法点击
    browser.get('https://bilibili.com')
    # 刷新一下，防止搜索button被登录弹框遮住
    browser.refresh()
    print("============成功进入B站首页！！！===========")

    # 输入关键词并点击搜索
    input = browser.find_element(By.CLASS_NAME, 'nav-search-input')
    button = browser.find_element(By.CLASS_NAME, 'nav-search-btn')
    input.send_keys(keyword)
    button.click()
    print(f'==========成功搜索{keyword}相关内容==========')

    # 设置窗口
    all_h = browser.window_handles
    browser.switch_to.window(all_h[1])

    # B站最多显示42页
    total_page = 42

    for i in range(total_page):
        url = f"https://search.bilibili.com/all?keyword={keyword}&from_source=webtop_search&spm_id_from=333.1007&search_source=5&page={i}"
        print(f"===========正在尝试获取第{i + 1}页网页内容===========")
        print(f"===========本次的url为：{url}===========")
        browser.get(url)
        print('正在等待页面加载...')
        time.sleep(3)

        # 直接分析网页
        html = browser.page_source
        soup = BeautifulSoup(html, 'lxml')
        infos = soup.find_all(class_='bili-video-card')
        bv_id_list = []

        for info in infos:
            href = info.find('a').get('href')
            split_url_data = href.split('/')
            split_url_data = [element for element in split_url_data if element != '']
            bvid = split_url_data[2]

            if bvid not in bv_id_list:
                bv_id_list.append(bvid)

        for bvid_index in range(len(bv_id_list)):
            write_to_csv_bvid(input_filename, bv_id_list[bvid_index])

        print('写入文件成功')
        print("===========成功获取第" + str(i + 1) + "次===========")
        time.sleep(1)

    # 退出爬虫
    browser.quit()
    print(f'==========爬取完成。退出爬虫==========')

def write_to_csv(filename, bvid, aid, cid, mid, name, follower, archive, title, tname, pub_date, pub_time, desc,
                 view, like, coin, favorite, share, reply, danmaku, communication_index):
    """
    向csv文件中写入B站视频相关的基本信息，若未找到文件，则新建文件
    :param filename: 写入数据的文件名
    :param bvid: BV号
    :param aid: AV号
    :param cid: 用于获取弹幕文本的
    :param mid: UP主的ID
    :param name: UP主名称
    :param follower: UP主粉丝数
    :param archive: UP主作品总数
    :param title: 标题
    :param tname: tag名称
    :param pub_date: 发布日期
    :param pub_time: 发布时间
    :param desc: 视频简介
    :param view: 播放量
    :param like: 点赞数
    :param coin: 投币数
    :param favorite: 收藏数
    :param share: 分享数
    :param reply: 评论数
    :param danmaku: 弹幕数
    :param communication_index: 传播效果公式的值
    :return:
    """
    file_exists = os.path.isfile(filename)
    max_retries = 50
    retries = 0

    while retries < max_retries:
        try:
            with open(filename, mode='a', encoding='utf-8', newline='') as csvfile:
                fieldnames = ['BV号', 'AV号', 'CID', 'UP主ID', 'UP主名称', 'UP主粉丝数', '作品总数', '视频标题',
                              '视频分类标签',
                              '发布日期', '发布时间', '视频简介', '播放量', '点赞数', '投币数', '收藏数', '分享数',
                              '评论数',
                              '弹幕数', '传播效果指数']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    'BV号': bvid, 'AV号': aid, 'CID': cid, 'UP主ID': mid, 'UP主名称': name, 'UP主粉丝数': follower,
                    '作品总数': archive, '视频标题': title, '视频分类标签': tname, '发布日期': pub_date,
                    '发布时间': pub_time,
                    '视频简介': desc, '播放量': view, '点赞数': like, '投币数': coin, '收藏数': favorite,
                    '分享数': share,
                    '评论数': reply, '弹幕数': danmaku, '传播效果指数': communication_index
                })
            break  # 如果成功写入，跳出循环
        except PermissionError as e:
            retries += 1
            print(f"将爬取到的数据写入csv时，遇到权限错误Permission denied，文件可能被占用或无写入权限: {e}")
            print(f"等待3s后重试，将会重试50次... (尝试 {retries}/{max_retries})")
    else:
        print("将爬取到的数据写入csv时遇到权限错误，且已达到最大重试次数50次，退出程序")

def get_user_info(uid):
    """
    通过uid(即mid)获取UP主的粉丝总数和作品总数
    :param uid: mid
    :return:user_info_dict
    """
    # 定义空字典用于存放数据
    user_info_dict = {}
    # 设置用户代理 User_Agent及Cookies
    headers = {
        'User-Agent': "",
        'Cookie': ""}
    api_url = f'https://api.bilibili.com/x/web-interface/card?mid={uid}'
    print(f"正在进行爬取uid为：{uid}的UP主的粉丝数量与作品总数")
    print(f"==========本次获取数据的up主的uid为：{uid}==========")
    print(f"url为{api_url}")
    up_info = requests.get(url=api_url, headers=headers)
    up_info_json = json.loads(up_info.text)
    fans_number = up_info_json['data']['card']['fans']
    user_info_dict['follower'] = fans_number
    archive_count = up_info_json['data']['archive_count']
    user_info_dict['archive'] = archive_count
    print(f'=========={bv_id} 的作者基本信息已成功获取==========\n')
    time.sleep(1.5)
    return user_info_dict

def get_video_info(bv_id):
    headers = {
        'User-Agent': "",
        'Cookie': ""}
    api_url = f'https://api.bilibili.com/x/web-interface/view?bvid={bv_id}'
    print(f"正在进行爬取uid为：{bv_id}的UP主的粉丝数量与作品总数")
    print(f"==========本次获取数据的视频BV号为：{bv_id}==========")
    print(f"url为：{api_url}")
    video_info = requests.get(url=api_url, headers=headers)
    video_info_json = json.loads(video_info.text)
    info_dict = {}
    # 信息解读
    bvid = video_info_json['data']['bvid']
    info_dict['bvid'] = bvid
    aid = video_info_json['data']['aid']
    info_dict['aid'] = aid
    cid = video_info_json['data']['cid']
    info_dict['cid'] = cid
    mid = video_info_json['data']['owner']['mid']
    info_dict['mid'] = mid
    name = video_info_json['data']['owner']['name']
    info_dict['name'] = name
    title = video_info_json['data']['title']
    info_dict['title'] = title
    tname = video_info_json['data']['tname']
    info_dict['tname'] = tname
    pubdate = video_info_json['data']['pubdate']
    pub_datatime = datetime.fromtimestamp(pubdate)
    pub_datatime_strf = pub_datatime.strftime('%Y-%m-%d %H:%M:%S')
    date = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", pub_datatime_strf)
    info_dict['pub_date'] = date.group()
    pub_time = re.search(r"(\d{1,2}:\d{1,2}:\d{1,2})", pub_datatime_strf)
    info_dict['pub_time'] = pub_time.group()
    desc = video_info_json['data']['desc']
    info_dict['desc'] = desc
    view = video_info_json['data']['stat']['view']
    info_dict['view'] = view
    like = video_info_json['data']['stat']['like']
    info_dict['like'] = like
    coin = video_info_json['data']['stat']['coin']
    info_dict['coin'] = coin
    favorite = video_info_json['data']['stat']['favorite']
    info_dict['favorite'] = favorite
    share = video_info_json['data']['stat']['share']
    info_dict['share'] = share
    repiy = video_info_json['data']['stat']['reply']
    info_dict['reply'] = repiy
    danmaku = video_info_json['data']['stat']['danmaku']
    info_dict['danmaku'] = danmaku
    print(f'=========={bv_id} 的视频基本信息已成功获取==========')
    print('正在等待，以防访问过于频繁\n')
    time.sleep(1.5)
    return info_dict

if __name__ == '__main__':
    keywords = ["暗区突围"]
    for keyword in keywords:
        spider_bvid(keyword)
    for keyword in keywords:
        csv_to_merge = f'{keyword}BV号.csv'
        merge_csv(input_filename=csv_to_merge, output_filename='BV号合并.csv')

    filename = 'BV号合并.csv'
    open_csv = pd.read_csv(filename)
    open_csv.drop_duplicates(subset='BV号')
    bv_id_list = np.array(open_csv['BV号'])

    for i in range(len(bv_id_list)):
        bv_id = bv_id_list[i]
        print(f'正在进行第{i + 1}次爬取\n')
        video_info = get_video_info(bv_id)
        bvid = video_info['bvid']
        aid = video_info['aid']
        cid = video_info['cid']
        mid = video_info['mid']
        name = video_info['name']
        title = video_info['title']
        tname = video_info['tname']
        pub_date = video_info['pub_date']
        pub_time = video_info['pub_time']
        desc = video_info['desc']
        view = video_info['view']
        like = video_info['like']
        coin = video_info['coin']
        favorite = video_info['favorite']
        share = video_info['share']
        reply = video_info['reply']
        danmaku = video_info['danmaku']

        Communication_Index = math.log(0.5 * int(view) + 0.3 * (int(like) + int(coin) + int(favorite)) + 0.2 * (int(reply) + int(danmaku)))
        user_info = get_user_info(uid=mid)
        follower = user_info['follower']
        archive = user_info['archive']
        write_to_csv(filename='视频基本信息.csv', bvid=bvid, aid=aid, cid=cid, mid=mid, name=name, follower=follower,
                     archive=archive, title=title, tname=tname, pub_date=pub_date, pub_time=pub_time, desc=desc,
                     view=view, like=like, coin=coin, favorite=favorite, share=share, reply=reply, danmaku=danmaku,
                     communication_index=Communication_Index)
        print(f'==========第{i + 1}个BV号：{bv_id}的相关数据已写入csv文件中==========')
        print('==================================================\n')
