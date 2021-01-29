import json
import base64
import urllib3
import logging
import hashlib
import requests
from Crypto import Random
from Crypto.Cipher import DES3
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Util.Padding import pad, unpad

random_generator = Random.new().read
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def create_key_pair(size):
    rsa = RSA.generate(size, random_generator)
    private_key = str(rsa.export_key(), 'utf8')
    private_key = private_key.split('-\n')[1].split('\n-')[0]
    public_key = str(rsa.publickey().export_key(), 'utf8')
    public_key = public_key.split('-\n')[1].split('\n-')[0]
    return public_key, private_key


def rsa_decrypt(input_string, private_key):
    input_bytes = base64.b64decode(input_string)
    rsa_key = RSA.importKey("-----BEGIN RSA PRIVATE KEY-----\n" +
                            private_key+"\n-----END RSA PRIVATE KEY-----")
    cipher = PKCS1_v1_5.new(rsa_key)
    return str(cipher.decrypt(input_bytes, random_generator), 'utf-8')


def des_3_encrypt(string, key, iv):
    cipher = DES3.new(key, DES3.MODE_CBC, iv.encode("utf-8"))
    ct_bytes = cipher.encrypt(pad(string.encode('utf8'), DES3.block_size))
    ct = base64.b64encode(ct_bytes).decode('utf8')
    return ct


def object_encrypt(object_to_encrypt, key, iv="66666666"):
    return des_3_encrypt(json.dumps(object_to_encrypt), key, iv)


class CampusCard:
    """
    完美校园APP
    初始化时需要传入手机号码、密码、device_seed
    """

    def __init__(self, username, password, device_seed):
        """
        初始化一卡通类
        :param username: 完美校园账号
        :param password: 完美校园密码
        :param device_seed: 用于生成deviceId的种子
        """
        self.seed = int(device_seed)
        self.user_info = self.create_blank_user()
        if self.user_info['exchangeFlag']:
            self.exchange_secret()
            self.login(username, password)

    def create_blank_user(self):
        """
        虚拟一个空的未登录设备
        :return: 空设备信息
        """
        rsa_keys = create_key_pair(1024)
        return {
            'appKey': '',
            'sessionId': '',
            'exchangeFlag': True,
            'login': False,
            'serverPublicKey': '',
            'deviceId': self.generate_IMEI(),
            'wanxiaoVersion': "10525101",
            'rsaKey': {
                'private': rsa_keys[1],
                'public': rsa_keys[0]
            }
        }

    def rand(self):
        """
        种子计算 用于生成IMEI
        """
        self.seed = (self.seed * 9301 + 49297) % 233280
        return self.seed / 233280.0

    def generate_IMEI(self):
        """
        生成IMEI
        """
        code = ''
        sum = 0
        for _ in range(12):
            code += str(int(self.rand()*10))
        data = '86' + code
        for index, ch in enumerate(data):
            if index % 2:
                ch = int(ch)*2
                sum += int(ch/10) + ch % 10
            else:
                sum += int(ch)
        data += str(sum * 9 % 10)
        return data

    def exchange_secret(self):
        """
        与完美校园服务器交换RSA加密的公钥，并取得sessionId
        :return:
        """
        resp = requests.post(
            "https://server.17wanxiao.com/campus/cam_iface46/exchangeSecretkey.action",
            headers={
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; HUAWEI INE-AL00 Build/HUAWEIINE-AL00)",
            },
            json={
                "key": self.user_info["rsaKey"]["public"]
            },
            verify=False
        )
        session_info = json.loads(
            rsa_decrypt(resp.text.encode(resp.apparent_encoding),
                        self.user_info["rsaKey"]["private"])
        )
        self.user_info["sessionId"] = session_info["session"]
        self.user_info["appKey"] = session_info["key"][:24]

    def login(self, username, password):
        """
        使用账号密码登录完美校园APP
        :param username: 完美校园APP绑定的手机号码
        :param password: 完美校园密码
        :return:
        """
        password_list = []
        for i in password:
            password_list.append(des_3_encrypt(
                i, self.user_info["appKey"], "66666666"))
        login_args = {
            "appCode": "M002",
            "deviceId": self.user_info["deviceId"],
            "netWork": "wifi",
            "password": password_list,
            "qudao": "guanwang",
            "requestMethod": "cam_iface46/loginnew.action",
            "shebeixinghao": "INE-AL00",
            "systemType": "android",
            "telephoneInfo": "9",
            "telephoneModel": "HUAWEI INE-AL00",
            "type": "1",
            "userName": username,
            "wanxiaoVersion": "10525101"
        }
        upload_args = {
            "session": self.user_info["sessionId"],
            "data": object_encrypt(login_args, self.user_info["appKey"])
        }
        resp = requests.post(
            "https://server.17wanxiao.com/campus/cam_iface46/loginnew.action",
            headers={"campusSign": hashlib.sha256(
                json.dumps(upload_args).encode('utf-8')).hexdigest()},
            json=upload_args,
            verify=False
        ).json()
        if resp["result_"]:
            logging.info(f"{username[:4]}：{resp['message_']}")
            self.data = resp["data"]
            self.user_info["login"] = True
            self.user_info["exchangeFlag"] = False
        else:
            logging.info(f"{username[:4]}：{resp['message_']}")
        return resp["result_"]


