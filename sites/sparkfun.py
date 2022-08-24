import logging
import random
import time
import requests
from utils import return_data, send_notif, format_proxy
from webhook import failed_spark_web, good_spark_web, cart_web


class Sparkfun:

    def __init__(self, task_id, status_signal, product_signal, product, size, profile, proxy, monitor_delay, error_delay,captcha_type, qty):
        self.task_id, self.status_signal, self.product_signal, self.product,self.size, self.profile, self.monitor_delay, self.error_delay, self.captcha_type, self.qty = task_id, status_signal, product_signal, product,size, profile, monitor_delay, error_delay,captcha_type, qty
        self.session = requests.Session()
        self.proxy_list = proxy
        if self.proxy_list != False:
            self.update_random_proxy()
        self.settings = return_data("./data/settings.json")

        self.image = ''
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.driver = ''
        self.token = ''
        self.current = ''
        self.price = ''
        account_info = str(self.size).split('|')
        self.req_login(account_info[0], account_info[1])
        self.check_session()
        self.get_item()
        self.atc()
        self.go_to_shipping()
        self.submit_shipping()
        self.submit_order_fast()

    def get_smart_qty(qty, max_qty):
        try:
            if qty >= (max_qty * 2):
                return str(max_qty)
            elif qty == 1:
                return str(1)
            else:
                return str(int(qty / 2))
        except:
            return '1'

    def get_stock_proxy(self, pid):
        self.update_random_proxy()
        return self.session.get(f'https://www.sparkfun.com/products/{pid}.json').json()

    def get_checkout_token(self, html):
        ind = html.index("csrf_token")
        sub = str(html[ind:])
        spli = sub.split("'")[2]
        return spli

    def get_braintree(self, html):
        ind = '"braintree-device-data" value="'
        ind = html.index(ind)
        to_parse = html[ind + len(ind)::]
        hey = to_parse.split('}')[0] + "}"
        return hey.replace('&quot;', '"')

    def get_price(self, html):
        ind = 'name="total_price" id="amount"'
        ind = html.index(ind)
        to_parse = html[ind + len(ind)::]
        return to_parse.split('"')[1]

    def get_sparkrev(self, html):
        hey = 'sparkrev: '
        ind = html.index(hey)
        to_parse = html[ind::]
        return to_parse.split("'")[1]

    def req_login(self, user, passwd):
        self.status_signal.emit({"msg": "Getting auth", "status": "normal"})
        token = self.get_checkout_token(self.session.get('https://www.sparkfun.com/account/login').text)
        logging.getLogger('harvester').setLevel(logging.CRITICAL)
        self.status_signal.emit({"msg": "Awaiting captcha", "status": "normal"})
        try:
            from app import MainWindow
            if not MainWindow.spark_started:
                MainWindow.spark_started = True
                MainWindow.sparkfun_harvester.launch_browser()
            while True:
                # block until we get sent a captcha token and repeat
                captcha = MainWindow.sparkfun_harvester.get_token_queue('www.sparkfun.com').get()

                self.status_signal.emit({"msg": "Logging in", "status": "normal"})
                data = {'csrf_token': token, 'redirect': '/', 'user': user, 'passwd': passwd,
                        'g-recaptcha-response': captcha}
                self.session.post('https://www.sparkfun.com/account/login', data=data)
                if self.check_session():
                    self.status_signal.emit({"msg": "Valid login session found", "status": "normal"})
                    break
                else:
                    self.status_signal.emit({"msg": "Login failed! Check credentials", "status": "error"})
            MainWindow.spark_started = False
        except KeyboardInterrupt:
            pass


    def check_session(self):
        session_check = self.session.get('https://www.sparkfun.com/account')
        return 'login' not in session_check.url

    def get_item(self):
        self.status_signal.emit({"msg": "Fetching product", "status": "normal"})
        j = self.session.get('https://www.sparkfun.com/products/' + str(self.product) + ".json").json()
        self.name = j['name']
        self.image = j['images'][0]['600']
        self.product_signal.emit(f'{self.name}')

    def atc(self):
        self.status_signal.emit({"msg": "Clearing cart", "status": "normal"})
        self.session.get("https://www.sparkfun.com/cart/remove_all.json")
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
                    for x in range(10):
                        r = self.session.post('https://www.sparkfun.com/cart/add.json', data=cart_add)
                        if r.json()['success']:
                            self.status_signal.emit({"msg": "Carted!", "status": "carted"})
                            has_carted = True
                            if self.settings['webhookcart']:
                                cart_web(f'https://www.sparkfun.com/products/{self.product}', self.image, 'Sparkfun', self.name,
                                         self.profile['profile_name'])
                            break
                        elif 'cannot be backordered' in str(r.json()['message']):
                            self.status_signal.emit({"msg": "OOS on cart", "status": "error"})
                            break
                        else:
                            time.sleep(0.5)
                    if has_carted:
                        break
                else:
                    self.status_signal.emit({"msg": "Waiting for restock", "status": "monitoring"})
                time.sleep(float(self.monitor_delay))
            except Exception as e:
                print(e)
                time.sleep(float(self.error_delay))
            if has_carted:
                break

    def go_to_shipping(self):
        self.current = time.time()
        r = self.session.get('https://www.sparkfun.com/cart/proceed')
        if 'cart' not in r.url:
            self.status_signal.emit({"msg": "Redirected to shipping", "status": "normal"})
            self.token = self.get_checkout_token(r.text)

    def submit_shipping(self):
        self.status_signal.emit({"msg": "Setting Address", "status": "normal"})
        set_address_data = {'address[name]': f'{self.profile["shipping_fname"]} {self.profile["shipping_lname"]}',
                'address[company]': '',
                'address[country_id]': '223',
                'address[street_address]': self.profile['shipping_a1'],
                'address[street_address2]': self.profile['shipping_a2'],
                'address[city]': self.profile['shipping_city'],
                'address[zone_id]': self.get_shipping_zone(),
                'address[state]': self.profile['shipping_state'],
                'address[postcode]': self.profile['shipping_zipcode'],
                'address[po_box]': 'false'}
        self.session.post('https://www.sparkfun.com/orders/set_shipping_address',data=set_address_data)
        self.status_signal.emit({"msg": "Getting Shipping Methods", "status": "normal"})
        shipping_quote = {'name': 'shipping_method', 'id': 'shipping_methods'}
        quote_get = self.session.post('https://www.sparkfun.com/orders/shipping_quotes', data=shipping_quote)
        self.shipping_method = self.get_shipping_method(quote_get.text)
        self.shipping_zone = self.get_shipping_zone()

        data = {'csrf_token': self.token,
                'shipping_address[entry_name]': f'{self.profile["shipping_fname"]} {self.profile["shipping_lname"]}',
                'shipping_address[entry_company]': '',
                'shipping_address[entry_country_id]': '223',
                'shipping_address[entry_street_address]': self.profile['billing_a1'],
                'shipping_address[entry_street_address2]': self.profile['billing_a2'],
                'shipping_address[entry_city]': self.profile['billing_city'],
                'shipping_address[entry_zone]': self.shipping_zone,
                'shipping_address[entry_postcode]': self.profile['billing_zipcode'],
                'shipping_methods[1][ship_immediately]': self.shipping_method}

        submit = self.session.post('https://www.sparkfun.com/orders/shipping_update',data=data)
        self.price = self.get_price(submit.text)
        if 'billing' in submit.url:
            self.status_signal.emit({"msg": "Redirected to billing", "status": "normal"})

    def submit_order_fast(self):
        billing_form = {'csrf_token': self.token,
                        'total_price': self.price,
                        'braintree_nonce': '',
                        'braintree_device_data': '',
                        'braintree_details': '',
                        'customers_telephone': self.profile['billing_phone'],
                        'billing_address[entry_name]': f'{self.profile["shipping_fname"]} {self.profile["shipping_lname"]}',
                        'billing_address[entry_company]': '',
                        'billing_address[entry_country_id]': '223',
                        'billing_address[entry_street_address]': self.profile["billing_a1"],
                        'billing_address[entry_street_address2]': self.profile["billing_a2"],
                        'billing_address[entry_city]': self.profile["billing_city"],
                        'billing_address[entry_zone]': self.shipping_zone,
                        'billing_address[entry_postcode]': self.profile["billing_zipcode"],
                        'payment_methods_id': '3'
                        }

        self.status_signal.emit({"msg": "Submitting payment", "status": "normal"})
        self.session.post('https://www.sparkfun.com/orders/confirm', data=billing_form)
        order_data = {'csrf_token': self.token}
        self.status_signal.emit({"msg": "Submitting order", "status": "alt"})
        create = self.session.post('https://www.sparkfun.com/orders/create', data=order_data)

        # On successful checkout, you will be redirected to https://www.sparkfun.com/orders/index
        if 'index' in create.url:
            self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})

            if self.settings['webhooksuccess']:
                good_spark_web(f'https://www.sparkfun.com/products/{str(self.product)}', self.image,
                               'Sparkfun',
                               self.name, self.profile["profile_name"])
            if self.settings['notifsuccess']:
                send_notif(self.name, 'success')
        else:
            self.status_signal.emit({"msg": "Checkout Failed", "status": "error"})
            if self.settings['webhookfailed']:
                failed_spark_web(f'https://www.sparkfun.com/products/{str(self.product)}', self.image,
                                 'Sparkfun',
                                 self.name, self.profile["profile_name"])
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

    def get_shipping_zone(self):
        zones = [{"id":1,"name":"Alabama","code":"AL"},{"id":2,"name":"Alaska","code":"AK"},{"id":3,"name":"American Samoa","code":"AS"},{"id":4,"name":"Arizona","code":"AZ"},{"id":5,"name":"Arkansas","code":"AR"},{"id":6,"name":"Armed Forces Africa","code":"AF"},{"id":7,"name":"Armed Forces Americas","code":"AA"},{"id":8,"name":"Armed Forces Canada","code":"AC"},{"id":9,"name":"Armed Forces Europe","code":"AE"},{"id":10,"name":"Armed Forces Middle East","code":"AM"},{"id":11,"name":"Armed Forces Pacific","code":"AP"},{"id":12,"name":"California","code":"CA"},{"id":13,"name":"Colorado","code":"CO"},{"id":14,"name":"Connecticut","code":"CT"},{"id":15,"name":"Delaware","code":"DE"},{"id":16,"name":"District of Columbia","code":"DC"},{"id":17,"name":"Federated States Of Micronesia","code":"FM"},{"id":18,"name":"Florida","code":"FL"},{"id":19,"name":"Georgia","code":"GA"},{"id":20,"name":"Guam","code":"GU"},{"id":21,"name":"Hawaii","code":"HI"},{"id":22,"name":"Idaho","code":"ID"},{"id":23,"name":"Illinois","code":"IL"},{"id":24,"name":"Indiana","code":"IN"},{"id":25,"name":"Iowa","code":"IA"},{"id":26,"name":"Kansas","code":"KS"},{"id":27,"name":"Kentucky","code":"KY"},{"id":28,"name":"Louisiana","code":"LA"},{"id":29,"name":"Maine","code":"ME"},{"id":30,"name":"Marshall Islands","code":"MH"},{"id":31,"name":"Maryland","code":"MD"},{"id":32,"name":"Massachusetts","code":"MA"},{"id":33,"name":"Michigan","code":"MI"},{"id":34,"name":"Minnesota","code":"MN"},{"id":35,"name":"Mississippi","code":"MS"},{"id":36,"name":"Missouri","code":"MO"},{"id":37,"name":"Montana","code":"MT"},{"id":38,"name":"Nebraska","code":"NE"},{"id":39,"name":"Nevada","code":"NV"},{"id":40,"name":"New Hampshire","code":"NH"},{"id":41,"name":"New Jersey","code":"NJ"},{"id":42,"name":"New Mexico","code":"NM"},{"id":43,"name":"New York","code":"NY"},{"id":44,"name":"North Carolina","code":"NC"},{"id":45,"name":"North Dakota","code":"ND"},{"id":46,"name":"Northern Mariana Islands","code":"MP"},{"id":47,"name":"Ohio","code":"OH"},{"id":48,"name":"Oklahoma","code":"OK"},{"id":49,"name":"Oregon","code":"OR"},{"id":50,"name":"Palau","code":"PW"},{"id":51,"name":"Pennsylvania","code":"PA"},{"id":52,"name":"Puerto Rico","code":"PR"},{"id":53,"name":"Rhode Island","code":"RI"},{"id":54,"name":"South Carolina","code":"SC"},{"id":55,"name":"South Dakota","code":"SD"},{"id":56,"name":"Tennessee","code":"TN"},{"id":57,"name":"Texas","code":"TX"},{"id":58,"name":"Utah","code":"UT"},{"id":59,"name":"Vermont","code":"VT"},{"id":61,"name":"Virginia","code":"VA"},{"id":60,"name":"Virgin Islands","code":"VI"},{"id":62,"name":"Washington","code":"WA"},{"id":63,"name":"West Virginia","code":"WV"},{"id":64,"name":"Wisconsin","code":"WI"},{"id":65,"name":"Wyoming","code":"WY"}]
        for zone in zones:
            if self.profile['shipping_state'] == zone['code']:
                return zone['id']

    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(format_proxy(random.choice(self.proxy_list)))
