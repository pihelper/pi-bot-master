import json
import random
import time
import urllib.parse
import uuid
import requests
import utils
from utils import send_notif, return_data
from webhook import good_spark_web, failed_spark_web, cart_web

def check_stock(json):
    availability = json["@graph"][0]["offers"][0]['availability']
    return availability.replace('http://schema.org/','').lower().strip()
def check_name(json):
    return json["@graph"][0]["name"]

def check_price(json):
    the = json["@graph"][0]["offers"][0]["priceSpecification"]
    return f'{the["price"]} {the["priceCurrency"]}'

def check_image(json):
    return json['@graph'][0]['image']['url']

def get_json(html):
    split = 'class="yoast-schema-graph yoast-schema-graph--woo yoast-schema-graph--footer">'
    ind = html.index(split)
    sub = str(html[ind + len(split):])
    spli = sub.split("<")[0]
    return json.loads(spli.strip())

def get_pk(html):
    split = 'wc_stripe_params ='
    ind = html.index(split)
    sub = str(html[ind + len(split):])
    spli = sub.split(";")[0]
    return json.loads(spli.strip())['key']

def get_pid(html):
    ind = html.index("shortlink")
    sub = str(html[ind:])
    spli = sub.split("'")[2]
    return spli.split('=')[1]

def get_nonce(html):
    split = 'name="woocommerce-process-checkout-nonce"'
    ind = html.index(split)
    sub = str(html[ind + len(split):])
    spli = sub.split('"')[1]
    return spli.strip()

