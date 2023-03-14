import json
import logging
import random
import time
import traceback

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from utils import return_data, send_notif, format_proxy, load_session, save_session
from webhook import new_web

class Sparkfun:
    def __init__(self, task_id, status_signal, product_signal, product, size, profile, proxy, monitor_delay, error_delay,captcha_type, qty):
        self.task_id, self.status_signal, self.product_signal, self.product,self.size, self.profile, self.monitor_delay, self.error_delay, self.captcha_type, self.qty = task_id, status_signal, product_signal, product,size, profile, monitor_delay, error_delay,captcha_type, qty
        self.session = requests.Session()
        self.proxy_list = proxy
        if self.proxy_list != False:
            self.update_random_proxy()
        self.settings = return_data("./data/settings.json")
        self.product = self.product.split('[')[0].strip()
        self.image = ''
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.driver = ''
        self.token = ''
        self.current = ''
        self.price = ''
        self.user = self.profile.split('|')[1]
        self.pw = self.profile.split('|')[2]
        self.phone = self.profile.split('|')[3]
        self.shipping_address = {}
        self.billing_address = {}
        self.address_validate = {}
        self.address_id = ''
        self.get_session()
        self.get_address()
        self.get_item()
        self.atc()
        self.go_to_shipping()
        self.submit_shipping()
        self.submit_order_fast()

    def get_smart_qty(self, qty, max_qty):
        try:
            if qty >= (max_qty * 2):
                return str(max_qty)
            elif qty == 1:
                return str(1)
            else:
                return str(int(qty / 2))
        except:
            return '1'

    def get_address_book(self, html):
        sub = 'var address_book = '
        ind = html.index(sub)
        to_parse = html[ind + len(sub)::]
        hey = to_parse.split(';')[0]
        return json.loads(hey)


    def get_stock_proxy(self, pid):
        self.update_random_proxy()
        return self.session.get(f'https://www.sparkfun.com/products/{pid}.json').json()

    def get_checkout_token(self, html):
        ind = html.index("csrf_token")
        sub = str(html[ind:])
        spli = sub.split("'")[2]
        return spli

    def get_braintree(self, html):
        sub = '"braintree-device-data" value="'
        ind = html.index(sub)
        to_parse = html[ind + len(sub)::]
        hey = to_parse.split('}')[0] + "}"
        return hey.replace('&quot;', '"')

    def get_price(self, html):
        sub = 'name="total_price" id="amount"'
        ind = html.index(sub)
        to_parse = html[ind + len(sub)::]
        return to_parse.split('"')[1]

    def get_price_new(self,html):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find('input', {'name': 'total_price'}).get('value')

    def get_sparkrev(self, html):
        hey = 'sparkrev: '
        ind = html.index(hey)
        to_parse = html[ind::]
        return to_parse.split("'")[1]

    def get_session(self):
        self.status_signal.emit({"msg": "Checking for session", "status": "normal"})
        session = load_session(self.user, 'https://www.sparkfun.com/')
        if session == False:
            self.browser_login()
        else:
            for cookies in session[0]:
                self.session.cookies.set(cookies, session[0][cookies])
            self.status_signal.emit({"msg": "Validating session", "status": "normal"})
            account_get = self.session.get('https://www.sparkfun.com/account/')
            if 'login' in account_get.url:
                self.status_signal.emit({"msg": "Session no longer valid", "status": "normal"})
                self.browser_login()
            else:
                self.status_signal.emit({"msg": "Valid session found!", "status": "normal"})

    def browser_login(self):
        self.status_signal.emit({"msg": "Awaiting browser login", "status": "alt"})
        caps = DesiredCapabilities().CHROME
        caps["pageLoadStrategy"] = 'eager'
        options = Options()
        options.add_argument("window-size=1920,1080")
        options.add_argument('enable-automation')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-gpu')
        options.add_argument('log-level=3')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('disable-infobars')
        driver = webdriver.Chrome(options=options, desired_capabilities=caps)
        # Loads base URL
        driver.get('https://www.sparkfun.com/account/login')
        driver.find_element(By.CSS_SELECTOR, '#login_user').send_keys(self.user)
        driver.find_element(By.CSS_SELECTOR, '#login_password').send_keys(self.pw)

        while 'account/login' in driver.current_url:
            time.sleep(0.1)

        for cookie in driver.get_cookies():
            self.session.cookies.update({cookie['name']: cookie['value']})

        driver.close()

        if self.check_session():
            self.status_signal.emit({"msg": "Valid login session found", "status": "normal"})
            save_session(self.user, 'https://www.sparkfun.com/', self.session)
        else:
            self.status_signal.emit({"msg": "Login failed! Check credentials", "status": "error"})

    def check_session(self):
        session_check = self.session.get('https://www.sparkfun.com/account')
        return 'login' not in session_check.url

    def get_address(self):
        self.status_signal.emit({"msg": "Getting Address Page", "status": "normal"})
        address_get = self.session.get('https://www.sparkfun.com/addresses')
        if address_get.status_code == 200:
            soup = BeautifulSoup(address_get.content, 'html.parser')
            address_url = str(soup.find_all('a', {'class': 'button'})[0].get('href'))
            self.address_id = address_url.split("/")[-1]
            self.status_signal.emit({"msg": "Loading Address", "status": "normal"})
            address_json = self.session.get(f'{address_url}.json').json()
            print(address_json)
            for value in address_json:
                self.shipping_address[f'shipping_address[entry_{value if value != "country" else "country_id"}]'] = address_json[value] if value != 'zone' else self.get_shipping_zone(address_json[value])
                self.billing_address[f'billing_address[entry_{value if value != "country" else "country_id"}]'] = address_json[value] if value != 'zone' else self.get_shipping_zone(address_json[value])
                self.address_validate[f'address[{value if value != "country" else "country_id"}]'] = address_json[value]
            self.address_validate['address[po_box]'] = False
            self.address_validate['address[state]'] = self.address_validate['address[zone]']

    def get_item(self):
        self.status_signal.emit({"msg": "Fetching product", "status": "normal"})
        j = self.session.get('https://www.sparkfun.com/products/' + str(self.product) + ".json").json()
        self.name = j['name']
        self.image = j['images'][0]['600']
        self.product_signal.emit(f'{self.name} [{self.qty}]')

    def clear_cart(self):
        self.status_signal.emit({"msg": "Clearing cart", "status": "normal"})
        self.session.get("https://www.sparkfun.com/cart/remove_all.json")

    def atc(self):
        self.clear_cart()
        self.status_signal.emit({"msg": "Getting Auth", "status": "normal"})
        r = self.session.get(f'https://www.sparkfun.com/products/{str(self.product)}')
        token = self.get_checkout_token(r.text)
        has_carted = False
        while True:
            try:
                self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
                r = self.get_stock_proxy(self.product)
                if r['in_stock']:
                    self.status_signal.emit({"msg": "Carting item", "status": "normal"})
                    cart_add = {'id': self.product, 'qty': str(self.qty), 'csrf_token': token}
                    r = self.session.post('https://www.sparkfun.com/cart/add.json', data=cart_add)
                    if r.json()['success']:
                        self.status_signal.emit({"msg": "Carted!", "status": "carted"})

                        if self.settings['webhookcart']:
                            new_web('carted', 'Sparkfun', self.image, self.name, self.user)
                        self.start_time = time.time()
                        break
                    elif 'cannot be backordered' in str(r.json()['message']):
                        self.status_signal.emit({"msg": "OOS on cart", "status": "error"})
                        self.clear_cart()
                        time.sleep(0.5)
                    else:
                        time.sleep(0.5)
                else:
                    self.status_signal.emit({"msg": "Waiting for restock", "status": "monitoring"})
                time.sleep(float(self.monitor_delay))
            except Exception:
                self.status_signal.emit({"msg": "Error on monitor", "status": "error"})
                print(traceback.format_exc())
                time.sleep(float(self.error_delay))

    def go_to_shipping(self):
        self.status_signal.emit({"msg": "Redirecting to shipping", "status": "normal"})
        self.current = time.time()
        r = self.session.get('https://www.sparkfun.com/cart/proceed')
        if 'cart' not in r.url:
            self.token = self.get_checkout_token(r.text)

    def submit_shipping(self):
        self.status_signal.emit({"msg": "Setting Address", "status": "normal"})
        self.session.post('https://www.sparkfun.com/orders/set_shipping_address',data=self.address_validate)
        self.status_signal.emit({"msg": "Posting Shipping Methods", "status": "normal"})
        quote_post = {'name': 'shipping_method', 'id': 'shipping_methods'}
        quote_get = self.session.post('https://www.sparkfun.com/orders/shipping_quotes', data=quote_post)
        quote_rate = "6" if 'FREE' in quote_get.text else "116"

        self.shipping_address['csrf_token'] = self.token
        self.shipping_address['address_select_dropdown'] = self.address_id
        self.shipping_address['shipping_methods[1][ship_immediately]'] = quote_rate

        self.status_signal.emit({"msg": "Submitting from address book", "status": "normal"})
        submit = self.session.post('https://www.sparkfun.com/orders/shipping_update', data=self.shipping_address)

        if 'billing' in submit.url:
            self.price = self.get_price_new(submit.content)
            self.status_signal.emit({"msg": "Redirected to billing", "status": "normal"})
        elif 'Please fix the errors below' in submit.text:
            self.status_signal.emit({"msg": "Error submitting shipping (OOS)", "status": "error"})
            if self.settings['webhookfailed']:
                new_web('failed', 'Sparkfun', self.image, self.name, self.user)
            self.atc()
            self.go_to_shipping()
            self.submit_shipping()
            return
        else:
            self.status_signal.emit({"msg": "Error submitting shipping (Other)", "status": "error"})
            if self.settings['webhookfailed']:
                new_web('failed', 'Sparkfun', self.image, self.name, self.user)
            self.atc()
            self.go_to_shipping()
            self.submit_shipping()
            return

    def submit_order_fast(self):
        self.billing_address['csrf_token'] = self.token
        self.billing_address['total_price'] = self.price
        self.billing_address['customers_telephone'] = self.phone
        self.billing_address['payment_methods_id'] = '3'
        self.billing_address['billing_address[address_select_dropdown]'] = self.address_id
        self.status_signal.emit({"msg": "Submitting payment", "status": "normal"})
        billing_submit = self.session.post('https://www.sparkfun.com/orders/confirm', data=self.billing_address)
        order_data = {'csrf_token': self.token}
        self.status_signal.emit({"msg": "Submitting order", "status": "alt"})
        create = self.session.post('https://www.sparkfun.com/orders/create', data=order_data)

        # On successful checkout, you will be redirected to https://www.sparkfun.com/orders/index
        end_time = time.time() - self.start_time
        if 'index' in create.url:
            self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
            if self.settings['webhooksuccess']:
                new_web('success', 'Sparkfun', self.image, self.name, self.user, checkout_time=end_time)
            if self.settings['notifsuccess']:
                send_notif(self.name, 'success')
        else:
            self.status_signal.emit({"msg": "Checkout Failed", "status": "error"})
            if self.settings['webhookfailed']:
                new_web('failed', 'Sparkfun', self.image, self.name, self.user, checkout_time=end_time)
            if self.settings['notiffailed']:
                send_notif(self.name, 'fail')

    def get_shipping_method(self, text):
        method_text = text.replace('\\n', '\n')
        methods = []
        for link in method_text.splitlines():
            if 'ship_immediately_' in link:
                methods.append(link.replace('"', ''))
        cheapest_method = methods[len(methods) - 1]
        return cheapest_method[cheapest_method.rfind("_") + 1:].replace('\\','')

    def get_shipping_zone(self, state):
        zones = [{"id":1,"name":"Alabama","code":"AL"},{"id":2,"name":"Alaska","code":"AK"},{"id":3,"name":"American Samoa","code":"AS"},{"id":4,"name":"Arizona","code":"AZ"},{"id":5,"name":"Arkansas","code":"AR"},{"id":6,"name":"Armed Forces Africa","code":"AF"},{"id":7,"name":"Armed Forces Americas","code":"AA"},{"id":8,"name":"Armed Forces Canada","code":"AC"},{"id":9,"name":"Armed Forces Europe","code":"AE"},{"id":10,"name":"Armed Forces Middle East","code":"AM"},{"id":11,"name":"Armed Forces Pacific","code":"AP"},{"id":12,"name":"California","code":"CA"},{"id":13,"name":"Colorado","code":"CO"},{"id":14,"name":"Connecticut","code":"CT"},{"id":15,"name":"Delaware","code":"DE"},{"id":16,"name":"District of Columbia","code":"DC"},{"id":17,"name":"Federated States Of Micronesia","code":"FM"},{"id":18,"name":"Florida","code":"FL"},{"id":19,"name":"Georgia","code":"GA"},{"id":20,"name":"Guam","code":"GU"},{"id":21,"name":"Hawaii","code":"HI"},{"id":22,"name":"Idaho","code":"ID"},{"id":23,"name":"Illinois","code":"IL"},{"id":24,"name":"Indiana","code":"IN"},{"id":25,"name":"Iowa","code":"IA"},{"id":26,"name":"Kansas","code":"KS"},{"id":27,"name":"Kentucky","code":"KY"},{"id":28,"name":"Louisiana","code":"LA"},{"id":29,"name":"Maine","code":"ME"},{"id":30,"name":"Marshall Islands","code":"MH"},{"id":31,"name":"Maryland","code":"MD"},{"id":32,"name":"Massachusetts","code":"MA"},{"id":33,"name":"Michigan","code":"MI"},{"id":34,"name":"Minnesota","code":"MN"},{"id":35,"name":"Mississippi","code":"MS"},{"id":36,"name":"Missouri","code":"MO"},{"id":37,"name":"Montana","code":"MT"},{"id":38,"name":"Nebraska","code":"NE"},{"id":39,"name":"Nevada","code":"NV"},{"id":40,"name":"New Hampshire","code":"NH"},{"id":41,"name":"New Jersey","code":"NJ"},{"id":42,"name":"New Mexico","code":"NM"},{"id":43,"name":"New York","code":"NY"},{"id":44,"name":"North Carolina","code":"NC"},{"id":45,"name":"North Dakota","code":"ND"},{"id":46,"name":"Northern Mariana Islands","code":"MP"},{"id":47,"name":"Ohio","code":"OH"},{"id":48,"name":"Oklahoma","code":"OK"},{"id":49,"name":"Oregon","code":"OR"},{"id":50,"name":"Palau","code":"PW"},{"id":51,"name":"Pennsylvania","code":"PA"},{"id":52,"name":"Puerto Rico","code":"PR"},{"id":53,"name":"Rhode Island","code":"RI"},{"id":54,"name":"South Carolina","code":"SC"},{"id":55,"name":"South Dakota","code":"SD"},{"id":56,"name":"Tennessee","code":"TN"},{"id":57,"name":"Texas","code":"TX"},{"id":58,"name":"Utah","code":"UT"},{"id":59,"name":"Vermont","code":"VT"},{"id":61,"name":"Virginia","code":"VA"},{"id":60,"name":"Virgin Islands","code":"VI"},{"id":62,"name":"Washington","code":"WA"},{"id":63,"name":"West Virginia","code":"WV"},{"id":64,"name":"Wisconsin","code":"WI"},{"id":65,"name":"Wyoming","code":"WY"}]
        for zone in zones:
            if state == zone['code']:
                return zone['id']
    def get_shipping_state(self, z):
        zones = [{"id":1,"name":"Alabama","code":"AL"},{"id":2,"name":"Alaska","code":"AK"},{"id":3,"name":"American Samoa","code":"AS"},{"id":4,"name":"Arizona","code":"AZ"},{"id":5,"name":"Arkansas","code":"AR"},{"id":6,"name":"Armed Forces Africa","code":"AF"},{"id":7,"name":"Armed Forces Americas","code":"AA"},{"id":8,"name":"Armed Forces Canada","code":"AC"},{"id":9,"name":"Armed Forces Europe","code":"AE"},{"id":10,"name":"Armed Forces Middle East","code":"AM"},{"id":11,"name":"Armed Forces Pacific","code":"AP"},{"id":12,"name":"California","code":"CA"},{"id":13,"name":"Colorado","code":"CO"},{"id":14,"name":"Connecticut","code":"CT"},{"id":15,"name":"Delaware","code":"DE"},{"id":16,"name":"District of Columbia","code":"DC"},{"id":17,"name":"Federated States Of Micronesia","code":"FM"},{"id":18,"name":"Florida","code":"FL"},{"id":19,"name":"Georgia","code":"GA"},{"id":20,"name":"Guam","code":"GU"},{"id":21,"name":"Hawaii","code":"HI"},{"id":22,"name":"Idaho","code":"ID"},{"id":23,"name":"Illinois","code":"IL"},{"id":24,"name":"Indiana","code":"IN"},{"id":25,"name":"Iowa","code":"IA"},{"id":26,"name":"Kansas","code":"KS"},{"id":27,"name":"Kentucky","code":"KY"},{"id":28,"name":"Louisiana","code":"LA"},{"id":29,"name":"Maine","code":"ME"},{"id":30,"name":"Marshall Islands","code":"MH"},{"id":31,"name":"Maryland","code":"MD"},{"id":32,"name":"Massachusetts","code":"MA"},{"id":33,"name":"Michigan","code":"MI"},{"id":34,"name":"Minnesota","code":"MN"},{"id":35,"name":"Mississippi","code":"MS"},{"id":36,"name":"Missouri","code":"MO"},{"id":37,"name":"Montana","code":"MT"},{"id":38,"name":"Nebraska","code":"NE"},{"id":39,"name":"Nevada","code":"NV"},{"id":40,"name":"New Hampshire","code":"NH"},{"id":41,"name":"New Jersey","code":"NJ"},{"id":42,"name":"New Mexico","code":"NM"},{"id":43,"name":"New York","code":"NY"},{"id":44,"name":"North Carolina","code":"NC"},{"id":45,"name":"North Dakota","code":"ND"},{"id":46,"name":"Northern Mariana Islands","code":"MP"},{"id":47,"name":"Ohio","code":"OH"},{"id":48,"name":"Oklahoma","code":"OK"},{"id":49,"name":"Oregon","code":"OR"},{"id":50,"name":"Palau","code":"PW"},{"id":51,"name":"Pennsylvania","code":"PA"},{"id":52,"name":"Puerto Rico","code":"PR"},{"id":53,"name":"Rhode Island","code":"RI"},{"id":54,"name":"South Carolina","code":"SC"},{"id":55,"name":"South Dakota","code":"SD"},{"id":56,"name":"Tennessee","code":"TN"},{"id":57,"name":"Texas","code":"TX"},{"id":58,"name":"Utah","code":"UT"},{"id":59,"name":"Vermont","code":"VT"},{"id":61,"name":"Virginia","code":"VA"},{"id":60,"name":"Virgin Islands","code":"VI"},{"id":62,"name":"Washington","code":"WA"},{"id":63,"name":"West Virginia","code":"WV"},{"id":64,"name":"Wisconsin","code":"WI"},{"id":65,"name":"Wyoming","code":"WY"}]
        for zone in zones:
            if z == zone['id']:
                return zone['code']

    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(format_proxy(random.choice(self.proxy_list)))
