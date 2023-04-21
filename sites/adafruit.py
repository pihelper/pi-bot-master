import json
import random
import time

import requests
import pyotp
from bs4 import BeautifulSoup

from utils import return_data, send_notif, format_proxy
from webhook import new_web

class Adafruit:

    def __init__(self, task_id, status_signal, product_signal, product, size, profile, proxy, monitor_delay, error_delay,captcha_type, qty):
        self.task_id, self.status_signal, self.product_signal, self.product,self.size, self.profile, self.monitor_delay, self.error_delay, self.captcha_type, self.qty= task_id, status_signal, product_signal, product,size, profile, monitor_delay, error_delay,captcha_type, qty
        self.session = requests.Session()
        self.proxy_list = proxy
        if self.proxy_list != False:
            self.update_random_proxy()

        self.user = self.profile.split('|')[1]
        self.pw = self.profile.split('|')[2]
        otp_secret = str(self.profile.split('|')[3]).strip()
        self.otp = pyotp.TOTP(otp_secret)
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
        self.zenid = ''
        self.acp_id = ''
        self.address = ''

        self.product = self.product.split('[')[0].strip()
        self.has_account = False
        self.shipping_method = ''
        self.request_login()
        self.monitor()
        self.cart()
        self.checkout()

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

    def request_login(self):
        login_url = 'https://accounts.adafruit.com/users/sign_in'
        auth = ''
        while auth == '':
            self.status_signal.emit({"msg": "Getting Auth", "status": "normal"})
            auth_get = self.session.get(login_url, headers=self.get_headers())
            if auth_get.status_code == 200:
                soup = BeautifulSoup(auth_get.content, 'html.parser')
                auth = soup.find('meta', {'name': 'csrf-token'}).get('content')
            else:
                self.status_signal.emit({"msg": "Error getting auth, retrying", "status": "error"})
                time.sleep(float(self.error_delay))
        while True:
            self.status_signal.emit({"msg": "Logging In (Email/Pass)", "status": "normal"})
            email_login_form = {
                'authenticity_token': auth,
                'user[login]': self.user,
                'user[password]': self.pw,
                'commit': 'SIGN IN'
            }
            email_post = self.session.post(login_url, data=email_login_form, headers=self.get_headers())
            if 'TWO FACTOR AUTH' in email_post.text:
                self.status_signal.emit({"msg": "Logging In (2FA)", "status": "normal"})
                otp_form = {
                    'authenticity_token': auth,
                    'user[otp_attempt]': self.otp.now(),
                    'commit': 'VERIFY'
                }
                opt_post = self.session.post(login_url, data=otp_form, headers=self.get_headers())
                account_check = self.session.get('https://accounts.adafruit.com/')
                if 'sign_in' not in account_check.url:
                    self.status_signal.emit({"msg": "Successfully logged in", "status": "normal"})
                    break
                else:
                    self.status_signal.emit({"msg": "Error OTP, retrying in 30s", "status": "error"})
                    time.sleep(30)
            else:
                self.status_signal.emit({"msg": "Error logging in, retrying", "status": "error"})
                time.sleep(float(self.error_delay))

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
                self.start_time = time.time()
                if self.settings['webhookcart']:
                    new_web('carted', 'Adafruit', self.image, self.item, self.user)

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
                    #print(checkout_get.url)
                    soup = BeautifulSoup(checkout_get.content, 'html.parser')
                    self.current_step = checkout_get.url.split('=')[1]
                    self.csrf = soup.find('input', {'name': 'csrf_token'}).get('value')

                    if 'step=2' in checkout_get.url:
                        saved_address = soup.find_all(['select'])[0].find_all(['option'])[0]
                        self.address = json.loads(saved_address.get('data-address'))
                        #print(self.address)
                else:
                    self.status_signal.emit({"msg": "Error redirecting", "status": "error"})

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

            blacklist_keys = ['firstname', 'lastname', 'country', 'label', 'country_id', 'state', 'zone_id']

            step_2_form = {'csrf_token': self.csrf,
                           'action': 'save_two',
                           'delivery_use_anyways': 0,
                           'billing_use_anyways': 0}

            for value in self.address:
                if value not in blacklist_keys:
                    step_2_form[f'delivery_{value}'] = self.address[value]
                    step_2_form[f'billing_{value}'] = self.address[value]

            step_2_form['delivery_country'] = self.address['country_id']
            step_2_form['billing_country'] = self.address['country_id']

            step_2_form['delivery_state'] = self.address['zone_id']
            step_2_form['billing_state'] = self.address['zone_id']

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
                           'payment': 'authorizenet_cim',
                           'authorizenet_aim_cc_number': '',
                           'authorizenet_aim_cc_expires_month': '0',
                           'authorizenet_aim_cc_expires_year': '0',
                           'authorizenet_aim_cc_cvv': '',
                           'authorizenet_aim_cc_nickname': '',
                           'card-type': 'amex',
                           'po_payment_type': 'replacement'}
            try:
                soup = BeautifulSoup(step_3_post.content, 'html.parser')
                self.acp_id = soup.find('input', {'name': 'acp_id'}).get('value')
                step_4_form["acp_id"] = self.acp_id
                step_4_form['authorizenet_aim_cc_owner'] = soup.find_all('label', {'class': 'checkout-payment-method-label'})[0].text.split('-')[0].strip()
            except:
                self.status_signal.emit({"msg": "No saved card on account", "status": "error"})
                if self.settings['webhookfailed']:
                    new_web('failed', 'Adafruit', self.image, self.item, self.user)
                if self.settings['notiffailed']:
                    send_notif(self.item, 'fail')
                return

            step_4_post = self.session.post(checkout_url, data=step_4_form, headers=self.get_headers())

            if step_4_post.url == 'https://www.adafruit.com/checkout':
                self.status_signal.emit({"msg": "Submitting order", "status": "alt"})
                soup = BeautifulSoup(step_4_post.content, 'html.parser')
                final_checkout_form = {'csrf_token': self.csrf, 'acp_id': self.acp_id}
                try:
                    final_checkout_form['zenid'] = soup.find('input', {'name': 'zenid'}).get('value')
                except:
                    print("Could not fetch ZenID")
                final_post = self.session.post('https://www.adafruit.com/index.php?main_page=checkout_process', data=final_checkout_form, headers=self.get_headers())
                end_time = time.time() - self.start_time
                if 'Your credit card could not be authorized' in final_post.text:
                    self.status_signal.emit({"msg": "Checkout Failed (Card Decline)", "status": "error"})
                    if self.settings['webhookfailed']:
                        new_web('failed', 'Adafruit', self.image, self.item, self.user, checkout_time=end_time)
                    if self.settings['notiffailed']:
                        send_notif(self.item, 'fail')
                elif 'checkout_success' in final_post.url:
                    self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                    if self.settings['webhooksuccess']:
                        new_web('success', 'Adafruit', self.image, self.item, self.user, checkout_time=end_time)
                    if self.settings['notifsuccess']:
                        send_notif(self.item, 'success')
                else:
                    self.status_signal.emit({"msg": "Checkout Failed (Other)", "status": "error"})
                    if self.settings['webhookfailed']:
                        new_web('failed', 'Adafruit', self.image, self.item, self.user, checkout_time=end_time)
                    if self.settings['notiffailed']:
                        send_notif(self.item, 'fail')


    def request_cookies(self):
        cook_string = ''
        for cook in self.session.cookies:
            cook_string += f'; {cook.name}={cook.value}'
        return cook_string[2:]

    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(format_proxy(random.choice(self.proxy_list)))