class Okdo:
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
        self.pk_live_key = ''
        self.nonce = ''
        self.title = ''

        self.main_site = self.info
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.monitor()
        self.checkout()

    def monitor(self):
        while True:
            try:
                self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
                get_item_page = self.session.get(self.info)
                if get_item_page.status_code == 200:
                    data_json = get_json(get_item_page.text)
                    if self.pid == '':
                        self.pid = get_pid(get_item_page.text)
                    if self.title == '':
                        self.title = check_name(data_json)
                        self.product_signal.emit(self.title)
                    available = 'out' not in check_stock(data_json)
                    if available:
                        okdo_cart_add = {'product_id': self.pid, 'quantity': str(self.qty), 'action': 'peake_add_to_basket'}
                        self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
                        cart_req = self.session.post('https://www.okdo.com/us/wp-admin/admin-ajax.php',data=okdo_cart_add).json()
                        if 'error' in cart_req:
                            self.status_signal.emit({"msg": "Error carting", "status": "error"})
                            time.sleep(float(self.error_delay))
                        else:
                            self.status_signal.emit({"msg": "Added to cart", "status": "carted"})
                            if self.settings['webhookcart']:
                                cart_web(str(self.info),self.image,'OKDO (US)', self.title, self.profile["profile_name"])
                        return
                    else:
                        self.status_signal.emit({"msg": "Waiting for restock", "status": "monitoring"})
                        self.update_random_proxy()
                        time.sleep(float(self.monitor_delay))
            except Exception as e:
                self.status_signal.emit({"msg": f"Error on monitor [{get_item_page.status_code}]", "status": "error"})
                self.update_random_proxy()
                time.sleep(float(self.error_delay))

    def checkout(self):
        self.status_signal.emit({"msg": "Redirecting to checkout", "status": "normal"})
        checkout_get = self.session.get('https://www.okdo.com/us/checkout/')
        self.pk_live_key = get_pk(checkout_get.text)
        self.nonce = get_nonce(checkout_get.text)
        profile = self.profile
        headers = {'Host': 'api.stripe.com',
                   'Connection': 'keep-alive',
                   'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
                   'Accept': 'application/json',
                   'Content-Type': 'application/x-www-form-urlencoded',
                   'sec-ch-ua-mobile': '?1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
                   'sec-ch-ua-platform': '"Windows"',
                   'Origin': 'https://js.stripe.com',
                   'Sec-Fetch-Site': 'same-site',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Dest': 'empty',
                   'Referer': 'https://js.stripe.com/',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.9'}
        # It seems like guid, muid, and sid are just random UUIDs
        checkout_data = {'type': 'card',
                         'owner[name]': f'{profile["shipping_fname"]} {profile["shipping_lname"]}',
                         'owner[address][line2]': profile["shipping_a1"],
                         'owner[address][state]': profile["shipping_state"],
                         'owner[address][city]': profile["shipping_city"],
                         'owner[address][postal_code]': profile["shipping_zipcode"],
                         'owner[address][country]': 'US',
                         'owner[email]': profile["shipping_email"],
                         'owner[phone]': profile["shipping_phone"],
                         'card[number]': profile["card_number"],
                         'card[cvc]': profile["card_cvv"],
                         'card[exp_month]': profile["card_month"],
                         'card[exp_year]': str(profile["card_year"]).replace("20",''),  # Just needs last 2 of card
                         'guid': uuid.uuid4(),
                         'muid': uuid.uuid4(),
                         'sid': uuid.uuid4(),
                         'payment_user_agent': 'stripe.js/0aad72e95; stripe-js-v3/0aad72e95',
                         'time_on_page': '29042',
                         'key': self.pk_live_key}
        self.status_signal.emit({"msg": "Submitting order", "status": "alt"})
        check = self.session.post('https://api.stripe.com/v1/sources', data=checkout_data, headers=headers).json()
        # This error only really happens if you use a test card or the card info is wrong
        if 'error' in check:
            self.status_signal.emit({"msg": f"Checkout Failed [{str(check['error']['code']).replace('_', ' ')}]", "status": "error"})
        else:
            self.status_signal.emit({"msg": "Processing", "status": "alt"})
            stripe_source = check['id']
            check_order = {'Host': 'www.okdo.com',
                   'Connection': 'keep-alive',
                   'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
                   'Accept': 'application/json, text/javascript, */*; q=0.01',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'X-Requested-With': 'XMLHttpRequest',
                   'sec-ch-ua-mobile': '?1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
                   'sec-ch-ua-platform': '"Windows"',
                   'Origin': 'https://www.okdo.com',
                   'Sec-Fetch-Site': 'same-site',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Dest': 'empty',
                   'Referer': 'https://www.okdo.com/us/checkout/',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.9',
                   }

            cook_string = ''
            for cook in self.session.cookies:
                cook_string += f'; {cook.name}={cook.value}'
            check_order['Cookie'] = cook_string[2:]

            checkout_url = 'https://www.okdo.com/us/?wc-ajax=checkout'
            check_data = {'billing_first_name': profile["shipping_fname"],
                          'billing_last_name': profile["shipping_lname"],
                          'billing_company': '',
                          'billing_company_number': '',
                          'billing_country': 'US',
                          'billing_address_1': profile["shipping_a1"],
                          'billing_address_2': profile["shipping_a2"],
                          'billing_city': profile["shipping_city"],
                          'billing_state': profile["shipping_state"],
                          'billing_postcode': profile["shipping_zipcode"],
                          'billing_phone': profile["shipping_phone"],
                          'billing_email': profile["shipping_email"],
                          'shipping_first_name': profile["shipping_fname"],
                          'shipping_last_name': profile["shipping_lname"],
                          'shipping_company': '',
                          'shipping_country': 'US',
                          'shipping_address_1': profile["shipping_a1"],
                          'shipping_address_2': profile["shipping_a2"],
                          'shipping_city': profile["shipping_city"],
                          'shipping_state': profile["shipping_state"],
                          'shipping_postcode': profile["shipping_zipcode"],
                          'order_comments': '',
                          'payment_method': 'stripe',
                          'shipping_method[0]': 'premium:1',
                          'terms-of-sale': 'on',
                          'terms-of-sale-field': '1',
                          'coupon_code': '',
                          'woocommerce-process-checkout-nonce': self.nonce,
                          '_wp_http_referer': '/us/checkout/',
                          'stripe_source': stripe_source,
                          }
            self.status_signal.emit({"msg": "Checking order", "status": "alt"})

            sub = self.session.post(checkout_url, data=check_data, headers=check_order).json()
            if sub['result'] == 'success':
                to_decode = sub['redirect']
                first_decode = urllib.parse.unquote(to_decode)
                second_decode = urllib.parse.unquote(first_decode)
                order_url = second_decode[second_decode.index('redirect_to=')+12:]
                self.status_signal.emit({"msg": "Order Placed", "status": "success"})
                if self.settings['webhooksuccess']:
                    good_spark_web(order_url,self.image,'OKDO (US)', self.title, self.profile["profile_name"])
                if self.settings['notifsuccess']:
                    send_notif(self.title,'success')
            else:
                self.status_signal.emit({"msg": "Order Failed", "status": "error"})
                if self.settings['webhookfailed']:
                    failed_spark_web('https://www.okdo.com/us/',self.image,'OKDO (US)', self.title, self.profile["profile_name"])
                if self.settings['notiffailed']:
                    send_notif(self.title,'fail')
    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(utils.format_proxy(random.choice(self.proxy_list)))


