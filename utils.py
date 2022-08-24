import json
import platform
import random
import time
from datetime import datetime

import requests
from colorama import init, Fore
from win10toast import ToastNotifier

normal_color = Fore.CYAN
e_key = "YnJ1aG1vbWVudA==".encode()
BLOCK_SIZE=16
if platform.system() == "Windows":
    init(convert=True)
else:
    init()
print(normal_color + "Welcome To Pi Bot")

class PiLogger:
    def ts(self):
        return str(datetime.now())[:-7]
    def normal(self,task_id,msg):
        print(normal_color + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
    def alt(self,task_id,msg):
        print(Fore.CYAN + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
    def error(self,task_id,msg):
        print(Fore.RED + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
    def success(self,task_id,msg):
        print(Fore.GREEN + "[{}][TASK {}] {}".format(self.ts(),task_id,msg))
def return_data(path):
    with open(path,"r") as file:
        data = json.load(file)
    file.close()
    return data
def write_data(path,data):
    with open(path, "w") as file:
        json.dump(data, file)
    file.close()
def get_profile(profile_name):
    profiles = return_data("./data/profiles.json")
    for p in profiles:
        if p["profile_name"] == profile_name:
            try:
                return p
            except ValueError:
                pass
            return p
    return None
def get_proxy(list_name):
    if list_name == "Proxy List" or list_name == "None":
        return False
    proxies = return_data("./data/proxies.json") 
    for proxy_list in proxies:
        if proxy_list["list_name"] == list_name:
            return format_proxy(random.choice(proxy_list["proxies"].splitlines()))
    return None

def get_proxy_list(list_name):
    if list_name == "Proxy List" or list_name == "None":
        return False
    proxies = return_data("./data/proxies.json")
    for proxy_list in proxies:
        if proxy_list["list_name"] == list_name:
            return proxy_list["proxies"].splitlines()
    return None

def format_proxy(proxy):
    try:
        proxy_parts = proxy.split(":")
        ip, port, user, passw = proxy_parts[0], proxy_parts[1], proxy_parts[2], proxy_parts[3]
        return {
            "http": "http://{}:{}@{}:{}".format(user, passw, ip, port),
            "https": "https://{}:{}@{}:{}".format(user, passw, ip, port)
        }
    except IndexError:
        return {"http": "http://" + proxy, "https": "https://" + proxy}

def get_captcha_cap(url, sitekey):
    settings = return_data("./data/settings.json")
    api_key = settings['capmonsterkey']
    r = requests.Session()
    if api_key == '':
        return 'INVALID_API_KEY'
    else:
        make_task = {'clientKey': api_key,
                     'task': {'type': 'NoCaptchaTaskProxyless', 'websiteURL': url, 'websiteKey': sitekey}}
        print('Requesting captcha')
        r = requests.post("https://api.capmonster.cloud/createTask", json=make_task).json()
        taskId = r['taskId']
        if taskId != 0:
            print('Waiting for captcha')
            get_result = '{"clientKey":"' + api_key + '", "taskId":' + str(taskId) + '}'
            i = 0
            while i < 60:
                r = requests.post('https://api.capmonster.cloud/getTaskResult', data=get_result).json()
                if r["status"] != 'ready':
                    time.sleep(2)
                    i += 1
                else:
                    return r['solution']['gRecaptchaResponse']

def get_captcha_two(url, sitekey):
    settings = return_data("./data/settings.json")
    api_key = settings['2captchakey']
    if api_key == '':
        return 'INVALID_API_KEY'
    else:
        get_url = f'https://2captcha.com/in.php?key={api_key}&method=userrecaptcha&googlekey={sitekey}&pageurl={url}&json=1'
        print('Requesting captcha')
        r = requests.get(get_url).json()
        taskId = r['status']
        if taskId == 1:
            id = r['request']
            print('Waiting for captcha')
            get_result = f'http://2captcha.com/res.php?key={api_key}&action=get&id={id}&json=1'
            i = 0
            while i < 60:
                r = requests.get(get_result).json()
                if r["status"] != 1:
                    time.sleep(2)
                    i += 1
                else:
                    return r['request']

def send_notif(item,mode):
    toast = ToastNotifier()
    try:
        if mode == 'success':
            toast.show_toast('[Pi Bot] Successful Checkout',
                             f'Item bought: {item}',
                             icon_path='icon.ico',
                             duration=8,
                             threaded=True)
        elif mode == 'captcha':
            toast.show_toast('[Pi Bot] Awaiting Captcha',
                             f'Awaiting captcha for: {item}',
                             icon_path='icon.ico',
                             duration=15,
                             threaded=True)
        elif mode == 'fail':
            toast.show_toast('[Pi Bot] Checkout Failed',
                             f'Checkout failed on: {item}',
                             icon_path='icon.ico',
                             duration=8,
                             threaded=True)
    except:
        print('Error sending notification (Most likely non Windows)')
