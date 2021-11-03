from campus import login_by_SMS

# 此脚本用于验证虚拟设备
# device_seed输入任意数字
# 密码登陆时需传入相同的device seed

print('username:', end="")
username = input()
print('device seed:', end="")
device_seed = input()

t = login_by_SMS(username, device_seed)
t.sendSMS()

print('SMS code:', end="")
t.authSMS(input())
