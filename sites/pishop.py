import json
import random
import time
import requests
from bs4 import BeautifulSoup
import utils
from utils import send_notif, return_data
from webhook import good_web, failed_web, cart_web


def get_csrf(html):
    ind = html.index("csrf_token")
    sub = str(html[ind:])
    spli = sub.split('"')[2]
    return spli

def get_image(html):
    ind = html.index("og:image")
    sub = str(html[ind:])
    spli = sub.split('"')[2]
    return spli

def check_stock(html):
    ind = html.index('var BCData = ')
    sub = str(html[ind + 13:])
    spli = sub.split(";")[0]
    return json.loads(spli.strip())


def get_varIdentifyToken(html):
    ind = html.index("window.checkoutVariantIdentificationToken = ")
    sub = str(html[ind:])
    spli = sub.split("'")[1]
    return spli

def get_pid(url):
    html = requests.get(url).content
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find_all(attrs={"name": "product_id"})[0]['value']

def get_captcha(url):
    sitekey = '6LcjX0sbAAAAACp92-MNpx66FT4pbIWh-FTDmkkz'
    api_key = 'd3feb431a12c805e759a4b111ebadd24'
    create_task = '{"clientKey": "' + api_key + '", "task": {"type": "NoCaptchaTaskProxyless", "websiteURL": "' + url + '", "websiteKey": "' + sitekey + '"}}'
    make_task = {'clientKey': api_key, 'task': {'type': 'NoCaptchaTaskProxyless', 'websiteURL': url, 'websiteKey' : sitekey}}
    print('Requesting captcha')
    r = requests.post("https://api.capmonster.cloud/createTask", json=make_task).json()
    taskId = r['taskId']
    if taskId != 0:
        print('Waiting for captcha')
        get_result = '{"clientKey":"' + api_key + '", "taskId":' + str(taskId) + '}'
        i = 0
        while i < 240:
            r = requests.post('https://api.capmonster.cloud/getTaskResult', data=get_result).json()
            if r["status"] != 'ready':
                time.sleep(0.5)
                i += 1
            else:
                return r['solution']['gRecaptchaResponse']

