import random
import time
from os.path import exists

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import return_data, send_notif, format_proxy, load_session, save_session
from webhook import failed_spark_web, good_spark_web, cart_web

account_items = ['4292', '4295', '4296', '4564', '5291']

class Adafruit:

    def __init__(self, task_id, status_signal, product_signal, product, size, profile, proxy, monitor_delay, error_delay,captcha_type, qty):
        self.task_id, self.status_signal, self.product_signal, self.product,self.size, self.profile, self.monitor_delay, self.error_delay, self.captcha_type, self.qty = task_id, status_signal, product_signal, product,size, profile, monitor_delay, error_delay,captcha_type, qty
        self.session = requests.Session()
        self.proxy_list = proxy
        if self.proxy_list != False:
            self.update_random_proxy()
        self.settings = return_data("./data/settings.json")

        self.pid = ''
        self.image = ''
        self.item = ''
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.security_token = ''
        self.driver = ''
        self.csrf = ''
        self.current = ''
        self.price = ''
        self.current_step = ''

        self.need_chrome = False
        self.product = self.product.split('[')[0].strip()
        self.has_account = False
        self.shipping_method = ''
        if self.acount_needed():
            if not exists('./chromedriver.exe'):
                self.status_signal.emit({"msg": "ChromeDriver.exe not found!", "status": "error"})
                self.need_chrome = True
            else:
                self.get_session()
        if not self.need_chrome:
            self.monitor()
            self.cart()
            self.checkout()

    def acount_needed(self):
        for x in account_items:
            if x in self.product:
                return True
        return False

    def get_headers(self):
        headers = {'authority': 'www.adafruit.com',
                   'scheme': 'https',
                   'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                   'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
                   'sec-ch-ua-mobile': '?0',
                   'sec-ch-ua-platform': '"Windows"',
                   'sec-fetch-dest': 'document',
                   'sec-fetch-site': 'none',
                   'sec-fetch-user': '?1',
                   'upgrade-insecure-requests': '1',
                   'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
                   'cookie': self.request_cookies()}
        return headers

    def get_checkout_token(self, html):
        ind = html.index("csrf_token")
        sub = str(html[ind:])
        spli = sub.split("'")[2]
        return spli

    def get_session(self):
        self.status_signal.emit({"msg": "Checking for session", "status": "normal"})
        session = load_session(self.profile["shipping_email"], 'https://www.adafruit.com/')
        if session == False:
            self.login()
        else:
            for cookies in session[0]:
                self.session.cookies.set(cookies, session[0][cookies], domain='.adafruit.com', path='/')
            self.status_signal.emit({"msg": "Validating session", "status": "normal"})
            account_get = self.session.get('https://accounts.adafruit.com/')
            if 'sign_in' in account_get.url:
                self.status_signal.emit({"msg": "Session no longer valid", "status": "normal"})
                self.login()
            else:
                self.status_signal.emit({"msg": "Valid session found!", "status": "normal"})
                self.has_account = True
    def login(self):
        self.status_signal.emit({"msg": "Awaiting Login", "status": "normal"})
        options = Options()
        options.headless = False
        options.add_argument("window-size=800,600")
        options.add_argument('enable-automation')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-gpu')
        options.add_argument('log-level=3')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('disable-infobars')
        driver = webdriver.Chrome(options=options)
        driver.get('https://accounts.adafruit.com/users/sign_in')
        while True:
            while 'sign_in' in driver.current_url:
                time.sleep(1)
            self.status_signal.emit({"msg": "Checking login session", "status": "normal"})

            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])
                print(cookie['name'], cookie['value'], cookie['domain'], cookie['path'])
            account_check = self.session.get('https://accounts.adafruit.com/')
            if 'sign_in' not in account_check.url:
                self.status_signal.emit({"msg": "Session valid!", "status": "normal"})
                driver.close()
                save_session(self.profile['shipping_email'], 'https://www.adafruit.com/', self.session)
                self.has_account = True
                return
            else:
                self.status_signal.emit({"msg": "Session invalid, please retry", "status": "normal"})
                driver.delete_all_cookies()
                driver.get('https://accounts.adafruit.com/users/sign_in')

    def monitor(self):
        while True:
            self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
            try:
                page_get = self.session.get(str(self.product), headers=self.get_headers())
                if page_get.status_code == 200:
                    soup = BeautifulSoup(page_get.content, 'html.parser')
                    if self.item == '':
                        self.item = str(soup.find_all('meta', {'name': 'twitter:title'})[0].get('content'))
                        self.product_signal.emit(f'{self.item} [{self.qty}]')
                    if self.image == '':
                        self.image = str(soup.find_all('meta', {'name': 'twitter:image:src'})[0].get('content'))
                    stock = str(soup.find_all('meta', {'name': 'twitter:data2'})[0].get('content')).lower()
                    if stock == 'out of stock':
                        self.status_signal.emit({"msg": "Waiting for restock", "status": "monitoring"})
                        self.update_random_proxy()
                        time.sleep(float(self.monitor_delay))
                    else:
                        self.pid = soup.find('input', {'name': 'pid'}).get('value')
                        self.security_token = soup.find('input', {'name': 'securityToken'}).get('value')
                        break
                else:
                    self.status_signal.emit({"msg": f"Error on monitor [{page_get.status_code}]", "status": "error"})
                    self.update_random_proxy()
                    time.sleep(float(self.error_delay))
            except:
                self.status_signal.emit({"msg": f"Error on monitor", "status": "error"})
                self.update_random_proxy()
                time.sleep(float(self.error_delay))

    def cart(self):
        self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
        cart_url = 'https://www.adafruit.com/added'
        cart_form = {'securityToken': self.security_token,
                     'action': 'add_product',
                     'pid': self.pid,
                     'qty': self.qty,
                     'source_page': 'product',
                     'source_id': self.pid}

        cart_add = self.session.post(cart_url, data=cart_form, headers=self.get_headers())
        if cart_add.status_code == 200:
            soup = BeautifulSoup(cart_add.content, 'html.parser')
            if 'Added to Adafruit' in soup.find('title').string:
                self.status_signal.emit({"msg": "Carted", "status": "carted"})
                if self.settings['webhookcart']:
                    cart_web(self.product, self.image, 'Adafruit (Guest)', self.item,
                             self.profile['profile_name'])

                self.status_signal.emit({"msg": "Navigating to cart", "status": "normal"})
                cart_get = self.session.get('https://www.adafruit.com/shopping_cart', headers=self.get_headers())
                soup = BeautifulSoup(cart_get.content, 'html.parser')
                security_token = soup.find('input', {'name': 'securityToken'}).get('value')

                cart_change_form = {'action': 'update_quantity',
                                    'pid': self.pid,
                                    'qty': self.qty,
                                    'securityToken': security_token,
                                    'return_full_cart': 1}

                for carted in soup.find_all('div', {'class': 'cart-row'}):
                    pid = str(carted.get('data-pid'))
                    print(f'In Cart: {pid}')
                    if pid != self.pid:
                        cart_delete_form = {'action': 'delete_product',
                                            'pid': pid,
                                            'securityToken': security_token,
                                            'return_full_cart': 1}
                        self.status_signal.emit({"msg": f"Deleting PID from cart: {pid}", "status": "normal"})
                        cart_del_post = self.session.post('https://www.adafruit.com/api/wildCart.php',
                                                             headers=self.get_headers(), data=cart_delete_form)

                self.status_signal.emit({"msg": f"Force Set Quantity [{self.qty}]", "status": "normal"})
                cart_change_post = self.session.post('https://www.adafruit.com/api/wildCart.php', headers=self.get_headers(), data=cart_change_form)
                self.status_signal.emit({"msg": "Redirecting to checkout", "status": "normal"})
                checkout_get = self.session.get('https://www.adafruit.com/checkout', headers=self.get_headers())
                if 'step=' in checkout_get.url:
                    soup = BeautifulSoup(checkout_get.content, 'html.parser')
                    self.current_step = checkout_get.url.split('=')[1]
                    self.csrf = soup.find('input', {'name': 'csrf_token'}).get('value')
                else:
                    self.status_signal.emit({"msg": "Error redirecting", "status": "error"})
                    print(checkout_get.text)

    def checkout(self):
        profile = self.profile
        checkout_url = 'https://www.adafruit.com/checkout'
        if self.current_step == '1':
            self.status_signal.emit({"msg": "Submitting Email", "status": "normal"})
            step_1_form = {'csrf_token': self.csrf,
                           'email_address': profile['shipping_email'],
                           'checkout_guest': 1,
                           'action': 'save_one'}

            step_1_post = self.session.post(checkout_url, data=step_1_form, headers=self.get_headers())

            if 'permanently disabled certain email addresses' in step_1_post.text:
                self.status_signal.emit({"msg": "Email Banned", "status": "error"})
                return
            elif 'step=2' in step_1_post.url:
                self.current_step = '2'
        if self.current_step == '2':
            self.status_signal.emit({"msg": "Submitting Address", "status": "normal"})
            step_2_form = {'csrf_token': self.csrf,
                           'delivery_use_anyways': 1,
                           'delivery_name': f"{profile['shipping_fname']} {profile['shipping_lname']}",
                           'delivery_company': '',
                           'delivery_address1': profile['shipping_a1'],
                           'delivery_address2': profile['shipping_a2'],
                           'delivery_city': profile['shipping_city'],
                           'delivery_state': self.get_shipping_zone(),
                           'delivery_postcode': profile['shipping_zipcode'],
                           'delivery_country': 223,
                           'delivery_phone': profile['shipping_phone'],
                           'action': 'save_two'}

            step_2_post = self.session.post(checkout_url, data=step_2_form, headers=self.get_headers())
            if 'permanently disabled certain shipping' in step_2_post.text:
                self.status_signal.emit({"msg": "Address Banned", "status": "error"})
                return
            elif 'step=3' in step_2_post.url:
                self.current_step = '3'
                soup = BeautifulSoup(step_2_post.content, 'html.parser')
                self.shipping_method = soup.find_all('input', {'data-module': 'usps'})[0].get('value')
        if self.current_step == '3':
            self.status_signal.emit({"msg": "Submitting shipping method", "status": "normal"})
            step_3_form = {'csrf_token': self.csrf,
                           'shipping': self.shipping_method,
                           'action': 'save_three'}
            step_3_post = self.session.post(checkout_url, data=step_3_form, headers=self.get_headers())
            if 'step=4' in step_3_post.url:
                self.current_step = '4'
        if self.current_step == '4':
            self.status_signal.emit({"msg": "Submitting payment", "status": "normal"})
            step_4_form = {'csrf_token' : self.csrf,
                           'action': 'save_four',
                           'payment': 'authorizenet_aim',
                           'authorizenet_aim_cc_owner': f"{profile['shipping_fname']} {profile['shipping_lname']}",
                           'authorizenet_aim_cc_number': profile['card_number'],
                           'authorizenet_aim_cc_expires_month': profile['card_month'],
                           'authorizenet_aim_cc_expires_year': profile['card_year'],
                           'authorizenet_aim_cc_cvv': profile['card_cvv'],
                           'card-type': 'amex',
                           'po_payment_type': 'replacement'}
            try:
                soup = BeautifulSoup(step_3_post.content, 'html.parser')
                step_4_form["acp_id"] = soup.find('input', {'name': 'acp_id'}).get('value')
            except:
                print("Couldn't find acp_id")

            step_4_post = self.session.post(checkout_url, data=step_4_form, headers=self.get_headers())



            if step_4_post.url == 'https://www.adafruit.com/checkout':
                self.status_signal.emit({"msg": "Submitting order", "status": "alt"})
                soup = BeautifulSoup(step_4_post.content, 'html.parser')
                values = ['cc_owner', 'cc_expires', 'cc_type', 'cc_number', 'cc_cvv', 'zenid']
                final_checkout_form = {'csrf_token': self.csrf, 'cc_nickname': ''}

                for value in values:
                    final_checkout_form[value] = soup.find('input', {'name': value}).get('value')

                final_post = self.session.post('https://www.adafruit.com/index.php?main_page=checkout_process', data=final_checkout_form, headers=self.get_headers())
                print(final_post.text)
                if 'Your credit card could not be authorized' in final_post.text:
                    self.status_signal.emit({"msg": "Checkout Failed (Card Decline)", "status": "error"})
                    if self.settings['webhookfailed']:
                        failed_spark_web(self.product, self.image,'Adafruit (Guest)', self.item, self.profile["profile_name"])
                    if self.settings['notiffailed']:
                        send_notif(self.item, 'fail')
                elif 'checkout_success' in final_post.url:
                    self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                    if self.settings['webhooksuccess']:
                        good_spark_web({str(self.product)}, self.image,'Adafruit (Guest)',self.item, self.profile["profile_name"])
                    if self.settings['notifsuccess']:
                        send_notif(self.item, 'success')
                else:
                    self.status_signal.emit({"msg": "Checkout Failed (Other)", "status": "error"})
                    if self.settings['webhookfailed']:
                        failed_spark_web(self.product, self.image,'Adafruit (Guest)', self.item, self.profile["profile_name"])
                    if self.settings['notiffailed']:
                        send_notif(self.item, 'fail')


    def get_shipping_zone(self):
        zones = [{"id":1,"name":"Alabama","code":"AL"},{"id":2,"name":"Alaska","code":"AK"},{"id":3,"name":"American Samoa","code":"AS"},{"id":4,"name":"Arizona","code":"AZ"},{"id":5,"name":"Arkansas","code":"AR"},{"id":7,"name":"Armed Forces Americas","code":"AA"},{"id":9,"name":"Armed Forces Europe","code":"AE"},{"id":11,"name":"Armed Forces Pacific","code":"AP"},{"id":12,"name":"California","code":"CA"},{"id":13,"name":"Colorado","code":"CO"},{"id":14,"name":"Connecticut","code":"CT"},{"id":15,"name":"Delaware","code":"DE"},{"id":16,"name":"District of Columbia","code":"DC"},{"id":17,"name":"Federated States Of Micronesia","code":"FM"},{"id":18,"name":"Florida","code":"FL"},{"id":19,"name":"Georgia","code":"GA"},{"id":20,"name":"Guam","code":"GU"},{"id":21,"name":"Hawaii","code":"HI"},{"id":22,"name":"Idaho","code":"ID"},{"id":23,"name":"Illinois","code":"IL"},{"id":24,"name":"Indiana","code":"IN"},{"id":25,"name":"Iowa","code":"IA"},{"id":26,"name":"Kansas","code":"KS"},{"id":27,"name":"Kentucky","code":"KY"},{"id":28,"name":"Louisiana","code":"LA"},{"id":29,"name":"Maine","code":"ME"},{"id":30,"name":"Marshall Islands","code":"MH"},{"id":31,"name":"Maryland","code":"MD"},{"id":32,"name":"Massachusetts","code":"MA"},{"id":33,"name":"Michigan","code":"MI"},{"id":34,"name":"Minnesota","code":"MN"},{"id":35,"name":"Mississippi","code":"MS"},{"id":36,"name":"Missouri","code":"MO"},{"id":37,"name":"Montana","code":"MT"},{"id":38,"name":"Nebraska","code":"NE"},{"id":39,"name":"Nevada","code":"NV"},{"id":40,"name":"New Hampshire","code":"NH"},{"id":41,"name":"New Jersey","code":"NJ"},{"id":42,"name":"New Mexico","code":"NM"},{"id":43,"name":"New York","code":"NY"},{"id":44,"name":"North Carolina","code":"NC"},{"id":45,"name":"North Dakota","code":"ND"},{"id":46,"name":"Northern Mariana Islands","code":"MP"},{"id":47,"name":"Ohio","code":"OH"},{"id":48,"name":"Oklahoma","code":"OK"},{"id":49,"name":"Oregon","code":"OR"},{"id":50,"name":"Palau","code":"PW"},{"id":51,"name":"Pennsylvania","code":"PA"},{"id":52,"name":"Puerto Rico","code":"PR"},{"id":53,"name":"Rhode Island","code":"RI"},{"id":54,"name":"South Carolina","code":"SC"},{"id":55,"name":"South Dakota","code":"SD"},{"id":56,"name":"Tennessee","code":"TN"},{"id":57,"name":"Texas","code":"TX"},{"id":58,"name":"Utah","code":"UT"},{"id":59,"name":"Vermont","code":"VT"},{"id":61,"name":"Virginia","code":"VA"},{"id":60,"name":"Virgin Islands","code":"VI"},{"id":62,"name":"Washington","code":"WA"},{"id":63,"name":"West Virginia","code":"WV"},{"id":64,"name":"Wisconsin","code":"WI"},{"id":65,"name":"Wyoming","code":"WY"}]
        for zone in zones:
            if self.profile['shipping_state'] == zone['code']:
                return zone['id']

    def request_cookies(self):
        cook_string = ''
        for cook in self.session.cookies:
            cook_string += f'; {cook.name}={cook.value}'
        return cook_string[2:]

    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(format_proxy(random.choice(self.proxy_list)))
