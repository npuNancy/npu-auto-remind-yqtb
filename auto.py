import re
import time
import pynput
import datetime
import requests
import pyperclip
import pyautogui as pg
from bs4 import BeautifulSoup


def get_pos():
    '''
    每隔一秒获取鼠标坐标
    '''
    try:
        while True:
            x, y = pg.position()
            print(f"{x}, {y}")
            time.sleep(1)
    except KeyboardInterrupt:
        print('\nExit.')


def get_click_pos():
    '''
    描述: 
        返回鼠标点击处的坐标
    '''
    with pynput.mouse.Events() as event:
        for i in event:
            # 监测鼠标点击事件。
            if isinstance(i, pynput.mouse.Events.Click):
                return i.x, i.y


def at_people(name, pos_x, pos_y):
    # 复制姓名到剪切板
    pyperclip.copy(name)
    time.sleep(1)

    # 定位鼠标
    pg.moveTo(pos_x, pos_y)
    pg.click()

    # 输入@
    pg.write('@', interval=0.2)
    time.sleep(1)

    # 输入姓名
    pg.hotkey('ctrl', 'v')
    time.sleep(1)

    # 选中此人
    pg.press('enter')

    print(f"{name} at成功")


def get_name_dict(username, password):
    '''
    描述:
        从疫情填报系统获取未填报人员名单
    参数:
        username: 翱翔门户账号
        password: 翱翔门户密码
    返回:
        {
            "年级":[name1, name2, ],
        }
    '''

    date = datetime.now().strftime("%Y-%m-%d")  # 当前日期
    login_url = "https://uis.nwpu.edu.cn/cas/login"  # 翱翔门户登录url
    post_url = "https://yqtb.nwpu.edu.cn/wx/ry/fktj_list.jsp?flag=wtbrs&gjc=&rq={}&bjbh=&PAGENUMBER={}&PAGEGROUP=0"

    login_data = {
        # 账号
        'username': username,
        # 密码
        'password': password,
        'currentMenu': '1',
        'execution': 'e1s1',
        "_eventId": "submit"
    }

    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # 登录
    session = requests.session()
    response = session.get(login_url, headers=header)
    execution = re.findall(r'name="execution" value="(.*?)"', response.text)[0]
    login_data['execution'] = execution
    response = session.post(login_url, data=login_data, headers=header)
    if "欢迎使用" in response.text:
        print(f"login successfully")
    else:
        print(f"login unsuccessfully")
        exit(1)

    res = ""
    for i in range(3):
        if len(res) == 0:
            response = session.get("https://yqtb.nwpu.edu.cn/wx/xg/yz-mobile/index.jsp")
            response = session.get("https://yqtb.nwpu.edu.cn/wx/ry/jrsb.jsp")
            pattern = r"url:'ry_util\.jsp\?sign=(.*).*'"
            res = re.findall(pattern, response.text)
    # print('res:' + str(res))
    if len(res) == 0:
        print("error in script, please contact to the author")
        exit(1)
    time.sleep(1)
    session.headers.update({'referer': 'https://yqtb.nwpu.edu.cn/wx/ry/jrsb.jsp'})

    # 获取PageNumber
    html = session.get(post_url.format(date, 1))
    number = int(re.findall(r"共(\d*)条", html.text)[0])  # 信息总数
    page_number = int(number / 15) + 1  # 每页有15条信息

    student_dict = {}
    # 遍历所有page
    for i in range(1, int(page_number)+1):
        print(f"Page: {i}")
        html = session.get(post_url.format(date, i))
        soup = BeautifulSoup(html.text, 'html.parser')
        table = soup.find_all("table")[0]

        tbody = table if not table.tbody else table.tbody

        # 遍历table
        for tr in tbody.findAll('tr')[1:]:
            name = tr.find_all('td')[0].getText()  # 姓名
            std_id = tr.find_all('td')[1].getText()  # 学号

            # 添加某个年级
            if std_id[:4] not in student_dict.keys():
                student_dict[std_id[:4]] = []
            student_dict[std_id[:4]].append(name)
        time.sleep(1)

    return student_dict


if __name__ == "__main__":

    username = "2016010054"
    password = "zhouying9146"

    student_dict = get_name_dict(username, password)
    for key, value in student_dict.items():
        print(f"现在操作{key}年级的人,你有10s时间打开聊天窗口")
        time.sleep(10)

        print('请点击聊天框')
        pos_x, pos_y = get_click_pos()

        for name in value:
            at_people(name, pos_x, pos_y)

        # 发送消息
        pg.press('enter')
