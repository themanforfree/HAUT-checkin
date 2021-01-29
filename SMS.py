from campus import CampusCard,login_by_SMS
import os 
import sys
username = os.environ.get('USERNAME')
device_seed = os.environ.get('DEVICE_SEED')
t = login_by_SMS(username,device_seed)
if sys.argv[1] == 'send':
    t.sendSMS()
else:
    t.authSMS(sys.argv[1])