class login_by_SMS:
    """
    短信登陆
    用于验证虚拟设备
    """

    def __init__(self, username, device_seed):
        """
        初始化；短信登陆类
        :param username: 完美校园账号
        :param device_seed: 用于生成deviceId的种子
        """
        self.seed = int(device_seed)
        self.username = username
        rsa_keys = create_key_pair(1024)
        self.user_info = {
            'appKey': '',
            'sessionId': '',
            'exchangeFlag': True,
            'login': False,
            'serverPublicKey': '',
            'deviceId': self.generate_IMEI(),
            'wanxiaoVersion': "10525101",
            'rsaKey': {
                'private': rsa_keys[1],
                'public': rsa_keys[0]
            }
        }
        self.exchange_secret()

    def exchange_secret(self):
        """
        与完美校园服务器交换RSA加密的公钥，并取得sessionId
        :return:
        """
        resp = requests.post(
            "https://server.17wanxiao.com/campus/cam_iface46/exchangeSecretkey.action",
            headers={
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; HUAWEI INE-AL00 Build/HUAWEIINE-AL00)",
            },
            json={
                "key": self.user_info["rsaKey"]["public"]
            },
            verify=False
        )
        session_info = json.loads(
            rsa_decrypt(resp.text.encode(resp.apparent_encoding),
                        self.user_info["rsaKey"]["private"])
        )
        self.user_info["sessionId"] = session_info["session"]
        self.user_info["appKey"] = session_info["key"][:24]

    def rand(self):
        """
        种子计算 用于生成IMEI
        """
        self.seed = (self.seed * 9301 + 49297) % 233280
        return self.seed / 233280.0

    def generate_IMEI(self):
        """
        生成IMEI
        """
        code = ''
        sum = 0
        for _ in range(12):
            code += str(int(self.rand()*10))
        data = '86' + code
        for index, ch in enumerate(data):
            if index % 2:
                ch = int(ch)*2
                sum += int(ch/10) + ch % 10
            else:
                sum += int(ch)
        data += str(sum * 9 % 10)
        return data

    def sendSMS(self):
        data = des_3_encrypt(json.dumps({
            'action': "registAndLogin",
            'deviceId': self.user_info['deviceId'],
            'mobile':  self.username,
            'requestMethod': "cam_iface46/gainMatrixCaptcha.action",
            'type': "sms"
        }), self.user_info['appKey'], '66666666')

        upload_args = {
            'session': self.user_info['sessionId'],
            'data': data
        }

        resp = requests.post(
            "https://app.59wanmei.com/campus/cam_iface46/gainMatrixCaptcha.action",
            headers={
                "campusSign": hashlib.sha256(
                    json.dumps(upload_args).encode('utf-8')).hexdigest()
            },
            json=upload_args,
            verify=False
        )
        print(resp.text)

    def authSMS(self, sms):
        data = des_3_encrypt(json.dumps({
            'appCode': "M002",
            'deviceId': "866859491137206",
            'netWork': "wifi",
            'qudao': "guanwang",
            'requestMethod': "cam_iface46/registerUsersByTelAndLoginNew.action",
            'shebeixinghao': 'INE-AL00',
            'sms': sms,
            'systemType': 'android',
            'telephoneInfo': '9',
            'telephoneModel': 'HUAWEI INE-AL00',
            'mobile': self.username,
            'wanxiaoVersion': "10525101"
        }), self.user_info['appKey'], '66666666')

        upload_args = {
            'session': self.user_info['sessionId'],
            'data': data
        }

        resp = requests.post(
            "https://app.59wanmei.com/campus/cam_iface46/registerUsersByTelAndLoginNew.action",
            headers={
                "campusSign": hashlib.sha256(
                    json.dumps(upload_args).encode('utf-8')).hexdigest()
            },
            json=upload_args,
            verify=False
        )
        print(resp.text)
