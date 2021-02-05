import requests
import json
import time
import re
import random
import os
from campus import CampusCard

# error数组用于保存打卡失败的成员循环打卡
error = []


def main(stus):

    for stu in stus:
        phone = stu[0]
        password = stu[1]
        device_seed = stu[2]
        uid = stu[3]
        msg = check(phone, password, device_seed, uid)
        print(msg)
        wechat_push(uid, msg)

    # 当error list不为空时一直循环打卡 直到清空error
    while len(error) != 0:
        # 等待1min
        time.sleep(60)
        for i in range(len(error)-1, -1, -1):
            phone = error[i][0]
            password = error[i][1]
            device_seed = error[i][2]
            uid = error[i][3]

            msg = check(phone, password, device_seed, uid)
            print(msg)
            wechat_push(uid, msg)
            # 打卡成功后从error中删除对应成员
            if re.search('打卡成功', msg):
                del error[i]


def get_time():
    return[(time.localtime().tm_hour + 8) % 24,
           time.localtime().tm_min,
           time.localtime().tm_sec]


def get_random_temperature():
    a = random.uniform(36.2, 36.5)
    return round(a, 1)


def wechat_push(uid, msg):
    json = {
        "appToken": "AT_hHtOWzcFDw3nhEWfhLNJgnNDAO132pFK",
        "content": msg,
        "contentType": 1,
        "uids": [uid]
    }
    response = requests.post(
        "http://wxpusher.zjiecode.com/api/send/message", json=json)
    if response.status_code == 200:
        print('微信推送成功!')
    else:
        print('微信推送失败!')


def get_token(phone, password, device_seed):
    stuobj = CampusCard(phone, password, device_seed).user_info
    if stuobj['login']:
        return stuobj["sessionId"]
    return None


def get_last_post_json(token):
    retry = 0
    while retry < 3:
        jsons = {"businessType": "epmpics",
                 "jsonData": {"templateid": "pneumonia", "token": token},
                 "method": "userComeApp"}
        try:
            # 如果不请求一下这个地址，token就会失效
            requests.post(
                "https://reportedh5.17wanxiao.com/api/clock/school/getUserInfo", data={'token': token})
            res = requests.post(
                url="https://reportedh5.17wanxiao.com/sass/api/epmpics", json=jsons, timeout=10).json()
        except:
            retry += 1
            time.sleep(1)
            continue
        if res['code'] != '10000':
            return None
        data = json.loads(res['data'])
        post_dict = {
            'deptStr': data['deptStr'],
            'areaStr': data['areaStr'],
            'username': data['username'],
            'stuNo': data['stuNo'],
            'phonenum': data['phonenum'],
            'updatainfos': data['cusTemplateRelations']
        }
        return post_dict
    return None


def get_updatainfo(updatainfos, propertyname):
    for a in updatainfos:
        if a['propertyname'] == propertyname:
            return a['value']
    return None


