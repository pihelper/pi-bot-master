import random
import time
import traceback
from os.path import exists

import requests, re
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import return_data, format_proxy
from webhook import good_web, failed_web, cart_web


class Shop:
    def __init__(self, task_id, status_signal, product_signal, product, info, size, profile, proxy, monitor_delay, error_delay):
        self.task_id, self.status_signal, self.product_signal, self.product, self.info, self.size, self.profile, self.monitor_delay, self.error_delay = task_id, status_signal, product_signal, product, info, size, profile,monitor_delay, error_delay
        self.session = requests.Session()
        self.settings = return_data("./data/settings.json")
        self.proxy_list = proxy
        self.session.verify = False
        self.product_json = self.size.split('|')[0]
        self.handle = self.size.split('|')[1]
        self.size_kw = self.size.split('|')[2]
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if self.proxy_list != False:
            self.update_random_proxy()
        self.image = ''
        self.main_site = self.info
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.proxy_to_use = self.update_random_proxy()

        needs_chrome = False

        if 'pimoroni' in self.main_site:
            if exists('./chromedriver.exe'):
                self.browser_login()
            else:
                self.status_signal.emit({"msg": "No ChromeDriver found!", "status": "error"})
                needs_chrome = True

        if not needs_chrome:
            req = self.atc()
            self.main_url = req.url
            self.auth_token, self.shipping_rate = self.get_tokens(req)
            self.submit_shipping()
            self.submit_rates()
            self.price, self.gateway = self.calc_taxes()
            self.submit_payment()

    def get_checkout_token(self, html):
        ind = html.index("authenticity_token")
        sub = str(html[ind:])
        spli = sub.split("\"")[2]
        return spli

    def compare_kw(self, item_name, kws):
        item_comp = item_name.lower()
        for keyword in kws:
            kw = str(keyword).lower()
            if '-' in keyword:
                if kw[1::] in item_comp:
                    return False
            else:
                if kw not in item_comp:
                    return False
        return True

    def get_gateway(self, html):
        ind = html.index("data-select-gateway=")
        sub = str(html[ind:])
        spli = sub.split("\"")[1]
        return spli

    def get_price(self, html):
        ind = html.index('data-checkout-payment-due-target="')
        sub = str(html[ind:])
        spli = sub.split("\"")[1]
        return spli

    def format_phone(self, phone):
        return '+1' + re.sub('[^A-Za-z0-9]+', '', phone).strip()

    def format_phone2(self, phone):
        phony = re.sub('[^A-Za-z0-9]+', '', phone).strip()
        return '(' + phony[:3] + ') ' + phony[3:6] + "-" + phony[-4:]

    def browser_login(self):
        while True:
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
            driver.get(str(self.main_site + 'account/login'))

            while 'login' in driver.current_url or '/challenge' in driver.current_url:
                time.sleep(0.1)

            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
            driver.close()
            self.status_signal.emit({"msg": "Checking login session", "status": "normal"})
            get = self.session.get(f'{self.main_site}account')
            if 'login?' not in get.url:
                self.status_signal.emit({"msg": "Valid session found", "status": "normal"})
                return
            else:
                self.status_signal.emit({"msg": "Session failed", "status": "error"})
    def atc(self):
        variant = ''
        found = ''
        while True:
            try:
                if variant == '':
                    if found == '':
                        self.status_signal.emit({"msg": "Searching for product", "status": "checking"})
                        found = False
                    elif found:
                        self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
                    products = self.session.get(self.main_site + self.product_json)
                    if products.status_code == 200:
                        products = products.json()['products']
                        for prod in products:
                            handle = prod['handle']
                            if handle == self.handle:
                                found = True
                                self.image = prod['images'][0]['src']
                                for vr in prod['variants']:
                                    if self.compare_size(vr['title']):
                                        if vr['available']:
                                            self.status_signal.emit(
                                                {"msg": "Adding to cart", "status": "normal"})
                                            variant = vr['id']
                                            break
                                        else:
                                            self.status_signal.emit(
                                                {"msg": "Waiting for restock", "status": "monitoring"})
                                            self.update_random_proxy()
                                            time.sleep(float(self.monitor_delay))
                                break
                        if not found:
                            self.status_signal.emit({"msg": "Waiting for product", "status": "monitoring"})
                            self.update_random_proxy()
                            time.sleep(float(self.monitor_delay))
                    elif products.status_code == 430:
                        self.status_signal.emit({"msg": f'IP Rate Limited!', "status": "error_no_log"})
                        self.update_random_proxy()
                        time.sleep(float(self.error_delay))
                    else:
                        self.status_signal.emit({"msg": f'Error getting stock [{products.status_code}]', "status": "error"})
                        self.update_random_proxy()
                        time.sleep(float(self.error_delay))
                elif variant != '':
                    cart = {'utf8': '✓', 'form_type': 'product', 'id': variant, 'quantity': '1'}
                    self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
                    url_to_post = f'{self.main_site}cart/add.js'
                    self.session.post(url_to_post, data=cart, headers=self.request_headers(self.main_site))
                    cart_json = self.session.get(f'{self.main_site}cart.js').json()
                    if cart_json['item_count'] == 0:
                        self.status_signal.emit({"msg": "Adding to cart (Alt)", "status": "normal"})
                        req = self.session.get(f'{self.main_site}cart/{variant}:1')
                    else:
                        req = self.session.get(f'{self.main_site}checkout')
                    if ('checkout' in req.url) and 'stock_problem' not in req.url:
                        self.status_signal.emit({"msg": "Added to Cart", "status": "carted"})
                        if self.settings['webhookcart']:
                            cart_web(self.main_site, self.image, self.main_site, self.product, self.profile['profile_name'])
                        return req
                    elif 'checkout' in req.url and 'stock_problems' in req.url:
                        self.status_signal.emit({"msg": "Monitoring (Carted)", "status": "carted"})
                        cart_time = req.url.replace('/stock_problems','')
                        while True:
                            time.sleep(float(self.monitor_delay))
                            check_cart = self.session.get(cart_time)
                            if check_cart.status_code == 429:
                                self.status_signal.emit({"msg": "Genning new session", "status": "idle"})
                                break
                            elif check_cart.status_code == 200:
                                if 'stock_problems' in check_cart.url:
                                    time.sleep(float(self.monitor_delay))
                                else:
                                    return check_cart
                            else:
                                time.sleep(float(self.monitor_delay))
                    else:
                        self.status_signal.emit({"msg": "Error on redirect", "status": "error"})
                        print(req.url)
                        self.session.cookies.clear()
                        time.sleep(float(self.error_delay))
            except Exception:
                self.status_signal.emit({"msg": "Error getting product info", "status": "error"})
                time.sleep(float(self.error_delay))

    def get_tokens(self,req):
        profile = self.profile
        while True:
            try:
                self.status_signal.emit({"msg": "Getting Auth Token", "status": "normal"})
                auth_token = self.get_checkout_token(req.text)
                break
            except:
                self.status_signal.emit({"msg": "Error Fetching Auth", "status": "error"})
                time.sleep(float(self.error_delay))
        while True:
            try:
                self.status_signal.emit({"msg": "Getting Shipping Rates", "status": "normal"})
                jayson = self.session.get(f'{self.main_site}cart/shipping_rates.json?shipping_address[zip]={str(profile["shipping_zipcode"]).replace(" ","")}&shipping_address[country]={self.get_country_code()}&shipping_address[province]={profile["shipping_state"]}').json()
                full_rate = f'{jayson["shipping_rates"][0]["source"]}-{jayson["shipping_rates"][0]["code"]}-{jayson["shipping_rates"][0]["price"]}'
                break
            except:
                self.status_signal.emit({"msg": "Error Fetching Shipping Rate", "status": "error"})
                print(f'Shipping rate response -> {jayson}')
                time.sleep(float(self.error_delay))
        return auth_token, full_rate

    def submit_shipping(self):
        while True:
            try:
                profile = self.profile
                x = {'_method': 'patch',
                     'authenticity_token': self.auth_token,
                     'previous_step': 'contact_information',
                     'step': 'shipping_method',
                     'checkout[buyer_accepts_marketing]': '0',
                     'checkout[shipping_address][first_name]': profile['shipping_fname'],
                     'checkout[shipping_address][last_name]': profile['shipping_lname'],
                     'checkout[shipping_address][address1]': profile['shipping_a1'],
                     'checkout[shipping_address][address2]': profile['shipping_a2'],
                     'checkout[shipping_address][city]': profile['shipping_city'],
                     'checkout[shipping_address][country]': profile['shipping_country'],
                     'checkout[shipping_address][zip]': profile['shipping_zipcode'],
                     'checkout[shipping_address][phone]': self.format_phone2(profile["shipping_phone"]),
                     'checkout[email]': profile['shipping_email'],
                     'checkout[client_details][browser_width]': '1009',
                     'checkout[client_details][browser_height]': '947',
                     'checkout[client_details][javascript_enabled]': '1',
                     'checkout[client_details][color_depth]': '24',
                     'checkout[client_details][java_enabled]': 'false',
                     'checkout[client_details][browzer_tz]': '240'
                     }
                if profile['shipping_state'] != '':
                    x['checkout[shipping_address][province]'] = profile['shipping_state'],
                self.status_signal.emit({"msg": "Submitting Shipping Info", "status": "normal"})
                self.session.post(self.main_url,data=x, headers=self.request_headers(self.main_url + '?step=contact_information'))
                return
            except:
                self.status_signal.emit({"msg": "Error Submitting Shipping", "status": "error"})
                time.sleep(float(self.error_delay))

    def submit_rates(self):
       while True:
           try:
                x = {'_method': 'patch',
                     'authenticity_token': self.auth_token,
                     'previous_step': 'shipping_method',
                     'step': 'payment_method',
                     'checkout[shipping_rate][id]': self.shipping_rate.replace(" ", '%20'),
                     'checkout[client_details][browser_width]': '1009',
                     'checkout[client_details][browser_height]': '947',
                     'checkout[client_details][javascript_enabled]': '1',
                     'checkout[client_details][color_depth]': '24',
                     'checkout[client_details][java_enabled]': 'false',
                     'checkout[client_details][browzer_tz]': '240'
                     }
                self.status_signal.emit({"msg": "Submitting Shipping Rate", "status": "normal"})
                r = self.session.post(self.main_url, headers=self.request_headers(self.main_url + '?previous_step=shipping_method&step=payment_method'), data=x, allow_redirects=True)
                if not 'step=payment_method' in r.url:
                    x = {'_method': 'patch',
                         'authenticity_token': self.auth_token,
                         'previous_step': 'shipping_method',
                         'step': 'payment_method',
                         'checkout[shipping_rate][id]': self.shipping_rate,
                         'checkout[client_details][browser_width]': '1009',
                         'checkout[client_details][browser_height]': '947',
                         'checkout[client_details][javascript_enabled]': '1',
                         'checkout[client_details][color_depth]': '24',
                         'checkout[client_details][java_enabled]': 'false',
                         'checkout[client_details][browzer_tz]': '240'
                         }
                    self.status_signal.emit({"msg": "Submitting Shipping Rate (Alt)", "status": "normal"})
                    r2 = self.session.post(self.main_url, headers=self.request_headers(f'{self.main_url}?previous_step=shipping_method&step=payment_method'), data=x, allow_redirects=True)
                    if 'step=payment_method' in r2.url:
                        return
                    else:
                        self.status_signal.emit({"msg": "Error submitting rates", "status": "error"})
                        time.sleep(float(self.error_delay))
                else:
                    return
           except Exception as e:
               self.status_signal.emit({"msg": "Error submitting rates", "status": "error"})
               time.sleep(float(self.error_delay))

    def calc_taxes(self):
        while True:
            try:
                self.status_signal.emit({"msg": "Calculating Tax", "status": "normal"})
                rate_after = self.session.get(f'{self.main_url}?step=payment_method', allow_redirects=True)
                price = self.get_price(rate_after.text)
                gateway = self.get_gateway(rate_after.text)
                return price,gateway
            except:
                self.status_signal.emit({"msg": "Error Calculating Tax", "status": "error"})
                time.sleep(float(self.error_delay))

    def submit_payment(self):
        self.status_signal.emit({"msg": "Encrypting Payment", "status": "normal"})
        profile = self.profile
        url_to_use = self.main_site.replace("https://", '').replace('www.', '')
        x = '{"credit_card":{"number":"' + profile["card_number"] + '","name":"' + f'{profile["shipping_fname"]} {profile["shipping_lname"]}' + '","month":' + str(int(profile["card_month"])) + ',"year":' + profile["card_year"] + ',"verification_value":"' + profile["card_cvv"] + '"}, "payment_session_scope": "' + url_to_use + '"}'
        card_payload = str(x).replace('\n', '')
        shopify_cs_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://checkout.shopifycs.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://checkout.shopifycs.com/'

        }
        encrypt = self.session.post('https://deposit.us.shopifycs.com/sessions', headers=shopify_cs_headers, data=card_payload, verify=False)
        encrypt_info = encrypt.json()['id']

        x = {'_method': 'patch',
             'authenticity_token': self.auth_token,
             'previous_step': 'payment_method',
             'step': '',
             's': encrypt_info,
             'checkout[payment_gateway]': self.gateway,
             'checkout[credit_card][vault]': 'false',
             'checkout[different_billing_address]': 'false',
             'checkout[vault_phone]': self.format_phone(profile['shipping_phone']),
             'checkout[total_price]': self.price,
             'complete': '1',
             'checkout[client_details][browser_width]': '1009',
             'checkout[client_details][browser_height]': '947',
             'checkout[client_details][javascript_enabled]': '1',
             'checkout[client_details][color_depth]': '24',
             'checkout[client_details][java_enabled]': 'false',
             'checkout[client_details][browzer_tz]': '240'
             }
        self.status_signal.emit({"msg": "Submitting Payment", "status": "normal"})

        submit = self.session.post(self.main_url, allow_redirects=True, headers=self.request_headers(self.main_url),data=x)
        if ('processing' in submit.url) or 'authentications' in submit.url:
            self.status_signal.emit({"msg": "Processing", "status": "alt"})
            pay_url = submit.url + "?from_processing_page=1"
            while True:
                after = self.session.get(pay_url, allow_redirects=True)
                if 'Thanks for your order' in after.text:
                    print('Good!')
                    break
                if 'authentications' in after.url:
                    self.status_signal.emit({"msg": "Processing (UK Auth)", "status": "alt"})
                    keys = after.url.split("/")
                    cardinal_key = keys[len(keys)-1]

                    while True:
                        auth_get = self.session.get(f'{after.url}/poll?authentication={cardinal_key}')
                        if auth_get.status_code == 200:
                            break
                        else:
                            time.sleep(1)

                    self.status_signal.emit({"msg": "Processing (Passing Auth)", "status": "alt"})
                    after = self.session.get(f'{auth_get.url}?')
                    if '/processing' in after.url:
                        self.status_signal.emit({"msg": "Processing", "status": "alt"})
                        base_url = after.url
                        while True:
                            pay_url = base_url + "?from_processing_page=1"
                            after = self.session.get(pay_url)
                            if '/processing' in after.url:
                                time.sleep(1)
                            else:
                                print(after.url)
                                break

                elif '/processing' in after.url:
                    time.sleep(1)
                else:
                    print(after.url)
                    break
            if '&validate=true' in after.url:
                price_to_use = int(self.price)/100
                self.status_signal.emit({"msg": "Checkout Failed", "status": "error"})
                failed_web(after.url,self.image,f'{self.main_site}',self.product,self.profile["profile_name"], "{:.2f}".format(price_to_use))

            elif 'thank_you' in after.url:
                price_to_use = int(self.price)/100
                self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                good_web(after.url, self.image, f'{self.main_site}',
                       self.product, self.profile["profile_name"],
                       "{:.2f}".format(price_to_use))

            else:
                self.status_signal.emit({"msg": "Checking order", "status": "alt"})
                price_to_use = int(self.price)/100
                r = self.session.get(self.main_url + "/thank_you")
                if r.url.endswith('/processing'):
                    self.status_signal.emit({"msg": "Checking order (Processing)", "status": "alt"})
                    while True:
                        time.sleep(2)
                        r = self.session.get(r.url)
                        if not r.url.endswith('/processing'):
                            break

                if 'order' in r.url or 'thank_you' in r.url:
                    self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                    if self.settings['webhooksuccess']:
                        good_web(r.url, self.image, f'Custom Shopify - {self.main_site}',
                                 self.product, self.profile["profile_name"],
                                 "{:.2f}".format(price_to_use))
                else:
                    self.status_signal.emit({"msg": "Checkout Failed", "status": "error"})
                    if self.settings['webhookfail']:
                        failed_web(r.url, self.image, f'Custom Shopify - {self.main_site}', self.product,
                                   self.profile["profile_name"], "{:.2f}".format(price_to_use))

        else:
            price_to_use = int(self.price) / 100
            failed_web(submit.url, self.image, f'Custom Shopify - {self.main_site}', self.product,
                       self.profile["profile_name"], "{:.2f}".format(price_to_use))

    def request_headers(self, url):
        x = {'Content-Type': 'application/x-www-form-urlencoded',
             "Accept": 'application/json, text/javascript, */*; q=0.01',
             'sec-fetch-site': 'same-origin',
             'sec-fetch-mode': 'navigate',
             'sec-fetch-user': '?1',
             'sec-fetch-dest': 'document',
             'sec-ch-ua-mobile': '?0',
             'accept-encoding': 'gzip, deflate, br',
             'cache-control': 'max-age=0',
             'upgrade-insecure-requests': '1',
             'dnt': '1',
             'referer': url
             }
        return x

    def compare_kw(self,title):
        item_comp = title.lower()
        for keyword in self.info.split(' '):
            kw = str(keyword).lower()
            if '-' in keyword:
                if kw[1::] in item_comp:
                    return False
            else:
                if kw not in item_comp:
                    return False
        return True

    def compare_size(self,title):
        item_comp = title.lower()
        for keyword in self.size_kw.split(' '):
            kw = str(keyword).lower()
            if '-' in keyword:
                if kw[1::] in item_comp:
                    return False
            else:
                if kw not in item_comp:
                    return False
        return True

    def get_country_code(self):
        return 'GB' if self.profile['shipping_country'] == 'United Kingdom' else 'US'

    def update_random_proxy(self):
        if self.proxy_list != False:
            proxy_to_use = format_proxy(random.choice(self.proxy_list))
            self.session.proxies.update(proxy_to_use)