class PiShop:
    def __init__(self, task_id, status_signal, product_signal, product, info, size, profile, proxy, monitor_delay, error_delay,captcha_type, qty):
        self.task_id, self.status_signal, self.product_signal, self.product, self.info, self.size, self.profile, self.monitor_delay, self.error_delay,self.captcha_type, self.qty = task_id, status_signal, product_signal, product, info, size, profile,monitor_delay, error_delay, captcha_type, qty
        self.session = requests.Session()
        self.proxy_list = proxy
        if self.proxy_list != False:
            self.update_random_proxy()
        self.settings = return_data("./data/settings.json")
        #Variables obtained during checkout process whick are needed
        self.image = ''
        self.pid = ''
        self.csrf_token = ''
        self.cart_id = ''
        self.item_id = ''
        self.verification_token = ''
        self.cosignment_id = ''
        self.title = ''

        self.main_site = self.info
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.monitor()
        self.get_checkout_page()
        self.submit_email()
        self.submit_shipping()
        self.submit_captcha()
        self.submit_payment_info()

    def monitor(self):
        while True:
            try:
                self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
                get_item_page = self.session.get(self.info)
                if get_item_page.status_code == 200:
                    soup = BeautifulSoup(get_item_page.content, 'html.parser')
                    if self.pid == '':
                        self.pid = soup.find_all(attrs={"name": "product_id"})[0]['value']
                    if self.title == '':
                        self.title = str(soup.find('title').get_text()).replace(' - PiShop.us','').split(' - CM4')[0]
                        self.product_signal.emit(self.title)
                    stock_json = check_stock(get_item_page.text)
                    if self.csrf_token == '':
                        self.csrf_token = stock_json['csrf_token']
                    if stock_json['product_attributes']['instock']:
                        atc_data = {'action': 'add', 'product_id': self.pid, 'qty[]': self.qty}
                        self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
                        cart_req = self.session.post('https://www.pishop.us/remote/v1/cart/add',data=atc_data).json()['data']
                        if 'error' in cart_req:
                            self.status_signal.emit({"msg": "OOS on cart", "status": "error"})
                            time.sleep(float(self.error_delay))
                        else:
                            self.status_signal.emit({"msg": "Added to cart", "status": "carted"})
                            self.cart_id = cart_req['cart_id']
                            self.item_id = cart_req['cart_item']['id']
                            self.image = cart_req['cart_item']['thumbnail']
                            if self.settings['webhookcart']:
                                cart_web(self.info, self.image,'PiShop (US)',self.title,self.profile['profile_name'])
                        return
                    else:
                        self.status_signal.emit({"msg": "Waiting for restock", "status": "monitoring"})
                        self.update_random_proxy()
                        time.sleep(float(self.monitor_delay))
            except:
                self.status_signal.emit({"msg": f"Error on monitor [{get_item_page.status_code}]", "status": "error"})
                self.update_random_proxy()
                time.sleep(float(self.error_delay))

    def get_checkout_page(self):
        check_headers = {'authority': 'www.pishop.us', 'host': 'www.pishop.us', 'scheme': 'https',
                         'accept': 'application/vnd.bc.v1+json', 'accept-encoding': 'gzip, deflate',
                         'accept-language': 'en-US,en;q=0.9', 'content-type': 'application/json',
                         'X-XSRF-TOKEN': self.session.cookies.get_dict()['XSRF-TOKEN'],
                         'x-checkout-sdk-version': '1.269.0', 'referer': "https://www.pishop.us/checkout",
                         'origin': 'https://www.pishop.us',
                         'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                         'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'Sec-Fetch-Site': 'same-origin',
                         'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'upgrade-insecure-requests': '1',
                         'Connection': 'keep-alive', 'Cookie': self.request_cookies()}

        while True:
            try:
                self.status_signal.emit({"msg": "Getting checkout", "status": "normal"})
                checkout_req = self.session.get('https://www.pishop.us/checkout',headers=check_headers)
                if checkout_req.url.endswith('/checkout'):
                    return
                else:
                    self.status_signal.emit(
                        {"msg": f"Error on checkout [{checkout_req.status_code}]", "status": "error"})
                    time.sleep(float(self.error_delay))
            except:
                self.status_signal.emit({"msg": f"Error on checkout [{checkout_req.status_code}]", "status": "error"})
                time.sleep(float(self.error_delay))

    def submit_email(self):
        email_url = f'https://www.pishop.us/api/storefront/checkouts/{self.cart_id}/billing-address?include=cart.lineItems.physicalItems.options%2Ccart.lineItems.digitalItems.options%2Ccustomer%2Cpromotions.banners'
        email_data = {'email': self.profile['shipping_email']}
        email_headers = {
            'authority': 'www.pishop.us',
            'host': 'www.pishop.us',
            'scheme': 'https',
            'accept': 'application/vnd.bc.v1+json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'X-XSRF-TOKEN': self.session.cookies.get_dict()['XSRF-TOKEN'],
            'x-checkout-sdk-version': '1.269.0',
            'referer': "https://www.pishop.us/checkout",
            'origin': 'https://www.pishop.us',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'upgrade-insecure-requests': '1',
            'Connection': 'keep-alive',
            'Cookie': self.request_cookies()}

        self.session.post(email_url, json=email_data, headers=email_headers)

    def submit_shipping(self):
        shipping_headers = {
            'host': 'www.pishop.us',
            'scheme': 'https',
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'X-XSRF-TOKEN': self.session.cookies.get_dict()['XSRF-TOKEN'],
            'origin': 'https://www.pishop.us',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'upgrade-insecure-requests': '1',
            'Connection': 'keep-alive',
            'Cookie': self.request_cookies()}

        cosignment_url = f'https://www.pishop.us/api/storefront/checkouts/{self.cart_id}/consignments?include=consignments.availableShippingOptions%2Ccart.lineItems.physicalItems.options%2Ccart.lineItems.digitalItems.options%2Ccustomer%2Cpromotions.banners%2C0'
        shipping_data = [{"address": {
            "firstName": self.profile['shipping_fname'],
            "lastName": self.profile['shipping_lname'],
            "company": "",
            "phone": self.profile['shipping_phone'],
            "address1": self.profile['shipping_a1'],
            "address2": self.profile['shipping_a2'],
            "city": self.profile['shipping_city'],
            "countryCode": "US",
            "stateOrProvinceCode": self.profile['shipping_state'],
            "postalCode": self.profile['shipping_zipcode'],
            "shouldSaveAddress": 'true',
            "stateOrProvince": "",
            "customFields": []},
            "lineItems": [{"itemId": self.item_id, "quantity": int(self.qty)}]}]

        billing_data = {"firstName": self.profile['billing_fname'], "lastName": self.profile['billing_lname'], "company": "", "phone": self.profile['billing_phone'],
                        "address1": self.profile['billing_a1'], "address2": self.profile['billing_a2'], "city": self.profile['billing_city'], "countryCode": "US",
                        "stateOrProvinceCode": self.profile['billing_state'], "postalCode": self.profile['billing_zipcode'], "shouldSaveAddress": 'true',
                        "stateOrProvince": "", "customFields": [], 'email': self.profile['shipping_email']}

        # Appends the shipping data to the checkout, and obtains the cosignment ID needed
        self.status_signal.emit({"msg": "Submitting shipping", "status": "normal"})
        cosign_json = self.session.post(cosignment_url, json=shipping_data, headers=shipping_headers).json()['consignments'][0]
        shipping_rate = cosign_json['availableShippingOptions'][0]['id']
        self.cosignment_id = cosign_json['id']

        # Uses the cosignment ID to obtain shipping method needed.
        # Can make slightly faster by hard coding cheapest Fedex rate but for now fetches rate to avoid errors
        self.status_signal.emit({"msg": "Submitting shipping rate", "status": "normal"})
        url_to_post = f'https://www.pishop.us/api/storefront/checkouts/{self.cart_id}/consignments/{self.cosignment_id}?include=consignments.availableShippingOptions%2Ccart.lineItems.physicalItems.options%2Ccart.lineItems.digitalItems.options%2Ccustomer%2Cpromotions.banners'
        shipping_rate = {"shippingOptionId": shipping_rate}
        self.status_signal.emit({"msg": "Submitting shipping rate", "status": "normal"})
        rate_submit = self.session.put(url_to_post, json=shipping_rate, headers=shipping_headers)

        # Submits the billing address for the order
        self.status_signal.emit({"msg": "Submitting billing", "status": "normal"})
        billing_id = rate_submit.json()['billingAddress']['id']
        billing_url = f'https://www.pishop.us/api/storefront/checkouts/{self.cart_id}/billing-address/{billing_id}?include=cart.lineItems.physicalItems.options%2Ccart.lineItems.digitalItems.options%2Ccustomer%2Cpromotions.banners'
        self.session.put(billing_url, json=billing_data, headers=shipping_headers)

    def submit_captcha(self):
        spam_protection = {
            'host': 'www.pishop.us',
            'method': 'POST',
            'scheme': 'https',
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'X-XSRF-TOKEN': self.session.cookies.get_dict()['XSRF-TOKEN'],
            'X-Checkout-SDK-Version': '1.269.0',
            'Content-Length': '95',
            'path': f'/api/storefront/checkouts/{self.cart_id}/spam-protection',
            'origin': 'https://www.pishop.us',
            'referrer': 'https://www.pishop.us/checkout',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'upgrade-insecure-requests': '1',
            'Connection': 'keep-alive',
            'Cookie': self.request_cookies()}

        # Order needs to submit a V2 ReCAPTCHA token to /spam-protection to proceed
        # I've never had an order using this bot that didn't need to invoke spam protection but later spam protection checking will be added
        captcha = self.handle_captcha()
        cap_data = {'token': captcha}
        self.status_signal.emit({"msg": "Submitting captcha", "status": "normal"})
        cap_submit = self.session.post(f'https://www.pishop.us/api/storefront/checkouts/{self.cart_id}/spam-protection', json=cap_data,
                            headers=spam_protection)

    def submit_payment_info(self):
        payment_headers = {
            'host': 'www.pishop.us',
            'method': 'POST',
            'scheme': 'https',
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'X-XSRF-TOKEN': self.session.cookies.get_dict()['XSRF-TOKEN'],
            'X-Checkout-SDK-Version': '1.269.0',
            'Content-Length': '95',
            'path': '/internalapi/v1/checkout/order',
            'origin': 'https://www.pishop.us',
            'referrer': 'https://www.pishop.us/checkout',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'upgrade-insecure-requests': '1',
            'Connection': 'keep-alive',
            'X-API-INTERNAL': 'This API endpoint is for internal use only and may change in the future',
            'Cookie': self.request_cookies()}

        # Need to get identity token that reveals itself later through the checkout process
        self.status_signal.emit({"msg": "Fetching checkout token", "status": "alt"})
        check_data = {'path': f'/checkout?cartId={self.cart_id}',
                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                      'Cookie': payment_headers['Cookie']}
        token_get = self.session.get(f'https://www.pishop.us/checkout?cartId={self.cart_id}', allow_redirects=True, headers=check_data)
        decoded_token = get_varIdentifyToken(token_get.text)

        # Appends checkout token to headers
        payment_headers['X-Checkout-Token'] = decoded_token

        # While submitting order, we can use the COD method to just place order and pay later.
        checkout_data = {'cartId': self.cart_id, 'customerMessage': '', 'payment': {'name': 'cod'}}
        self.status_signal.emit({"msg": "Submitting Order", "status": "alt"})

        # We submit the order now
        paying = self.session.post('https://www.pishop.us/internalapi/v1/checkout/order', headers=payment_headers, json=checkout_data, allow_redirects=False).json()
        if 'data' in paying:
            price = str(float(int(paying['data']['order']['grandTotal']['integerAmount'])/100))
            if 'AWAITING_PAYMENT' in paying['data']['order']['status']:
                self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                if self.settings['webhooksuccess']:
                    good_web(self.info, self.image,'PiShop (US)',self.title,self.profile['profile_name'],price)
                if self.settings['notifsuccess']:
                    send_notif(self.title,'success')
            else:
                self.status_signal.emit({"msg": f"Checkout Failed[{paying['data']['order']['status']}]", "status": "error"})
                if self.settings['webhookfailed']:
                    failed_web(self.info, self.image,'PiShop (US)',self.title,self.profile['profile_name'],price)
                if self.settings['notiffailed']:
                    send_notif(self.title,'fail')
    def handle_captcha(self):
        sitekey = '6LcjX0sbAAAAACp92-MNpx66FT4pbIWh-FTDmkkz'
        self.status_signal.emit({"msg": f"Awaiting Captcha ({self.captcha_type})", "status": "alt"})
        if self.captcha_type == 'Manual Harvester':
            if self.settings['notifcaptcha']:
                send_notif(self.title,'captcha')
            try:
                from app import MainWindow
                if not MainWindow.pishop_started:
                    MainWindow.pishop_started = True
                    MainWindow.pishop_harvester.launch_browser()
                while True:
                    # block until we get sent a captcha token and repeat
                    captcha = MainWindow.pishop_harvester.get_token_queue('www.pishop.us').get()
                    break
                MainWindow.pishop_started = False
                return captcha
            except KeyboardInterrupt:
                pass

        elif self.captcha_type == 'CapMonster':
            return utils.get_captcha_cap('https://www.pishop.us',sitekey)
        elif self.captcha_type == '2Captcha':
            return utils.get_captcha_two('https://www.pishop.us',sitekey)

    def request_cookies(self):
        cook_string = ''
        for cook in self.session.cookies:
            cook_string += f'; {cook.name}={cook.value}'
        return cook_string[2:]

    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(utils.format_proxy(random.choice(self.proxy_list)))