def check(phone, password, device_seed, uid):
    token = get_token(phone, password, device_seed)
    if not token:
        return '获取token失败'
    last_check_json = get_last_post_json(token)
    if not last_check_json:
        return '获取上一次打卡信息失败'
    now = get_time()
    check_json = {
        "businessType": "epmpics",
        "method": "submitUpInfo",
        "jsonData": {
            "deptStr": last_check_json['deptStr'],
            "areaStr": last_check_json['areaStr'],
            "reportdate": round(time.time() * 1000),
            "customerid": "43",
            "deptid": last_check_json['deptStr']['deptid'],
            "source": "app",
            "templateid": "pneumonia",
            "stuNo": last_check_json['stuNo'],
            "username": last_check_json['username'],
            "phonenum": last_check_json['phonenum'],
            "userid": round(time.time()),
            "updatainfo": [
                {
                    "propertyname": "isGoWarningAdress",
                    "value": get_updatainfo(last_check_json['updatainfos'], "isGoWarningAdress")
                },
                {
                    "propertyname": "jtdz",
                    "value": get_updatainfo(last_check_json['updatainfos'], "jtdz")
                },
                {
                    "propertyname": "personNO",
                    "value": get_updatainfo(last_check_json['updatainfos'], "personNO")
                },
                {
                    "propertyname": "langtineadress",
                    "value": get_updatainfo(last_check_json['updatainfos'], "langtineadress")
                },
                {
                    "propertyname": "ownPhone",
                    "value": get_updatainfo(last_check_json['updatainfos'], "ownPhone")
                },
                {
                    "propertyname": "emergencyContact",
                    "value": get_updatainfo(last_check_json['updatainfos'], "emergencyContact")
                },
                {
                    "propertyname": "tradeNum",
                    "value": get_updatainfo(last_check_json['updatainfos'], "tradeNum")
                },
                {
                    "propertyname": "temperature",
                    "value": get_updatainfo(last_check_json['updatainfos'], "temperature")
                },
                {
                    "propertyname": "symptom",
                    "value": "均无"
                },
                {
                    "propertyname": "isContactpatient",
                    "value": "均无"
                },
                {
                    "propertyname": "istouchcb",
                    "value": "否"
                },
                {
                    "propertyname": "isTransitProvince",
                    "value": "否"
                },
                {
                    "propertyname": "isTouch",
                    "value": "否"
                },
                {
                    "propertyname": "backadress",
                    "value": ""
                },
                {
                    "propertyname": "isContactFriendIn14",
                    "value": "否"
                },
                {
                    "propertyname": "sxaddress",
                    "value": ""
                },
                {
                    "propertyname": "medicalObservation",
                    "value": "否"
                },
                {
                    "propertyname": "sxss",
                    "value": ""
                },
                {
                    "propertyname": "isConfirmed",
                    "value": "否"
                },
                {
                    "propertyname": "assistRemark",
                    "value": ""
                },
                {
                    "propertyname": "gyfh",
                    "value": "否"
                },
                {
                    "propertyname": "FamilyIsolate",
                    "value": ""},
                {
                    "propertyname": "ishborwh",
                    "value": "否"
                },
                {
                    "propertyname": "IsHospitaltxt",
                    "value": ""
                },
                {
                    "propertyname": "fhhb",
                    "value": "否"
                },
                {
                    "propertyname": "isname",
                    "value": ""
                },
                {
                    "propertyname": "other1",
                    "value": ""
                },
                {
                    "propertyname": "isFFHasSymptom",
                    "value": "是"
                }
            ],
            "gpsType": 1,
            "token": token
        },
        "token": token
    }

    flag = 0
    for i in range(1, 2):
        print('{0}第{1}次尝试打卡中...'.format(last_check_json['username'], i))
        response = requests.post(
            "https://reportedh5.17wanxiao.com/sass/api/epmpics", json=check_json)
        if response.status_code == 200:
            flag = 1
            break
        else:
            print(response.text)
            print('{0}第{1}次打卡失败!30s后重新打卡'.format(
                last_check_json['username'], i))
            time.sleep(30)
    print(response.text)
    time_msg = str(now[0]) + '时' + str(now[1]) + '分' + str(now[2]) + '秒'
    if flag == 1:
        if response.json()["msg"] == '成功':
            msg = time_msg + '时' + last_check_json['username'] + "打卡成功"
        else:
            msg = time_msg + '时' + last_check_json['username'] + "打卡异常"
    else:
        msg = time_msg + "网络错误打卡失败!1min后重新打卡!"
        error.append([phone, password, device_seed, uid])
    return msg

# 腾讯云函数从此入口进入
def main_handler(arg1, arg2):
    stus = []
    i = 1
    while True:
        try:
            user = os.environ.get('user' + str(i))
            if user is None:
                break
            stus.append(user.split(' '))
            i += 1
        except:
            break
    main(stus)

# 直接运行脚本从此入口进入
if __name__ == "__main__":
    stus = []
    tmp = input()
    while tmp != 'end':
        stus.append(tmp.split(' '))
        tmp = input()
    main(stus)
