import json
import random
import time
import traceback
import urllib.parse

from bs4 import BeautifulSoup
import requests, re
import urllib3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from utils import return_data, format_proxy, load_session, save_session, delete_session, get_country_code
from webhook import new_web

class Shop:
    def __init__(self, task_id, status_signal, product_signal, product, info, size, profile, proxy, monitor_delay,
                 error_delay, qty):
        self.task_id, self.status_signal, self.product_signal, self.product, self.info, self.size, self.profile, self.monitor_delay, self.error_delay, self.qty = task_id, status_signal, product_signal, product, info, size, profile, monitor_delay, error_delay, qty
        self.session = requests.Session()
        self.settings = return_data("./data/settings.json")
        self.proxy_list = proxy
        self.session.verify = False
        self.product_json = self.size.split('|')[0]
        self.handle = self.size.split('|')[1]
        self.size_kw = self.size.split('|')[2]
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.driver = ''

        if self.proxy_list != False:
            self.update_random_proxy()

        self.image = ''
        self.main_site = self.info
        self.status_signal.emit({"msg": "Starting", "status": "normal"})

        self.safe_mode = len(self.size.split('|')) >= 4
        self.cart_id = ''
        self.session_token = ''
        self.queue_token = ''
        self.delivery_json = ''
        self.payment_id = ''
        self.checkout_total = ''
        self.initial_graphql = ''
        self.latest_response_graphql = ''

        self.checkpoint_data = None

        req = self.atc()

        # Check for new checkout flow
        if '/c/' in req.url:
            self.cart_id = req.url.split('?')[0].split('/')[-1]
            self.initial_graphql = self.fix_graphql(req)
            self.new_submit_address()
            self.new_submit_rate()
            self.new_submit_pay()
        else:
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

    def get_session(self):
        self.status_signal.emit({"msg": "Checking for session", "status": "normal"})
        session = load_session(self.profile['shipping_email'], self.main_site)
        if session == False:
            self.browser_login()
        else:
            for cookies in session[0]:
                self.session.cookies.set(cookies, session[0][cookies])
            self.status_signal.emit({"msg": "Validating session", "status": "normal"})
            account_get = self.session.get(self.main_site + 'account')
            if 'login' in account_get.url:
                delete_session(self.profile['shipping_email'], self.main_site)
                self.browser_login()
            else:
                self.status_signal.emit({"msg": "Valid session found!", "status": "normal"})

    # This code handles logging in for Pimoroni
    def browser_login(self):
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
        while True:
            while 'login' in driver.current_url or '/challenge' in driver.current_url:
                time.sleep(0.1)
            self.status_signal.emit({"msg": "Checking login session", "status": "normal"})

            for cookie in driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'], path=cookie['path'])

            account_check = self.session.get(f'{self.main_site}account')
            if 'login' not in account_check.url:
                self.status_signal.emit({"msg": "Session valid!", "status": "normal"})
                driver.close()
                save_session(self.profile['shipping_email'], self.main_site, self.session)
                return
            else:
                self.status_signal.emit({"msg": "Session invalid, please retry", "status": "normal"})
                driver.delete_all_cookies()
                driver.refresh()

    def open_browser(self):
        if self.safe_mode:
            self.status_signal.emit({"msg": "Opening Browser", "status": "normal"})
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
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(str(self.main_site))

    # This portion monitors for the item and will add to cart when it can
    def atc(self):
        variant = ''
        found = ''
        while True:
            try:
                if variant == '':
                    # This runs only on first loop.
                    if found == '':
                        self.status_signal.emit({"msg": "Searching for product", "status": "checking"})
                        found = False
                    elif found:
                        self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
                    # Gets item data from product.json endpoint.
                    products = self.session.get(self.main_site + self.product_json)
                    # Only operates when a valid response happens
                    if products.status_code == 200:
                        # List of all products is stores as json
                        products = products.json()['products']
                        # Loops through all products in json
                        for prod in products:
                            # Filters by item handle (text after 'product/' in URL)
                            handle = prod['handle']
                            # The handle on the product matches the stored in the bot
                            if handle == self.handle:
                                found = True
                                # Saves product image
                                self.image = prod['images'][0]['src']
                                # Now we loop through variants. You can think of these as different options for the product
                                # If an item as one size, it goes by Default Title.
                                # We need to do this as UK sites tend to have one "Raspberry Pi 4" page with the different RAM models as different variants
                                # US sites tend to have one separate item page per Pi 4.
                                for vr in prod['variants']:
                                    # If the variant name contains the size stored in bot.
                                    if self.compare_size(vr['title']):
                                        # If the variants "available" tag is true, it is in stock
                                        # This is how Pi Helper monitors these sites, by checking this tag on products!
                                        if vr['available']:
                                            # self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
                                            # Stores variant to 'variant' variable. Exits monitoring loop
                                            variant = vr['id']
                                            break
                                        else:
                                            self.status_signal.emit(
                                                {"msg": "Waiting for restock", "status": "monitoring"})
                                            # If product is not available, sleep for delay and try again. Rotates proxy if you use them
                                            self.update_random_proxy()
                                            time.sleep(float(self.monitor_delay))
                                # Since we found the handle, no need to check the other products. End loop early
                                break
                        # If product is NOT found (this shouldn't happen unless site change), sleep and try to find again
                        if not found:
                            self.status_signal.emit({"msg": "Waiting for product", "status": "monitoring"})
                            self.update_random_proxy()
                            time.sleep(float(self.monitor_delay))
                    elif products.status_code == 430:
                        # 430 is the response code when rate limited. Sleep for error delay and try again
                        self.status_signal.emit({"msg": f'IP Rate Limited!', "status": "error_no_log"})
                        self.update_random_proxy()
                        time.sleep(float(self.error_delay))
                    else:
                        # Sleep for error delay and try again
                        self.status_signal.emit(
                            {"msg": f'Error getting stock [{products.status_code}]', "status": "error"})
                        self.update_random_proxy()
                        time.sleep(float(self.error_delay))
                elif variant != '':
                    # Once the variant variable isn't empty, we now add to cart.
                    # Below is the data sent on carting
                    cart = {'utf8': '✓', 'form_type': 'product', 'id': variant, 'quantity': self.qty}
                    self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
                    url_to_post = f'{self.main_site}cart/add.js'
                    # We send the cart data to the cart url
                    self.session.post(url_to_post, data=cart, headers=self.request_headers(self.main_site))
                    self.status_signal.emit({"msg": "Added to cart", "status": "carted"})
                    # self.status_signal.emit({"msg": "Checking cart", "status": "normal"})
                    # This checks the cart. If the cart length is 0 (empty cart) it tries alt carting method
                    # cart_json = self.session.get(f'{self.main_site}cart.js').json()
                    self.status_signal.emit({"msg": "Initiating checkout", "status": "normal"})
                    req = self.session.get(f'{self.main_site}checkout')
                    # if cart_json['item_count'] == 0:
                    # self.status_signal.emit({"msg": "Adding to cart (Alt)", "status": "normal"})
                    # By simply going to 'https://www.shopname.com/cart/variant:1' with the variant ID we fetched earlier,
                    # we can also add to cart. This is slower and only a backup to the carting.
                    # req = self.session.get(f'{self.main_site}cart/{variant}:1')
                    # else:
                    # If your cart does have items, proceeds to checkout
                    if 'checkpoint' in req.url:
                        self.handle_checkpoint()
                    if ('checkout' in req.url) and 'stock_problem' not in req.url:
                        # This checks for the checkout page to be loaded. We can now proceed to checking out.
                        # If you have the webhook cart enabled, it sends a webhook to alert you have carted.
                        self.start = time.time()
                        if self.settings['webhookcart']:
                            new_web('carted', f"Shopify - {self.main_site}", self.image, self.product, self.profile['profile_name'])
                        return req
                    elif 'checkout' in req.url and 'stock_problems' in req.url:
                        # If you cart it and it is now out of stock, it will monitor that page until it can proceed again.
                        self.status_signal.emit({"msg": "Monitoring (Carted)", "status": "carted"})
                        # We simply remove the '/stock_problems' in the URL and try going to that URL again
                        # If we don't get '/stock_problems' in the URL, it is back in stock.
                        cart_time = req.url.replace('/stock_problems', '')
                        while True:
                            time.sleep(float(self.monitor_delay))
                            check_cart = self.session.get(cart_time)
                            # If you get a 429 response code, the checkout has expired. We must go back and monitor again
                            if check_cart.status_code == 429:
                                self.status_signal.emit({"msg": "Genning new session", "status": "idle"})
                                break
                            elif check_cart.status_code == 200:
                                # Loops on OOS
                                if 'stock_problems' in check_cart.url:
                                    time.sleep(float(self.monitor_delay))
                                else:
                                    # If its in stock, proceed with checkout
                                    return check_cart
                            else:
                                time.sleep(float(self.monitor_delay))
                    else:
                        # Error on cart, starts over
                        self.status_signal.emit({"msg": "Error on redirect", "status": "error"})
                        print(req.url)
                        self.session.cookies.clear()
                        time.sleep(float(self.error_delay))
            except Exception:
                self.status_signal.emit({"msg": "Error getting product info", "status": "error"})
                time.sleep(float(self.error_delay))

    # This function returns auth token and shipping rate
    # Shipping rate is the shipping method used during checkout
    def get_tokens(self, req):
        profile = self.profile
        while True:
            try:
                self.status_signal.emit({"msg": "Getting Auth Token", "status": "normal"})
                # Parses auth token
                auth_token = self.get_checkout_token(req.text)
                break
            except:
                self.status_signal.emit({"msg": "Error Fetching Auth", "status": "error"})
                time.sleep(float(self.error_delay))
        while True:
            try:
                # This uses a neat cart URL to load all shipping methods for the items in your cart.
                # It will choose the first one (cheapest method)
                self.status_signal.emit({"msg": "Getting Shipping Rates", "status": "normal"})
                jayson = self.session.get(
                    f'{self.main_site}cart/shipping_rates.json?shipping_address[zip]={str(profile["shipping_zipcode"]).replace(" ", "")}&shipping_address[country]={get_country_code(profile["shipping_country"])}&shipping_address[province]={profile["shipping_state"]}').json()
                if len(jayson['shipping_rates']) == 0:
                    return auth_token, ''
                full_rate = f'{jayson["shipping_rates"][0]["source"]}-{jayson["shipping_rates"][0]["code"]}-{jayson["shipping_rates"][0]["price"]}'
                break
            except:
                # Prints shipping rate json on failed fetch (for logging)
                self.status_signal.emit({"msg": "Error Fetching Shipping Rate", "status": "error"})
                print(f'Shipping rate response -> {jayson}')
                time.sleep(float(self.error_delay))
        # Returns both variables.
        return auth_token, full_rate

    def get_manual_rate(self):
        self.status_signal.emit({"msg": "Waiting for shipping rates", "status": "normal"})
        while True:
            manual_rate_get = self.session.get(
                f"{self.main_url}?previous_step=contact_information&step=shipping_method")
            soup = BeautifulSoup(manual_rate_get.content, 'html.parser')
            for radio_button in soup.find_all('div', {'class': 'radio-wrapper'}):
                if radio_button.has_attr('data-shipping-method'):
                    self.shipping_rate = radio_button.get('data-shipping-method')
                    print(f'Found Rate -> {self.shipping_rate}')
                    return
            time.sleep(1)

    # Here we handle the shipping details (first page on Shopify checkout)
    def submit_shipping(self):
        while True:
            try:
                profile = self.profile
                # This is the data you send when submitting shipping details
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
                # Adds shipping state ONLY if your profile has a state.
                if profile['shipping_state'] != '':
                    x['checkout[shipping_address][province]'] = profile['shipping_state'],
                self.status_signal.emit({"msg": "Submitting Shipping Info", "status": "normal"})
                # Sends data to appropriate URL.
                self.session.post(self.main_url, data=x,
                                  headers=self.request_headers(self.main_url + '?step=contact_information'))
                return
            except:
                self.status_signal.emit({"msg": "Error Submitting Shipping", "status": "error"})
                time.sleep(float(self.error_delay))

    # This is where we submit the shipping rate obtained above. This is the second page in the checkout process
    def submit_rates(self):
        if self.shipping_rate == '':
            self.get_manual_rate()
        while True:
            try:
                # This is the data sent on submitting shipping rate
                # A majority of sites will use the rate, but with spaces replaced with '%20'
                rate_data = {'_method': 'patch',
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
                # Sends data to appropriate URL.
                r = self.session.post(self.main_url, headers=self.request_headers(
                    self.main_url + '?previous_step=shipping_method&step=payment_method'), data=rate_data,
                                      allow_redirects=True)
                # If it doesn't work, it will try again but with the unformatted rate
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
                    r2 = self.session.post(self.main_url, headers=self.request_headers(
                        f'{self.main_url}?previous_step=shipping_method&step=payment_method'), data=x,
                                           allow_redirects=True)
                    # Checks if alt rate worked
                    if 'step=payment_method' in r2.url:
                        return
                    else:
                        # Tries again (can be a site error)
                        self.status_signal.emit({"msg": "Error submitting rates", "status": "error"})
                        time.sleep(float(self.error_delay))
                else:
                    # If first rate submit works, proceed
                    return
            except Exception as e:
                self.status_signal.emit({"msg": "Error submitting rates", "status": "error"})
                time.sleep(float(self.error_delay))

    # This will calculate taxes, and returns full price and gateway ID (needed for payment)
    def calc_taxes(self):
        while True:
            try:
                # Just parses page
                self.status_signal.emit({"msg": "Calculating Tax", "status": "normal"})
                rate_after = self.session.get(f'{self.main_url}?step=payment_method', allow_redirects=True)
                price = self.get_price(rate_after.text)
                gateway = self.get_gateway(rate_after.text)
                return price, gateway
            except:
                # If theres an error, it will try again after error delay
                self.status_signal.emit({"msg": "Error Calculating Tax", "status": "error"})
                time.sleep(float(self.error_delay))

    # Now we submit payment. This is the third and final page of the checkout process.
    def submit_payment(self):
        # We must encrypt the payment using Shopify's checkout.shopifycs.com.
        self.status_signal.emit({"msg": "Encrypting Payment", "status": "normal"})
        profile = self.profile
        url_to_use = self.main_site.replace("https://", '').replace('www.', '')
        # Loads your card details into a json
        cs = '{"credit_card":{"number":"' + profile[
            "card_number"] + '","name":"' + f'{profile["shipping_fname"]} {profile["shipping_lname"]}' + '","month":' + str(
            int(profile["card_month"])) + ',"year":' + profile["card_year"] + ',"verification_value":"' + profile[
                 "card_cvv"] + '"}, "payment_session_scope": "' + url_to_use + '"}'
        card_payload = str(cs).replace('\n', '')

        # Headers for encryption
        shopify_cs_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://checkout.shopifycs.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://checkout.shopifycs.com/'
        }
        # Sends card data for encryption
        encrypt = self.session.post('https://deposit.us.shopifycs.com/sessions', headers=shopify_cs_headers,
                                    data=card_payload, verify=False)
        # Returns an encrypted ID for your details
        encrypt_info = encrypt.json()['id']

        # This is the data sent on submitting payment
        pay_data = {'_method': 'patch',
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
        # Sends data to payment URL.
        submit = self.session.post(self.main_url, allow_redirects=True, headers=self.request_headers(self.main_url),
                                   data=pay_data)

        # If processing or authentications is in the URL, payment has been submitted.
        if ('processing' in submit.url) or 'authentications' in submit.url:
            self.status_signal.emit({"msg": "Processing", "status": "alt"})
            pay_url = submit.url + "?from_processing_page=1"
            while True:
                # Poll the processing/authentication URL
                after = self.session.get(pay_url, allow_redirects=True)
                # Sometimes, when Shopify sites are busy you'll just get a "Thank you for your order" page and it might be a checkout.
                # I've only really seen this in testing with PiHut
                if 'Thanks for your order' in after.text:
                    break
                # PiHut authentication handling. Fun stuff
                if 'authentications' in after.url:
                    # Auth key is just the key at the end of the URL.
                    keys = after.url.split("/")
                    cardinal_key = keys[len(keys) - 1]
                    num_of_checks = 1
                    is_202 = False
                    self.status_signal.emit({"msg": f"Handling UK Auth", "status": "alt"})
                    while True:
                        self.status_signal.emit({"msg": f"Handling UK Auth ({num_of_checks})", "status": "alt_no_log"})
                        # Polls the authentication URL. It will give a 202 response code when authenticating,
                        # and a 200 response code when it has passed authentication
                        auth_get = self.session.get(f'{after.url.split("?")[0]}/poll?authentication={cardinal_key}')

                        # If it does have a 202 error code, set is_202 to True
                        if auth_get.status_code == 202 and not is_202:
                            is_202 = True
                        elif auth_get.status_code == 200 and is_202:
                            # Authentication has passed
                            break
                        elif num_of_checks >= 5 and not is_202:
                            # If it doesn't read a 202 response in 5 times, it will retry.
                            self.status_signal.emit({"msg": f"Retrying Auth", "status": "alt_no_log"})
                            auth_get = self.session.get(after.url.split("?")[0])
                            break
                        else:
                            # Increment num of checks and sleep
                            num_of_checks += 1
                            time.sleep(1)

                    # Only happens if you exit loop and you at one point read a 202
                    if is_202:
                        self.status_signal.emit({"msg": "Processing (Passing Auth)", "status": "alt"})
                        # Now we can go to the auth URL and it will redirect to processing
                        after = self.session.get(f'{auth_get.url}?')
                        if '/processing' in after.url:
                            # Processing. This is when you see the wheel spinning and it says "Processing"
                            self.status_signal.emit({"msg": "Processing", "status": "alt"})
                            base_url = after.url
                            while True:
                                pay_url = base_url + "?from_processing_page=1"
                                # Polls processing page
                                after = self.session.get(pay_url)
                                if '/processing' in after.url:
                                    time.sleep(1)
                                else:
                                    # Processing is done. Exit poll loop
                                    break

                elif '/processing' in after.url:
                    # Processing is not done. Stay in poll loop
                    time.sleep(1)
                else:
                    # Processing is done. Exit poll loop
                    break
            checkout_time = time.time() - self.start
            if '&validate=true' in after.url:
                # This means the checkout was unsuccessful.
                price_to_use = int(self.price) / 100
                self.status_signal.emit({"msg": "Checkout Failed", "status": "error"})
                new_web('failed', f"Shopify - {self.main_site}", self.image, self.product,
                        self.profile['profile_name'],
                        price="{:.2f}".format(price_to_use),
                        checkout_time=checkout_time)

            elif 'thank_you' in after.url:
                # This means the checkout was successful.
                price_to_use = int(self.price) / 100
                self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                new_web('success', f"Shopify - {self.main_site}", self.image, self.product,
                        self.profile['profile_name'],
                        price="{:.2f}".format(price_to_use),
                        checkout_time=checkout_time)

            else:
                # Sometimes there can be weird URLs after submitting order.
                self.status_signal.emit({"msg": "Checking order", "status": "alt"})
                price_to_use = int(self.price) / 100
                r = self.session.get(self.main_url + "/thank_you")
                if r.url.endswith('/processing'):
                    # IDK there is some weird processing thing that this handles. It happened one time I think
                    self.status_signal.emit({"msg": "Checking order (Processing)", "status": "alt"})
                    while True:
                        time.sleep(2)
                        r = self.session.get(r.url)
                        if not r.url.endswith('/processing'):
                            break
                # If it shows up with "order" in URL, it is a good checkout.
                if 'order' in r.url or 'thank_you' in r.url:
                    self.status_signal.emit({"msg": "Successful Checkout", "status": "success"})
                    if self.settings['webhooksuccess']:
                        new_web('success', f"Shopify - {self.main_site}", self.image, self.product,
                                self.profile['profile_name'],
                                price="{:.2f}".format(price_to_use),
                                checkout_time=checkout_time)
                else:
                    # Checkout failed.
                    print(traceback.format_exc())
                    self.status_signal.emit({"msg": "Checkout Failed", "status": "error"})
                    if self.settings['webhookfailed']:
                        new_web('failed', f"Shopify - {self.main_site}", self.image, self.product,
                                self.profile['profile_name'],
                                price="{:.2f}".format(price_to_use),
                                checkout_time=checkout_time)

        else:
            # Other error checking out
            print(traceback.format_exc())
            price_to_use = int(self.price) / 100
            new_web('failed', f"Shopify - {self.main_site}", self.image, self.product,
                    self.profile['profile_name'],
                    price="{:.2f}".format(price_to_use))

    def handle_checkpoint(self):
        captcha_response = ''
        checkpoint_form = {
            'authenticity_token': self.auth_token,
            'g-recaptcha-response': captcha_response,
            'data_via': 'cookie'
        }

    # These are the headers used during the whole process, with a field to change the referer URL.
    def request_headers(self, url):
        x = {'Content-Type': 'application/x-www-form-urlencoded',
             "Accept": 'application/json, text/javascript, */*; q=0.01',
             'sec-fetch-site': 'same-origin',
             'sec-fetch-mode': 'navigate',
             'sec-fetch-user': '?1',
             'sec-fetch-dest': 'document',
             'sec-ch-ua-mobile': '?0',
             'accept-encoding': 'gzip, deflate',
             'cache-control': 'max-age=0',
             'upgrade-insecure-requests': '1',
             'dnt': '1',
             'referer': url
             }
        return x

    # Method to determine if the variant is the one we want to parse.
    def compare_size(self, title):
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

    # Method to update proxy to random one in list
    def update_random_proxy(self):
        if self.proxy_list != False:
            proxy_to_use = format_proxy(random.choice(self.proxy_list))
            self.session.proxies.update(proxy_to_use)

    # Functions added for new checkout

    def new_submit_address(self):
        self.status_signal.emit({"msg": "Submitting address", "status": "normal"})
        graphql = self.new_shipping(self.initial_graphql)
        self.queue_token = graphql[list(graphql.keys())[-2]]['queueToken']
        self.session_token = self.get_session_token()
        shipping_post = self.session.post(f"{self.main_site}checkouts/unstable/graphql", data=json.dumps(graphql),
                                          headers=self.new_headers())
        self.queue_token = shipping_post.json()['data']['session']['negotiate']['result']['queueToken']
        self.latest_response_graphql = shipping_post.json()

    def new_submit_rate(self):
        self.status_signal.emit({"msg": "Loading shipping rates", "status": "normal"})
        graphql = self.new_shipping(self.initial_graphql)
        for i in range(0, 20):
            try:
                fetch_post = self.session.post(f"{self.main_site}checkouts/unstable/graphql",
                                                  data=json.dumps(graphql), headers=self.new_headers())
                self.latest_response_graphql = fetch_post.json()
                self.queue_token = self.latest_response_graphql['data']['session']['negotiate']['result']['queueToken']
                if fetch_post.json()['data']['session']['negotiate']['result']['sellerProposal']['delivery'][
                    'deliveryLines'][0]['availableDeliveryStrategies']:
                    self.delivery_json = fetch_post.json()['data']['session']['negotiate']['result']['sellerProposal']['delivery'][
                            'deliveryLines'][0]['availableDeliveryStrategies'][0]
                    break
            except:
                print('Not Loaded')
            finally:
                time.sleep(0.5)
        self.status_signal.emit({"msg": "Submitting shipping rate", "status": "normal"})
        rate_json = json.dumps(self.new_rate())
        rate_post = self.session.post(f"{self.main_site}checkouts/unstable/graphql", data=rate_json,headers=self.new_headers())
        self.latest_response_graphql = rate_post.json()
        self.queue_token = self.latest_response_graphql['data']['session']['negotiate']['result']['queueToken']
        self.checkout_total = self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['total']['value']
        self.tax_total = self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['tax']['totalTaxAmount']['value']

    def new_submit_pay(self):
        # We must encrypt the payment using Shopify's checkout.shopifycs.com.
        self.status_signal.emit({"msg": "Encrypting Payment", "status": "normal"})
        profile = self.profile
        url_to_use = self.main_site.replace("https://", '').replace('www.', '')
        # Loads your card details into a json
        cs = '{"credit_card":{"number":"' + profile[
            "card_number"] + '","name":"' + f'{profile["shipping_fname"]} {profile["shipping_lname"]}' + '","month":' + str(
            int(profile["card_month"])) + ',"year":' + profile["card_year"] + ',"verification_value":"' + \
             profile["card_cvv"] + '"}, "payment_session_scope": "' + url_to_use + '"}'
        card_payload = str(cs).replace('\n', '')

        # Headers for encryption
        shopify_cs_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://checkout.shopifycs.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://checkout.shopifycs.com/'

        }
        # Sends card data for encryption
        encrypt = self.session.post('https://deposit.us.shopifycs.com/sessions', headers=shopify_cs_headers,
                                    data=card_payload, verify=False)
        # Returns an encrypted ID for your details
        encrypt_info = encrypt.json()['id']

        self.status_signal.emit({"msg": "Submitting Payment", "status": "normal"})
        pay_json = json.dumps(self.new_pay(encrypt_info))
        pay_post = self.session.post(f"{self.main_site}checkouts/unstable/graphql", data=pay_json,
                                     headers=self.new_headers())

        if pay_post.json()['data']['submitForCompletion'] and pay_post.json()['data']['submitForCompletion']['receipt']:
            auth_needed = False
            checkout_time = time.time() - self.start
            self.receipt_id = pay_post.json()['data']['submitForCompletion']['receipt']['id']
            self.status_signal.emit({"msg": "Processing", "status": "alt"})
            for i in range(0, 60):
                processing_data = self.new_poll()
                processing_post = self.session.post(f"{self.main_site}checkouts/unstable/graphql",
                                                    data=json.dumps(processing_data),
                                                    headers=self.new_headers())
                if processing_post.json()['data']['receipt']['__typename'] == 'ActionRequiredReceipt':
                    #UK Auth
                    auth_needed = True
                    auth_url = processing_post.json()['data']['receipt']['action']['url']
                    auth_key = auth_url.split('/')[-1]
                    self.status_signal.emit({"msg": f"Handling UK Auth", "status": "alt"})
                    auth_get_first = self.session.get(auth_url)
                    num_of_checks = 1
                    is_202 = False
                    while True:
                        self.status_signal.emit({"msg": f"Handling UK Auth ({num_of_checks})", "status": "alt_no_log"})
                        # Polls the authentication URL. It will give a 202 response code when authenticating,
                        # and a 200 response code when it has passed authentication
                        auth_get = self.session.get(f'{auth_url}/polling?authentication={auth_key}')
                        # If it does have a 202 error code, set is_202 to True
                        if auth_get.status_code == 202 and not is_202:
                            is_202 = True
                        elif auth_get.status_code == 204 and is_202:
                            # Authentication has passed
                            auth_get = self.session.get(f'{auth_url}/polling')
                            break
                        else:
                            # Increment num of checks and sleep
                            num_of_checks += 1
                            time.sleep(1)

                elif processing_post.json()['data']['receipt']['__typename'] == 'ProcessingReceipt':
                    if auth_needed:
                        auth_needed = False
                        self.status_signal.emit({"msg": "Processing (Passed Auth)", "status": "alt"})
                    time.sleep(0.1)
                elif processing_post.json()['data']['receipt']['__typename'] == 'FailedReceipt':
                    self.status_signal.emit({
                                                "msg": f"Checkout Failed ({processing_post.json()['data']['receipt']['processingError']['code']})",
                                                "status": "error"})
                    if self.settings['webhookfailed']:
                        new_web('failed', f"Shopify - {self.main_site}", self.image, self.product,
                                self.profile['profile_name'],
                                price=f"{self.checkout_total['amount']} {self.checkout_total['currencyCode']}",
                                checkout_time=checkout_time)

                    break
                else:
                    self.status_signal.emit({"msg": f"Successful Checkout", "status": "success"})
                    if self.settings['webhooksuccess']:
                        new_web('success', f"Shopify - {self.main_site}", self.image, self.product,
                                self.profile['profile_name'],
                                price=f"{self.checkout_total['amount']} {self.checkout_total['currencyCode']}",
                                checkout_time=checkout_time)
    def delete_between_strings(self, text, start_str, end_str):
        start_index = text.find(start_str)
        end_index = text.find(end_str)

        if start_index == -1 or end_index == -1:
            return text

        if start_index > end_index:
            start_index, end_index = end_index, start_index

        return text[:start_index] + text[end_index + len(end_str):]

    def cookie_string(self):
        to_return = ''
        for cookie in self.session.cookies:
            to_return += f'; {cookie.name}={cookie.value}'
        return to_return[2:]

    def get_session_token(self):
        for cookie in self.session.cookies:
            if cookie.name.startswith('checkout_session_token'):
                cookie_json = json.loads(urllib.parse.unquote(cookie.value))
                return cookie_json['token']

    def new_headers(self):
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
            'accept-language': 'en-US',
            'sec-ch-ua-mobile': '?0',
            'Cookie': self.cookie_string(),
            'x-checkout-one-session-token': self.get_session_token(),
            'x-checkout-web-deploy-stage': 'production',
            'x-checkout-web-source-id': self.cart_id,
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        return headers

    def new_shipping(self, graphql_json):
        profile = self.profile
        currency_key = list(graphql_json.keys())[0]
        data_json = json.loads(list(graphql_json.keys())[-1][64:])
        main_json = graphql_json[list(graphql_json.keys())[-1]]
        currency_json = graphql_json[currency_key]

        self.session_token = self.get_session_token()
        self.checkpoint_data = data_json['checkpointData']

        tax_key = 'totalTaxAmount' if main_json['session']['negotiate']['result']['sellerProposal']['tax'][
                                'totalTaxAmount'] else 'totalAmountIncludedInTarget'
        merch_dict = main_json['session']['negotiate']['result']['buyerProposal']['merchandise']['merchandiseLines'][
            0]
        shipping_data = {
            "query": "query Proposal($delivery:DeliveryTermsInput,$discounts:DiscountTermsInput,$payment:PaymentTermInput,$merchandise:MerchandiseTermInput,$buyerIdentity:BuyerIdentityTermInput,$taxes:TaxTermInput,$sessionInput:SessionTokenInput!,$checkpointData:String,$queueToken:String,$reduction:ReductionInput,$changesetTokens:[String!],$tip:TipTermInput,$note:NoteInput,$localizationExtension:LocalizationExtensionInput,$nonNegotiableTerms:NonNegotiableTermsInput,$scriptFingerprint:ScriptFingerprintInput,$transformerFingerprintV2:String,$optionalDuties:OptionalDutiesInput,$attribution:AttributionInput,$captcha:CaptchaInput,$poNumber:String,$saleAttributions:SaleAttributionsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{delivery:$delivery,discounts:$discounts,payment:$payment,merchandise:$merchandise,buyerIdentity:$buyerIdentity,taxes:$taxes,reduction:$reduction,tip:$tip,note:$note,poNumber:$poNumber,nonNegotiableTerms:$nonNegotiableTerms,localizationExtension:$localizationExtension,scriptFingerprint:$scriptFingerprint,transformerFingerprintV2:$transformerFingerprintV2,optionalDuties:$optionalDuties,attribution:$attribution,captcha:$captcha,saleAttributions:$saleAttributions},checkpointData:$checkpointData,queueToken:$queueToken,changesetTokens:$changesetTokens}){__typename result{...on NegotiationResultAvailable{queueToken buyerProposal{...BuyerProposalDetails __typename}sellerProposal{...ProposalDetails __typename}__typename}...on CheckpointDenied{redirectUrl __typename}...on Throttled{pollAfter queueToken pollUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}...on NegotiationResultFailed{__typename}__typename}errors{code localizedMessage nonLocalizedMessage localizedMessageHtml...on RemoveTermViolation{target __typename}...on AcceptNewTermViolation{target __typename}...on ConfirmChangeViolation{from to __typename}...on UnprocessableTermViolation{target __typename}...on UnresolvableTermViolation{target __typename}...on GenericError{__typename}__typename}}__typename}}fragment BuyerProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...ProposalDeliveryFragment __typename}merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponents{...MerchandiseBundleLineComponent __typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}attribution{attributions{...on AttributionItem{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}__typename}fragment ProposalDiscountFragment on DiscountTermsV2{__typename...on FilledDiscountTerms{lines{...DiscountLineDetailsFragment __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment DiscountLineDetailsFragment on DiscountLine{allocations{...on DiscountAllocatedAllocationSet{__typename allocations{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}target{index targetType stableId __typename}__typename}}__typename}discount{...DiscountDetailsFragment __typename}lineAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}fragment DiscountDetailsFragment on Discount{...on CustomDiscount{title presentationLevel signature signatureUuid type value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on CodeDiscount{title code presentationLevel __typename}...on DiscountCodeTrigger{code __typename}...on AutomaticDiscount{presentationLevel title __typename}__typename}fragment ProposalDeliveryFragment on DeliveryTerms{__typename...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken deliveryLines{destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}__typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}...on DeliveryStrategyReference{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{title handle custom description acceptsInstructions phoneRequired methodType carrierName brandedPromise{logoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name __typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment FilledMerchandiseLineTargetCollectionFragment on FilledMerchandiseLineTargetCollection{linesV2{...on MerchandiseLine{stableId merchandise{...MerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on MerchandiseBundleLineComponent{stableId merchandise{...MerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}fragment MerchandiseFragment on ProposalMerchandise{...SourceProvidedMerchandise...on ProductVariantMerchandise{id digest variantId title subtitle requiresShipping properties{...MerchandiseProperties __typename}__typename}...on ContextualizedProductVariantMerchandise{id digest variantId title subtitle requiresShipping sellingPlan{id digest name prepaid deliveriesPerBillingCycle subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}properties{...MerchandiseProperties __typename}__typename}...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}fragment SourceProvidedMerchandise on Merchandise{...on SourceProvidedMerchandise{__typename product{id title productType vendor __typename}digest variantId optionalIdentifier title untranslatedTitle subtitle untranslatedSubtitle taxable giftCard requiresShipping price{amount currencyCode __typename}deferredAmount{amount currencyCode __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}options{name value __typename}properties{...MerchandiseProperties __typename}taxCode taxesIncluded weight{value unit __typename}sku}__typename}fragment MerchandiseProperties on MerchandiseProperty{name value{...on MerchandisePropertyValueString{string:value __typename}...on MerchandisePropertyValueInt{int:value __typename}...on MerchandisePropertyValueFloat{float:value __typename}...on MerchandisePropertyValueBoolean{boolean:value __typename}...on MerchandisePropertyValueJson{json:value __typename}__typename}visible __typename}fragment ProductVariantMerchandiseDetails on ProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle product{id vendor productType __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{id subscriptionDetails{billingInterval __typename}__typename}giftCard __typename}fragment ContextualizedProductVariantMerchandiseDetails on ContextualizedProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle sku price{amount currencyCode __typename}product{id vendor productType __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}giftCard deferredAmount{amount currencyCode __typename}__typename}fragment LineAllocationDetails on LineAllocation{stableId quantity totalAmountBeforeReductions{amount currencyCode __typename}totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}unitPrice{price{amount currencyCode __typename}measurement{referenceUnit referenceValue __typename}__typename}allocations{...on LineComponentDiscountAllocation{allocation{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}__typename}__typename}__typename}fragment MerchandiseBundleLineComponent on MerchandiseBundleLineComponent{__typename stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}}fragment ProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken deliveryLines{destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}__typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{originLocation{id __typename}title handle custom description acceptsInstructions phoneRequired methodType carrierName brandedPromise{logoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromiseProviderApiClientId deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name distanceFromBuyer{unit value __typename}__typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}payment{...on FilledPaymentTerms{availablePayments{paymentMethod{...on AnyDirectPaymentMethod{__typename availablePaymentProviders{paymentMethodIdentifier name brands orderingIndex displayName availablePresentmentCurrencies __typename}}...on AnyOffsitePaymentMethod{__typename availableOffsiteProviders{__typename paymentMethodIdentifier name paymentBrands orderingIndex showRedirectionNotice availablePresentmentCurrencies}}...on AnyCustomOnsitePaymentMethod{__typename availableCustomOnsiteProviders{__typename paymentMethodIdentifier name paymentBrands orderingIndex availablePresentmentCurrencies}}...on DirectPaymentMethod{__typename paymentMethodIdentifier}...on GiftCardPaymentMethod{__typename}...on AnyRedeemablePaymentMethod{__typename availableRedemptionSources orderingIndex}...on WalletsPlatformConfiguration{name configurationParams __typename}...on AnyWalletPaymentMethod{availableWalletPaymentConfigs{...on PaypalWalletConfig{__typename name clientId merchantId venmoEnabled payflow paymentIntent paymentMethodIdentifier orderingIndex}...on ShopPayWalletConfig{__typename name storefrontUrl paymentMethodIdentifier orderingIndex}...on ShopifyInstallmentsWalletConfig{__typename name availableLoanTypes maxPrice{amount currencyCode __typename}minPrice{amount currencyCode __typename}supportedCountries supportedCurrencies giftCardsNotAllowed subscriptionItemsNotAllowed ineligibleTestModeCheckout ineligibleLineItem paymentMethodIdentifier orderingIndex}...on FacebookPayWalletConfig{__typename name partnerId partnerMerchantId supportedContainers acquirerCountryCode mode paymentMethodIdentifier orderingIndex}...on ApplePayWalletConfig{__typename name supportedNetworks walletAuthenticationToken walletOrderTypeIdentifier walletServiceUrl paymentMethodIdentifier orderingIndex}...on GooglePayWalletConfig{__typename name allowedAuthMethods allowedCardNetworks gateway gatewayMerchantId merchantId authJwt environment paymentMethodIdentifier orderingIndex}...on AmazonPayClassicWalletConfig{__typename name orderingIndex}__typename}__typename}...on LocalPaymentMethodConfig{__typename paymentMethodIdentifier name displayName additionalParameters{...on IdealBankSelectionParameterConfig{__typename label options{label value __typename}}__typename}orderingIndex}...on AnyPaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex displayName}...on PaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier}...on CustomPaymentMethod{id name additionalDetails paymentInstructions __typename}...on ManualPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex __typename}...on CustomPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on NoopPaymentMethod{__typename}...on GiftCardPaymentMethod{__typename}...on CustomerCreditCardPaymentMethod{__typename expired expiryMonth expiryYear name orderingIndex...CustomerCreditCardPaymentMethodFragment}...on PaypalBillingAgreementPaymentMethod{__typename orderingIndex paypalAccountEmail...PaypalBillingAgreementPaymentMethodFragment}__typename}__typename}paymentLines{...PaymentLines __typename}billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}paymentFlexibilityPaymentTermsTemplate{id translatedName dueDate dueInDays __typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}poNumber merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponents{...MerchandiseBundleLineComponent __typename}__typename}__typename}__typename}note{customAttributes{key value __typename}message __typename}scriptFingerprint{signature signatureUuid lineItemScriptChanges paymentScriptChanges shippingScriptChanges __typename}transformerFingerprintV2 buyerIdentity{...on FilledBuyerIdentityTerms{buyerIdentity{...on GuestProfile{presentmentCurrency countryCode market{id handle __typename}__typename}...on CustomerProfile{id presentmentCurrency fullName firstName lastName countryCode email imageUrl acceptsMarketing phone billingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}shippingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}storeCreditAccounts{id balance{amount currencyCode __typename}__typename}__typename}...on BusinessCustomerProfile{checkoutExperienceConfiguration{availablePaymentOptions checkoutCompletionTarget editableShippingAddress __typename}id presentmentCurrency fullName firstName lastName acceptsMarketing companyName countryCode email phone selectedCompanyLocation{id name __typename}locationCount billingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}shippingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}__typename}contactInfoV2{...on EmailFormContents{email __typename}...on SMSFormContents{phoneNumber __typename}__typename}marketingConsent{...on SMSMarketingConsent{value __typename}...on EmailMarketingConsent{value __typename}__typename}shopPayOptInPhone __typename}__typename}recurringTotals{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}duty{...on FilledDutyTerms{totalDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}exemptions{taxExemptionReason targets{...on TargetAllLines{__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tip{tipSuggestions{...on TipSuggestion{__typename percentage amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}}__typename}terms{...on FilledTipTerms{tipLines{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}localizationExtension{...on LocalizationExtension{fields{...on LocalizationExtensionField{key title value __typename}__typename}__typename}__typename}landedCostDetails{incotermInformation{incoterm reason __typename}__typename}nonNegotiableTerms{signature contents{signature targetTerms targetLine{allLines index __typename}attributes __typename}__typename}optionalDuties{buyerRefusesDuties refuseDutiesPermitted __typename}attribution{attributions{...on AttributionItem{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}managedByMarketsPro captcha{...on Captcha{provider challenge sitekey token __typename}...on PendingTerms{taskId pollDelay __typename}__typename}__typename}fragment CustomerCreditCardPaymentMethodFragment on CustomerCreditCardPaymentMethod{cvvSessionId paymentMethodIdentifier token displayLastDigits brand billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaypalBillingAgreementPaymentMethodFragment on PaypalBillingAgreementPaymentMethod{paymentMethodIdentifier token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaymentLines on PaymentLine{specialInstructions amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier creditCard{...on CreditCard{brand lastDigits __typename}__typename}__typename}...on GiftCardPaymentMethod{code balance{amount currencyCode __typename}__typename}...on RedeemablePaymentMethod{redemptionSource redemptionContent{...on ShopCashRedemptionContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}__typename}redemptionId destinationAmount{amount currencyCode __typename}sourceAmount{amount currencyCode __typename}__typename}__typename}__typename}...on WalletsPlatformPaymentMethod{name walletParams __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{paypalBillingAddress:billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token paymentMethodIdentifier acceptedSubscriptionTerms expiresAt __typename}...on ApplePayWalletContent{data signature version lastDigits paymentMethodIdentifier __typename}...on GooglePayWalletContent{signature signedMessage protocolVersion paymentMethodIdentifier __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode paymentMethodIdentifier __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken paymentMethodIdentifier __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name additionalParameters{...on IdealPaymentMethodParameters{bank __typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on OffsitePaymentMethod{paymentMethodIdentifier name __typename}...on CustomPaymentMethod{id name additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on CustomOnsitePaymentMethod{paymentMethodIdentifier name encryptedAttributes __typename}...on ManualPaymentMethod{id name paymentMethodIdentifier __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on CustomerCreditCardPaymentMethod{...CustomerCreditCardPaymentMethodFragment __typename}...on PaypalBillingAgreementPaymentMethod{...PaypalBillingAgreementPaymentMethodFragment __typename}...on NoopPaymentMethod{__typename}__typename}__typename}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token classicThankYouPageUrl poNumber orderIdentity{buyerIdentifier id __typename}shopPayArtifact{optIn{vaultPhone __typename}__typename}eligibleForMarketingOptIn purchaseOrder{...ReceiptPurchaseOrder __typename}orderCreationStatus{__typename}paymentDetails{creditCardBrand creditCardLastFourDigits __typename}shopAppLinksAndResources{mobileUrl qrCodeUrl canTrackOrderUpdates shopInstallmentsViewSchedules shopInstallmentsMobileUrl installmentsHighlightEligible mobileUrlAttributionPayload shopAppEligible shopAppQrCodeKillswitch shopPayOrder buyerHasShopApp buyerHasShopPay orderUpdateOptions __typename}postPurchasePageRequested postPurchaseVaultedPaymentMethodStatus __typename}...on ProcessingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}__typename}...on FailedReceipt{id processingError{...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on PaymentFailed{code messageUntranslated __typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}fragment ReceiptPurchaseOrder on PurchaseOrder{__typename sessionToken totalAmountToPay{amount currencyCode __typename}delivery{...on PurchaseOrderDeliveryTerms{deliveryLines{__typename deliveryStrategy{handle title description methodType pickupLocation{...on PickupInStoreLocation{name address{address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}instructions __typename}__typename}__typename}lineAmount{amount currencyCode __typename}destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}__typename}groupType}__typename}__typename}payment{...on PurchaseOrderPaymentTerms{billingAddress{__typename...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}}paymentLines{amount{amount currencyCode __typename}postPaymentMessage dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier vaultingAgreement creditCard{brand lastDigits __typename}billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomerCreditCardPaymentMethod{brand displayLastDigits token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on PurchaseOrderGiftCardPaymentMethod{code __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token expiresAt __typename}...on ApplePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}data signature version __typename}...on GooglePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}signature signedMessage protocolVersion __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on OffsitePaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on ManualPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on PaypalBillingAgreementPaymentMethod{token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}buyerIdentity{...on PurchaseOrderBuyerIdentityTerms{contactMethod{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}marketingConsent{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}__typename}__typename}merchandise{merchandiseLines{stableId merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}tax{totalTaxAmount{amount currencyCode __typename}__typename}discounts{lines{deliveryAllocations{amount{amount currencyCode __typename}index __typename}__typename}__typename}}fragment ProductVariantSnapshotMerchandiseDetails on ProductVariantSnapshot{variantId options{name value __typename}productTitle title sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}__typename}",
            'variables': {
                "checkpointData": self.checkpoint_data,
                'sessionInput': {
                    'sessionToken': self.session_token
                },
                'queueToken': self.queue_token,
                'discounts': {
                    'lines': [],
                    'acceptUnexpectedDiscounts': True
                },
                'delivery': {
                    'deliveryLines': [
                        {
                            'destination': {
                                'partialStreetAddress': {
                                    'address1': profile['shipping_a1'],
                                    'address2': profile['shipping_a2'],
                                    "city": profile['shipping_city'],
                                    "countryCode": get_country_code(profile['shipping_country']),
                                    "postalCode": profile['shipping_zipcode'],
                                    "firstName": profile['shipping_fname'],
                                    "lastName": profile['shipping_lname'],
                                    "zoneCode": profile['shipping_state'],
                                    "phone": self.format_phone2(profile['shipping_phone'])
                                }
                            },
                            "selectedDeliveryStrategy": {
                                "deliveryStrategyMatchingConditions": {
                                    "estimatedTimeInTransit": {
                                        "any": True
                                    },
                                    "shipments": {
                                        "any": True
                                    }
                                },
                                "options": {}
                            },
                            "targetMerchandiseLines": {
                                "lines": []
                            },
                            "deliveryMethodTypes": [
                                "SHIPPING"
                            ],
                            "expectedTotalPrice": {
                                "any": True
                            },
                            "destinationChanged": True
                        }
                    ],
                    "noDeliveryRequired": [],
                    "useProgressiveRates": True,
                    "prefetchShippingRatesStrategy": None,
                    "interfaceFlow": "SHOPIFY"
                },
                "merchandise": {
                    "merchandiseLines": [
                        {
                            "stableId": merch_dict['stableId'],
                            "merchandise": {
                                "productVariantReference": {
                                    "id": merch_dict['merchandise']['id'],
                                    "variantId": merch_dict['merchandise']['variantId'],
                                    "properties": [],
                                    "sellingPlanId": None,
                                    "sellingPlanDigest": None
                                }
                            },
                            "quantity": {
                                "items": {
                                    "value": merch_dict['quantity']['items']['value']
                                }
                            },
                            "expectedTotalPrice": {
                                "value": {
                                    "amount": merch_dict['totalAmount']['value']['amount'],
                                    "currencyCode": merch_dict['totalAmount']['value']['currencyCode']
                                }
                            },
                            "lineComponents": []
                        }
                    ]
                },
                "payment": {
                    "totalAmount": {
                        "any": True
                    },
                    "paymentLines": [],
                    "billingAddress": {
                        "streetAddress": {
                            'address1': profile['billing_a1'],
                            'address2': profile['billing_a2'],
                            "city": profile['billing_city'],
                            "countryCode": get_country_code(profile['billing_country']),
                            "postalCode": profile['billing_zipcode'],
                            "firstName": profile['billing_fname'],
                            "lastName": profile['billing_lname'],
                            "zoneCode": profile['billing_state'],
                            "phone": self.format_phone2(profile['billing_phone'])
                        }
                    }
                },
                "buyerIdentity": {
                    "buyerIdentity": {
                        "presentmentCurrency": currency_json['shop']['currencyCode']
                    },
                    "contactInfoV2": {
                        "emailOrSms": {
                            "value": profile['shipping_email'],
                            "emailOrSmsChanged": False
                        }
                    },
                    "marketingConsent": [],
                    "shopPayOptInPhone": {
                        "number": self.format_phone2(profile['shipping_phone']),
                        "countryCode": get_country_code(profile['billing_country'])
                    }
                },
                "tip": {
                    "tipLines": []
                },
                "taxes": {
                    "proposedAllocations": None,
                    "proposedTotalAmount": {
                        "value": {
                            "amount": main_json['session']['negotiate']['result']['sellerProposal']['tax'][
                                tax_key]['value']['amount'],
                            "currencyCode": main_json['session']['negotiate']['result']['sellerProposal']['tax'][
                                tax_key]['value']['currencyCode']
                        }
                    },
                    "proposedTotalIncludedAmount": None,
                    "proposedMixedStateTotalAmount": None,
                    "proposedExemptions": []
                },
                "note": {
                    "message": None,
                    "customAttributes": []
                },
                "localizationExtension": {
                    "fields": []
                },
                "nonNegotiableTerms": None,
                "optionalDuties": {
                    "buyerRefusesDuties": False
                }
            },
            "operationName": "Proposal"
        }

        return shipping_data

    def new_rate(self):
        profile = self.profile
        tax_key = 'totalTaxAmount' if self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['tax'][
            'totalTaxAmount'] else 'totalAmountIncludedInTarget'
        merch_dict = self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['merchandise']['merchandiseLines'][0]
        shipping_data = {
            "query": "query Proposal($delivery:DeliveryTermsInput,$discounts:DiscountTermsInput,$payment:PaymentTermInput,$merchandise:MerchandiseTermInput,$buyerIdentity:BuyerIdentityTermInput,$taxes:TaxTermInput,$sessionInput:SessionTokenInput!,$checkpointData:String,$queueToken:String,$reduction:ReductionInput,$changesetTokens:[String!],$tip:TipTermInput,$note:NoteInput,$localizationExtension:LocalizationExtensionInput,$nonNegotiableTerms:NonNegotiableTermsInput,$scriptFingerprint:ScriptFingerprintInput,$transformerFingerprintV2:String,$optionalDuties:OptionalDutiesInput,$attribution:AttributionInput,$captcha:CaptchaInput,$poNumber:String,$saleAttributions:SaleAttributionsInput){session(sessionInput:$sessionInput){negotiate(input:{purchaseProposal:{delivery:$delivery,discounts:$discounts,payment:$payment,merchandise:$merchandise,buyerIdentity:$buyerIdentity,taxes:$taxes,reduction:$reduction,tip:$tip,note:$note,poNumber:$poNumber,nonNegotiableTerms:$nonNegotiableTerms,localizationExtension:$localizationExtension,scriptFingerprint:$scriptFingerprint,transformerFingerprintV2:$transformerFingerprintV2,optionalDuties:$optionalDuties,attribution:$attribution,captcha:$captcha,saleAttributions:$saleAttributions},checkpointData:$checkpointData,queueToken:$queueToken,changesetTokens:$changesetTokens}){__typename result{...on NegotiationResultAvailable{queueToken buyerProposal{...BuyerProposalDetails __typename}sellerProposal{...ProposalDetails __typename}__typename}...on CheckpointDenied{redirectUrl __typename}...on Throttled{pollAfter queueToken pollUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}...on NegotiationResultFailed{__typename}__typename}errors{code localizedMessage nonLocalizedMessage localizedMessageHtml...on RemoveTermViolation{target __typename}...on AcceptNewTermViolation{target __typename}...on ConfirmChangeViolation{from to __typename}...on UnprocessableTermViolation{target __typename}...on UnresolvableTermViolation{target __typename}...on GenericError{__typename}__typename}}__typename}}fragment BuyerProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...ProposalDeliveryFragment __typename}merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponents{...MerchandiseBundleLineComponent __typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}attribution{attributions{...on AttributionItem{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}__typename}fragment ProposalDiscountFragment on DiscountTermsV2{__typename...on FilledDiscountTerms{lines{...DiscountLineDetailsFragment __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment DiscountLineDetailsFragment on DiscountLine{allocations{...on DiscountAllocatedAllocationSet{__typename allocations{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}target{index targetType stableId __typename}__typename}}__typename}discount{...DiscountDetailsFragment __typename}lineAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}fragment DiscountDetailsFragment on Discount{...on CustomDiscount{title presentationLevel signature signatureUuid type value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on CodeDiscount{title code presentationLevel __typename}...on DiscountCodeTrigger{code __typename}...on AutomaticDiscount{presentationLevel title __typename}__typename}fragment ProposalDeliveryFragment on DeliveryTerms{__typename...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken deliveryLines{destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}__typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}...on DeliveryStrategyReference{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{title handle custom description acceptsInstructions phoneRequired methodType carrierName brandedPromise{logoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name __typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment FilledMerchandiseLineTargetCollectionFragment on FilledMerchandiseLineTargetCollection{linesV2{...on MerchandiseLine{stableId merchandise{...MerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on MerchandiseBundleLineComponent{stableId merchandise{...MerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}fragment MerchandiseFragment on ProposalMerchandise{...SourceProvidedMerchandise...on ProductVariantMerchandise{id digest variantId title subtitle requiresShipping properties{...MerchandiseProperties __typename}__typename}...on ContextualizedProductVariantMerchandise{id digest variantId title subtitle requiresShipping sellingPlan{id digest name prepaid deliveriesPerBillingCycle subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}properties{...MerchandiseProperties __typename}__typename}...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}fragment SourceProvidedMerchandise on Merchandise{...on SourceProvidedMerchandise{__typename product{id title productType vendor __typename}digest variantId optionalIdentifier title untranslatedTitle subtitle untranslatedSubtitle taxable giftCard requiresShipping price{amount currencyCode __typename}deferredAmount{amount currencyCode __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}options{name value __typename}properties{...MerchandiseProperties __typename}taxCode taxesIncluded weight{value unit __typename}sku}__typename}fragment MerchandiseProperties on MerchandiseProperty{name value{...on MerchandisePropertyValueString{string:value __typename}...on MerchandisePropertyValueInt{int:value __typename}...on MerchandisePropertyValueFloat{float:value __typename}...on MerchandisePropertyValueBoolean{boolean:value __typename}...on MerchandisePropertyValueJson{json:value __typename}__typename}visible __typename}fragment ProductVariantMerchandiseDetails on ProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle product{id vendor productType __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{id subscriptionDetails{billingInterval __typename}__typename}giftCard __typename}fragment ContextualizedProductVariantMerchandiseDetails on ContextualizedProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle sku price{amount currencyCode __typename}product{id vendor productType __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}giftCard deferredAmount{amount currencyCode __typename}__typename}fragment LineAllocationDetails on LineAllocation{stableId quantity totalAmountBeforeReductions{amount currencyCode __typename}totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}unitPrice{price{amount currencyCode __typename}measurement{referenceUnit referenceValue __typename}__typename}allocations{...on LineComponentDiscountAllocation{allocation{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}__typename}__typename}__typename}fragment MerchandiseBundleLineComponent on MerchandiseBundleLineComponent{__typename stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}}fragment ProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken deliveryLines{destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}__typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{originLocation{id __typename}title handle custom description acceptsInstructions phoneRequired methodType carrierName brandedPromise{logoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromiseProviderApiClientId deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name distanceFromBuyer{unit value __typename}__typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}payment{...on FilledPaymentTerms{availablePayments{paymentMethod{...on AnyDirectPaymentMethod{__typename availablePaymentProviders{paymentMethodIdentifier name brands orderingIndex displayName availablePresentmentCurrencies __typename}}...on AnyOffsitePaymentMethod{__typename availableOffsiteProviders{__typename paymentMethodIdentifier name paymentBrands orderingIndex showRedirectionNotice availablePresentmentCurrencies}}...on AnyCustomOnsitePaymentMethod{__typename availableCustomOnsiteProviders{__typename paymentMethodIdentifier name paymentBrands orderingIndex availablePresentmentCurrencies}}...on DirectPaymentMethod{__typename paymentMethodIdentifier}...on GiftCardPaymentMethod{__typename}...on AnyRedeemablePaymentMethod{__typename availableRedemptionSources orderingIndex}...on WalletsPlatformConfiguration{name configurationParams __typename}...on AnyWalletPaymentMethod{availableWalletPaymentConfigs{...on PaypalWalletConfig{__typename name clientId merchantId venmoEnabled payflow paymentIntent paymentMethodIdentifier orderingIndex}...on ShopPayWalletConfig{__typename name storefrontUrl paymentMethodIdentifier orderingIndex}...on ShopifyInstallmentsWalletConfig{__typename name availableLoanTypes maxPrice{amount currencyCode __typename}minPrice{amount currencyCode __typename}supportedCountries supportedCurrencies giftCardsNotAllowed subscriptionItemsNotAllowed ineligibleTestModeCheckout ineligibleLineItem paymentMethodIdentifier orderingIndex}...on FacebookPayWalletConfig{__typename name partnerId partnerMerchantId supportedContainers acquirerCountryCode mode paymentMethodIdentifier orderingIndex}...on ApplePayWalletConfig{__typename name supportedNetworks walletAuthenticationToken walletOrderTypeIdentifier walletServiceUrl paymentMethodIdentifier orderingIndex}...on GooglePayWalletConfig{__typename name allowedAuthMethods allowedCardNetworks gateway gatewayMerchantId merchantId authJwt environment paymentMethodIdentifier orderingIndex}...on AmazonPayClassicWalletConfig{__typename name orderingIndex}__typename}__typename}...on LocalPaymentMethodConfig{__typename paymentMethodIdentifier name displayName additionalParameters{...on IdealBankSelectionParameterConfig{__typename label options{label value __typename}}__typename}orderingIndex}...on AnyPaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex displayName}...on PaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier}...on CustomPaymentMethod{id name additionalDetails paymentInstructions __typename}...on ManualPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex __typename}...on CustomPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on NoopPaymentMethod{__typename}...on GiftCardPaymentMethod{__typename}...on CustomerCreditCardPaymentMethod{__typename expired expiryMonth expiryYear name orderingIndex...CustomerCreditCardPaymentMethodFragment}...on PaypalBillingAgreementPaymentMethod{__typename orderingIndex paypalAccountEmail...PaypalBillingAgreementPaymentMethodFragment}__typename}__typename}paymentLines{...PaymentLines __typename}billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}paymentFlexibilityPaymentTermsTemplate{id translatedName dueDate dueInDays __typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}poNumber merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponents{...MerchandiseBundleLineComponent __typename}__typename}__typename}__typename}note{customAttributes{key value __typename}message __typename}scriptFingerprint{signature signatureUuid lineItemScriptChanges paymentScriptChanges shippingScriptChanges __typename}transformerFingerprintV2 buyerIdentity{...on FilledBuyerIdentityTerms{buyerIdentity{...on GuestProfile{presentmentCurrency countryCode market{id handle __typename}__typename}...on CustomerProfile{id presentmentCurrency fullName firstName lastName countryCode email imageUrl acceptsMarketing phone billingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}shippingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}storeCreditAccounts{id balance{amount currencyCode __typename}__typename}__typename}...on BusinessCustomerProfile{checkoutExperienceConfiguration{availablePaymentOptions checkoutCompletionTarget editableShippingAddress __typename}id presentmentCurrency fullName firstName lastName acceptsMarketing companyName countryCode email phone selectedCompanyLocation{id name __typename}locationCount billingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}shippingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}__typename}contactInfoV2{...on EmailFormContents{email __typename}...on SMSFormContents{phoneNumber __typename}__typename}marketingConsent{...on SMSMarketingConsent{value __typename}...on EmailMarketingConsent{value __typename}__typename}shopPayOptInPhone __typename}__typename}recurringTotals{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}duty{...on FilledDutyTerms{totalDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}exemptions{taxExemptionReason targets{...on TargetAllLines{__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tip{tipSuggestions{...on TipSuggestion{__typename percentage amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}}__typename}terms{...on FilledTipTerms{tipLines{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}localizationExtension{...on LocalizationExtension{fields{...on LocalizationExtensionField{key title value __typename}__typename}__typename}__typename}landedCostDetails{incotermInformation{incoterm reason __typename}__typename}nonNegotiableTerms{signature contents{signature targetTerms targetLine{allLines index __typename}attributes __typename}__typename}optionalDuties{buyerRefusesDuties refuseDutiesPermitted __typename}attribution{attributions{...on AttributionItem{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}managedByMarketsPro captcha{...on Captcha{provider challenge sitekey token __typename}...on PendingTerms{taskId pollDelay __typename}__typename}__typename}fragment CustomerCreditCardPaymentMethodFragment on CustomerCreditCardPaymentMethod{cvvSessionId paymentMethodIdentifier token displayLastDigits brand billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaypalBillingAgreementPaymentMethodFragment on PaypalBillingAgreementPaymentMethod{paymentMethodIdentifier token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaymentLines on PaymentLine{specialInstructions amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier creditCard{...on CreditCard{brand lastDigits __typename}__typename}__typename}...on GiftCardPaymentMethod{code balance{amount currencyCode __typename}__typename}...on RedeemablePaymentMethod{redemptionSource redemptionContent{...on ShopCashRedemptionContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}__typename}redemptionId destinationAmount{amount currencyCode __typename}sourceAmount{amount currencyCode __typename}__typename}__typename}__typename}...on WalletsPlatformPaymentMethod{name walletParams __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{paypalBillingAddress:billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token paymentMethodIdentifier acceptedSubscriptionTerms expiresAt __typename}...on ApplePayWalletContent{data signature version lastDigits paymentMethodIdentifier __typename}...on GooglePayWalletContent{signature signedMessage protocolVersion paymentMethodIdentifier __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode paymentMethodIdentifier __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken paymentMethodIdentifier __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name additionalParameters{...on IdealPaymentMethodParameters{bank __typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on OffsitePaymentMethod{paymentMethodIdentifier name __typename}...on CustomPaymentMethod{id name additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on CustomOnsitePaymentMethod{paymentMethodIdentifier name encryptedAttributes __typename}...on ManualPaymentMethod{id name paymentMethodIdentifier __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on CustomerCreditCardPaymentMethod{...CustomerCreditCardPaymentMethodFragment __typename}...on PaypalBillingAgreementPaymentMethod{...PaypalBillingAgreementPaymentMethodFragment __typename}...on NoopPaymentMethod{__typename}__typename}__typename}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token classicThankYouPageUrl poNumber orderIdentity{buyerIdentifier id __typename}shopPayArtifact{optIn{vaultPhone __typename}__typename}eligibleForMarketingOptIn purchaseOrder{...ReceiptPurchaseOrder __typename}orderCreationStatus{__typename}paymentDetails{creditCardBrand creditCardLastFourDigits __typename}shopAppLinksAndResources{mobileUrl qrCodeUrl canTrackOrderUpdates shopInstallmentsViewSchedules shopInstallmentsMobileUrl installmentsHighlightEligible mobileUrlAttributionPayload shopAppEligible shopAppQrCodeKillswitch shopPayOrder buyerHasShopApp buyerHasShopPay orderUpdateOptions __typename}postPurchasePageRequested postPurchaseVaultedPaymentMethodStatus __typename}...on ProcessingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}__typename}...on FailedReceipt{id processingError{...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on PaymentFailed{code messageUntranslated __typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}fragment ReceiptPurchaseOrder on PurchaseOrder{__typename sessionToken totalAmountToPay{amount currencyCode __typename}delivery{...on PurchaseOrderDeliveryTerms{deliveryLines{__typename deliveryStrategy{handle title description methodType pickupLocation{...on PickupInStoreLocation{name address{address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}instructions __typename}__typename}__typename}lineAmount{amount currencyCode __typename}destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}__typename}groupType}__typename}__typename}payment{...on PurchaseOrderPaymentTerms{billingAddress{__typename...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}}paymentLines{amount{amount currencyCode __typename}postPaymentMessage dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier vaultingAgreement creditCard{brand lastDigits __typename}billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomerCreditCardPaymentMethod{brand displayLastDigits token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on PurchaseOrderGiftCardPaymentMethod{code __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token expiresAt __typename}...on ApplePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}data signature version __typename}...on GooglePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}signature signedMessage protocolVersion __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on OffsitePaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on ManualPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on PaypalBillingAgreementPaymentMethod{token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}buyerIdentity{...on PurchaseOrderBuyerIdentityTerms{contactMethod{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}marketingConsent{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}__typename}__typename}merchandise{merchandiseLines{stableId merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}tax{totalTaxAmount{amount currencyCode __typename}__typename}discounts{lines{deliveryAllocations{amount{amount currencyCode __typename}index __typename}__typename}__typename}}fragment ProductVariantSnapshotMerchandiseDetails on ProductVariantSnapshot{variantId options{name value __typename}productTitle title sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}__typename}",
            'variables': {
                "checkpointData": None,
                'sessionInput': {
                    'sessionToken': self.session_token
                },
                'queueToken': self.queue_token,
                'discounts': {
                    'lines': [],
                    'acceptUnexpectedDiscounts': True
                },
                'delivery': {
                    'deliveryLines': [
                        {
                            'destination': {
                                'partialStreetAddress': {
                                    'address1': profile['shipping_a1'],
                                    'address2': profile['shipping_a2'],
                                    "city": profile['shipping_city'],
                                    "countryCode": get_country_code(profile['shipping_country']),
                                    "postalCode": profile['shipping_zipcode'],
                                    "firstName": profile['shipping_fname'],
                                    "lastName": profile['shipping_lname'],
                                    "zoneCode": profile['shipping_state'],
                                    "phone": self.format_phone2(profile['shipping_phone'])
                                }
                            },
                            "selectedDeliveryStrategy": {
                                'deliveryStrategyByHandle': {
                                    'handle': self.delivery_json['handle'],
                                    'customDeliveryRate': self.delivery_json['custom']
                                },
                                "options": {
                                    "phone": self.format_phone2(profile['shipping_phone'])
                                }
                            },
                            "targetMerchandiseLines": {
                                "lines": [
                                    {
                                        'atIndex': 0
                                    }
                                ]
                            },
                            "deliveryMethodTypes": [
                                "SHIPPING"
                            ],
                            "expectedTotalPrice": {
                                'value': {
                                    'amount': self.delivery_json['amount']['value']['amount'],
                                    'currencyCode': self.delivery_json['amount']['value']['currencyCode']
                                }
                            },
                            "destinationChanged": True
                        }
                    ],
                    "noDeliveryRequired": [],
                    "useProgressiveRates": True,
                    "prefetchShippingRatesStrategy": None,
                    "interfaceFlow": "SHOPIFY"
                },
                "merchandise": {
                    "merchandiseLines": [
                        {
                            "stableId": merch_dict['stableId'],
                            "merchandise": {
                                "productVariantReference": {
                                    "id": merch_dict['merchandise']['id'],
                                    "variantId": merch_dict['merchandise']['variantId'],
                                    "properties": [],
                                    "sellingPlanId": None,
                                    "sellingPlanDigest": None
                                }
                            },
                            "quantity": {
                                "items": {
                                    "value": merch_dict['quantity']['items']['value']
                                }
                            },
                            "expectedTotalPrice": {
                                "value": {
                                    "amount": merch_dict['totalAmount']['value']['amount'],
                                    "currencyCode": merch_dict['totalAmount']['value']['currencyCode']
                                }
                            },
                            "lineComponents": []
                        }
                    ]
                },
                "payment": {
                    "totalAmount": {
                        "any": True
                    },
                    "paymentLines": [],
                    "billingAddress": {
                        "streetAddress": {
                            'address1': profile['billing_a1'],
                            'address2': profile['billing_a2'],
                            "city": profile['billing_city'],
                            "countryCode": get_country_code(profile['billing_country']),
                            "postalCode": profile['billing_zipcode'],
                            "firstName": profile['billing_fname'],
                            "lastName": profile['billing_lname'],
                            "zoneCode": profile['billing_state'],
                            "phone": self.format_phone2(profile['billing_phone'])
                        }
                    }
                },
                "buyerIdentity": {
                    "buyerIdentity": {
                        "presentmentCurrency": self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['buyerIdentity']['buyerIdentity']['presentmentCurrency']
                    },
                    "contactInfoV2": {
                        "emailOrSms": {
                            "value": profile['shipping_email'],
                            "emailOrSmsChanged": False
                        }
                    },
                    "marketingConsent": [],
                    "shopPayOptInPhone": {
                        "number": self.format_phone2(profile['shipping_phone']),
                        "countryCode": get_country_code(profile['billing_country'])
                    }
                },
                "tip": {
                    "tipLines": []
                },
                "taxes": {
                    "proposedAllocations": None,
                    "proposedTotalAmount": {
                        "value": {
                            "amount": str(self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['tax'][
                                tax_key]['value']['amount']).replace('0.0', '0'),
                            "currencyCode": self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['tax'][
                                tax_key]['value']['currencyCode']
                        }
                    },
                    "proposedTotalIncludedAmount": None,
                    "proposedMixedStateTotalAmount": None,
                    "proposedExemptions": []
                },
                "note": {
                    "message": None,
                    "customAttributes": []
                },
                "localizationExtension": {
                    "fields": []
                },
                "nonNegotiableTerms": None,
                "optionalDuties": {
                    "buyerRefusesDuties": False
                }
            },
            "operationName": "Proposal"
        }

        return shipping_data

    def new_pay(self, payment):
        profile = self.profile
        merch_dict = self.latest_response_graphql['data']['session']['negotiate']['result']['sellerProposal']['merchandise']['merchandiseLines'][0]
        shipping_data = {
            "query": "mutation SubmitForCompletion($input:NegotiationInput!,$attemptToken:String!,$metafields:[MetafieldInput!],$postPurchaseInquiryResult:PostPurchaseInquiryResultCode){submitForCompletion(input:$input attemptToken:$attemptToken metafields:$metafields postPurchaseInquiryResult:$postPurchaseInquiryResult){...on SubmitSuccess{receipt{...ReceiptDetails __typename}__typename}...on SubmitAlreadyAccepted{receipt{...ReceiptDetails __typename}__typename}...on SubmitFailed{reason __typename}...on SubmitRejected{buyerProposal{...BuyerProposalDetails __typename}sellerProposal{...ProposalDetails __typename}errors{...on NegotiationError{code localizedMessage nonLocalizedMessage localizedMessageHtml...on RemoveTermViolation{message{code localizedDescription __typename}target __typename}...on AcceptNewTermViolation{message{code localizedDescription __typename}target __typename}...on ConfirmChangeViolation{message{code localizedDescription __typename}from to __typename}...on UnprocessableTermViolation{message{code localizedDescription __typename}target __typename}...on UnresolvableTermViolation{message{code localizedDescription __typename}target __typename}...on InputValidationError{field __typename}__typename}__typename}__typename}...on Throttled{pollAfter pollUrl queueToken buyerProposal{...BuyerProposalDetails __typename}__typename}...on CheckpointDenied{redirectUrl __typename}...on SubmittedForCompletion{receipt{...ReceiptDetails __typename}__typename}__typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token classicThankYouPageUrl poNumber orderIdentity{buyerIdentifier id __typename}shopPayArtifact{optIn{vaultPhone __typename}__typename}eligibleForMarketingOptIn purchaseOrder{...ReceiptPurchaseOrder __typename}orderCreationStatus{__typename}paymentDetails{creditCardBrand creditCardLastFourDigits __typename}shopAppLinksAndResources{mobileUrl qrCodeUrl canTrackOrderUpdates shopInstallmentsViewSchedules shopInstallmentsMobileUrl installmentsHighlightEligible mobileUrlAttributionPayload shopAppEligible shopAppQrCodeKillswitch shopPayOrder buyerHasShopApp buyerHasShopPay orderUpdateOptions __typename}postPurchasePageRequested postPurchaseVaultedPaymentMethodStatus __typename}...on ProcessingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}__typename}...on FailedReceipt{id processingError{...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on PaymentFailed{code messageUntranslated __typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}fragment ReceiptPurchaseOrder on PurchaseOrder{__typename sessionToken totalAmountToPay{amount currencyCode __typename}delivery{...on PurchaseOrderDeliveryTerms{deliveryLines{__typename deliveryStrategy{handle title description methodType pickupLocation{...on PickupInStoreLocation{name address{address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}instructions __typename}__typename}__typename}lineAmount{amount currencyCode __typename}destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}__typename}groupType}__typename}__typename}payment{...on PurchaseOrderPaymentTerms{billingAddress{__typename...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}}paymentLines{amount{amount currencyCode __typename}postPaymentMessage dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier vaultingAgreement creditCard{brand lastDigits __typename}billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomerCreditCardPaymentMethod{brand displayLastDigits token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on PurchaseOrderGiftCardPaymentMethod{code __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token expiresAt __typename}...on ApplePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}data signature version __typename}...on GooglePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}signature signedMessage protocolVersion __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on OffsitePaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on ManualPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on PaypalBillingAgreementPaymentMethod{token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}buyerIdentity{...on PurchaseOrderBuyerIdentityTerms{contactMethod{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}marketingConsent{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}__typename}__typename}merchandise{merchandiseLines{stableId merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}tax{totalTaxAmount{amount currencyCode __typename}__typename}discounts{lines{deliveryAllocations{amount{amount currencyCode __typename}index __typename}__typename}__typename}}fragment ProductVariantSnapshotMerchandiseDetails on ProductVariantSnapshot{variantId options{name value __typename}productTitle title sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}__typename}fragment BuyerProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...ProposalDeliveryFragment __typename}merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponents{...MerchandiseBundleLineComponent __typename}__typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}attribution{attributions{...on AttributionItem{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}__typename}fragment ProposalDiscountFragment on DiscountTermsV2{__typename...on FilledDiscountTerms{lines{...DiscountLineDetailsFragment __typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment DiscountLineDetailsFragment on DiscountLine{allocations{...on DiscountAllocatedAllocationSet{__typename allocations{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}target{index targetType stableId __typename}__typename}}__typename}discount{...DiscountDetailsFragment __typename}lineAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}fragment DiscountDetailsFragment on Discount{...on CustomDiscount{title presentationLevel signature signatureUuid type value{...on PercentageValue{percentage __typename}...on FixedAmountValue{appliesOnEachItem fixedAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}...on CodeDiscount{title code presentationLevel __typename}...on DiscountCodeTrigger{code __typename}...on AutomaticDiscount{presentationLevel title __typename}__typename}fragment ProposalDeliveryFragment on DeliveryTerms{__typename...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken deliveryLines{destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}__typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}...on DeliveryStrategyReference{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{title handle custom description acceptsInstructions phoneRequired methodType carrierName brandedPromise{logoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name __typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}}fragment FilledMerchandiseLineTargetCollectionFragment on FilledMerchandiseLineTargetCollection{linesV2{...on MerchandiseLine{stableId merchandise{...MerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on MerchandiseBundleLineComponent{stableId merchandise{...MerchandiseFragment __typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}fragment MerchandiseFragment on ProposalMerchandise{...SourceProvidedMerchandise...on ProductVariantMerchandise{id digest variantId title subtitle requiresShipping properties{...MerchandiseProperties __typename}__typename}...on ContextualizedProductVariantMerchandise{id digest variantId title subtitle requiresShipping sellingPlan{id digest name prepaid deliveriesPerBillingCycle subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}properties{...MerchandiseProperties __typename}__typename}...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}fragment SourceProvidedMerchandise on Merchandise{...on SourceProvidedMerchandise{__typename product{id title productType vendor __typename}digest variantId optionalIdentifier title untranslatedTitle subtitle untranslatedSubtitle taxable giftCard requiresShipping price{amount currencyCode __typename}deferredAmount{amount currencyCode __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}options{name value __typename}properties{...MerchandiseProperties __typename}taxCode taxesIncluded weight{value unit __typename}sku}__typename}fragment MerchandiseProperties on MerchandiseProperty{name value{...on MerchandisePropertyValueString{string:value __typename}...on MerchandisePropertyValueInt{int:value __typename}...on MerchandisePropertyValueFloat{float:value __typename}...on MerchandisePropertyValueBoolean{boolean:value __typename}...on MerchandisePropertyValueJson{json:value __typename}__typename}visible __typename}fragment ProductVariantMerchandiseDetails on ProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle product{id vendor productType __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{id subscriptionDetails{billingInterval __typename}__typename}giftCard __typename}fragment ContextualizedProductVariantMerchandiseDetails on ContextualizedProductVariantMerchandise{id digest variantId title untranslatedTitle subtitle untranslatedSubtitle sku price{amount currencyCode __typename}product{id vendor productType __typename}image{altText one:transformedSrc(maxWidth:64,maxHeight:64)two:transformedSrc(maxWidth:128,maxHeight:128)four:transformedSrc(maxWidth:256,maxHeight:256)__typename}properties{...MerchandiseProperties __typename}requiresShipping options{name value __typename}sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}giftCard deferredAmount{amount currencyCode __typename}__typename}fragment LineAllocationDetails on LineAllocation{stableId quantity totalAmountBeforeReductions{amount currencyCode __typename}totalAmountAfterDiscounts{amount currencyCode __typename}totalAmountAfterLineDiscounts{amount currencyCode __typename}checkoutPriceAfterDiscounts{amount currencyCode __typename}checkoutPriceBeforeReductions{amount currencyCode __typename}unitPrice{price{amount currencyCode __typename}measurement{referenceUnit referenceValue __typename}__typename}allocations{...on LineComponentDiscountAllocation{allocation{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}amount{amount currencyCode __typename}discount{...DiscountDetailsFragment __typename}__typename}__typename}__typename}fragment MerchandiseBundleLineComponent on MerchandiseBundleLineComponent{__typename stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}}fragment ProposalDetails on Proposal{merchandiseDiscount{...ProposalDiscountFragment __typename}deliveryDiscount{...ProposalDiscountFragment __typename}delivery{...on FilledDeliveryTerms{intermediateRates progressiveRatesEstimatedTimeUntilCompletion shippingRatesStatusToken deliveryLines{destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on Geolocation{country{code __typename}zone{code __typename}coordinates{latitude longitude __typename}__typename}...on PartialStreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}__typename}targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}groupType selectedDeliveryStrategy{...on CompleteDeliveryStrategy{handle __typename}__typename}availableDeliveryStrategies{...on CompleteDeliveryStrategy{originLocation{id __typename}title handle custom description acceptsInstructions phoneRequired methodType carrierName brandedPromise{logoUrl name __typename}deliveryStrategyBreakdown{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}discountRecurringCycleLimit excludeFromDeliveryOptionPrice targetMerchandise{...FilledMerchandiseLineTargetCollectionFragment __typename}__typename}minDeliveryDateTime maxDeliveryDateTime deliveryPromiseProviderApiClientId deliveryPromisePresentmentTitle{short long __typename}displayCheckoutRedesign estimatedTimeInTransit{...on IntIntervalConstraint{lowerBound upperBound __typename}...on IntValueConstraint{value __typename}__typename}amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}amountAfterDiscounts{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}pickupLocation{...on PickupInStoreLocation{address{address1 address2 city countryCode phone postalCode zoneCode __typename}instructions name distanceFromBuyer{unit value __typename}__typename}...on PickupPointLocation{address{address1 address2 address3 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}__typename}businessHours{day openingTime closingTime __typename}carrierCode carrierName handle kind name __typename}__typename}__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay taskId __typename}...on UnavailableTerms{__typename}__typename}payment{...on FilledPaymentTerms{availablePayments{paymentMethod{...on AnyDirectPaymentMethod{__typename availablePaymentProviders{paymentMethodIdentifier name brands orderingIndex displayName availablePresentmentCurrencies __typename}}...on AnyOffsitePaymentMethod{__typename availableOffsiteProviders{__typename paymentMethodIdentifier name paymentBrands orderingIndex showRedirectionNotice availablePresentmentCurrencies}}...on AnyCustomOnsitePaymentMethod{__typename availableCustomOnsiteProviders{__typename paymentMethodIdentifier name paymentBrands orderingIndex availablePresentmentCurrencies}}...on DirectPaymentMethod{__typename paymentMethodIdentifier}...on GiftCardPaymentMethod{__typename}...on AnyRedeemablePaymentMethod{__typename availableRedemptionSources orderingIndex}...on WalletsPlatformConfiguration{name configurationParams __typename}...on AnyWalletPaymentMethod{availableWalletPaymentConfigs{...on PaypalWalletConfig{__typename name clientId merchantId venmoEnabled payflow paymentIntent paymentMethodIdentifier orderingIndex}...on ShopPayWalletConfig{__typename name storefrontUrl paymentMethodIdentifier orderingIndex}...on ShopifyInstallmentsWalletConfig{__typename name availableLoanTypes maxPrice{amount currencyCode __typename}minPrice{amount currencyCode __typename}supportedCountries supportedCurrencies giftCardsNotAllowed subscriptionItemsNotAllowed ineligibleTestModeCheckout ineligibleLineItem paymentMethodIdentifier orderingIndex}...on FacebookPayWalletConfig{__typename name partnerId partnerMerchantId supportedContainers acquirerCountryCode mode paymentMethodIdentifier orderingIndex}...on ApplePayWalletConfig{__typename name supportedNetworks walletAuthenticationToken walletOrderTypeIdentifier walletServiceUrl paymentMethodIdentifier orderingIndex}...on GooglePayWalletConfig{__typename name allowedAuthMethods allowedCardNetworks gateway gatewayMerchantId merchantId authJwt environment paymentMethodIdentifier orderingIndex}...on AmazonPayClassicWalletConfig{__typename name orderingIndex}__typename}__typename}...on LocalPaymentMethodConfig{__typename paymentMethodIdentifier name displayName additionalParameters{...on IdealBankSelectionParameterConfig{__typename label options{label value __typename}}__typename}orderingIndex}...on AnyPaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex displayName}...on PaymentOnDeliveryMethod{__typename additionalDetails paymentInstructions paymentMethodIdentifier}...on CustomPaymentMethod{id name additionalDetails paymentInstructions __typename}...on ManualPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex __typename}...on CustomPaymentMethodConfig{id name additionalDetails paymentInstructions paymentMethodIdentifier orderingIndex __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on NoopPaymentMethod{__typename}...on GiftCardPaymentMethod{__typename}...on CustomerCreditCardPaymentMethod{__typename expired expiryMonth expiryYear name orderingIndex...CustomerCreditCardPaymentMethodFragment}...on PaypalBillingAgreementPaymentMethod{__typename orderingIndex paypalAccountEmail...PaypalBillingAgreementPaymentMethodFragment}__typename}__typename}paymentLines{...PaymentLines __typename}billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}paymentFlexibilityPaymentTermsTemplate{id translatedName dueDate dueInDays __typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}poNumber merchandise{...on FilledMerchandiseTerms{taxesIncluded merchandiseLines{stableId merchandise{...SourceProvidedMerchandise...ProductVariantMerchandiseDetails...ContextualizedProductVariantMerchandiseDetails...on MissingProductVariantMerchandise{id digest variantId __typename}__typename}quantity{...on ProposalMerchandiseQuantityByItem{items{...on IntValueConstraint{value __typename}__typename}__typename}__typename}totalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}recurringTotal{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}lineAllocations{...LineAllocationDetails __typename}lineComponents{...MerchandiseBundleLineComponent __typename}__typename}__typename}__typename}note{customAttributes{key value __typename}message __typename}scriptFingerprint{signature signatureUuid lineItemScriptChanges paymentScriptChanges shippingScriptChanges __typename}transformerFingerprintV2 buyerIdentity{...on FilledBuyerIdentityTerms{buyerIdentity{...on GuestProfile{presentmentCurrency countryCode market{id handle __typename}__typename}...on CustomerProfile{id presentmentCurrency fullName firstName lastName countryCode email imageUrl acceptsMarketing phone billingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}shippingAddresses{id default address{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}storeCreditAccounts{id balance{amount currencyCode __typename}__typename}__typename}...on BusinessCustomerProfile{checkoutExperienceConfiguration{availablePaymentOptions checkoutCompletionTarget editableShippingAddress __typename}id presentmentCurrency fullName firstName lastName acceptsMarketing companyName countryCode email phone selectedCompanyLocation{id name __typename}locationCount billingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}shippingAddress{firstName lastName address1 address2 phone postalCode city company zoneCode countryCode label __typename}__typename}__typename}contactInfoV2{...on EmailFormContents{email __typename}...on SMSFormContents{phoneNumber __typename}__typename}marketingConsent{...on SMSMarketingConsent{value __typename}...on EmailMarketingConsent{value __typename}__typename}shopPayOptInPhone __typename}__typename}recurringTotals{title interval intervalCount recurringPrice{amount currencyCode __typename}fixedPrice{amount currencyCode __typename}fixedPriceCount __typename}subtotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}runningTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}total{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalBeforeTaxesAndShipping{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotalTaxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}checkoutTotal{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}deferredTotal{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}subtotalAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}taxes{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt __typename}hasOnlyDeferredShipping subtotalBeforeReductions{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}duty{...on FilledDutyTerms{totalDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tax{...on FilledTaxTerms{totalTaxAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalTaxAndDutyAmount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}totalAmountIncludedInTarget{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}exemptions{taxExemptionReason targets{...on TargetAllLines{__typename}__typename}__typename}__typename}...on PendingTerms{pollDelay __typename}...on UnavailableTerms{__typename}__typename}tip{tipSuggestions{...on TipSuggestion{__typename percentage amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}}__typename}terms{...on FilledTipTerms{tipLines{amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}localizationExtension{...on LocalizationExtension{fields{...on LocalizationExtensionField{key title value __typename}__typename}__typename}__typename}landedCostDetails{incotermInformation{incoterm reason __typename}__typename}nonNegotiableTerms{signature contents{signature targetTerms targetLine{allLines index __typename}attributes __typename}__typename}optionalDuties{buyerRefusesDuties refuseDutiesPermitted __typename}attribution{attributions{...on AttributionItem{...on RetailAttributions{deviceId locationId userId __typename}...on DraftOrderAttributions{userIdentifier:userId sourceName locationIdentifier:locationId __typename}__typename}__typename}__typename}saleAttributions{attributions{...on SaleAttribution{recipient{...on StaffMember{id __typename}...on Location{id __typename}...on PointOfSaleDevice{id __typename}__typename}targetMerchandiseLines{...FilledMerchandiseLineTargetCollectionFragment...on AnyMerchandiseLineTargetCollection{any __typename}__typename}__typename}__typename}__typename}managedByMarketsPro captcha{...on Captcha{provider challenge sitekey token __typename}...on PendingTerms{taskId pollDelay __typename}__typename}__typename}fragment CustomerCreditCardPaymentMethodFragment on CustomerCreditCardPaymentMethod{cvvSessionId paymentMethodIdentifier token displayLastDigits brand billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaypalBillingAgreementPaymentMethodFragment on PaypalBillingAgreementPaymentMethod{paymentMethodIdentifier token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}fragment PaymentLines on PaymentLine{specialInstructions amount{...on MoneyValueConstraint{value{amount currencyCode __typename}__typename}__typename}dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier creditCard{...on CreditCard{brand lastDigits __typename}__typename}__typename}...on GiftCardPaymentMethod{code balance{amount currencyCode __typename}__typename}...on RedeemablePaymentMethod{redemptionSource redemptionContent{...on ShopCashRedemptionContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}__typename}redemptionId destinationAmount{amount currencyCode __typename}sourceAmount{amount currencyCode __typename}__typename}__typename}__typename}...on WalletsPlatformPaymentMethod{name walletParams __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{paypalBillingAddress:billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token paymentMethodIdentifier acceptedSubscriptionTerms expiresAt __typename}...on ApplePayWalletContent{data signature version lastDigits paymentMethodIdentifier __typename}...on GooglePayWalletContent{signature signedMessage protocolVersion paymentMethodIdentifier __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode paymentMethodIdentifier __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken paymentMethodIdentifier __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name additionalParameters{...on IdealPaymentMethodParameters{bank __typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on OffsitePaymentMethod{paymentMethodIdentifier name __typename}...on CustomPaymentMethod{id name additionalDetails paymentInstructions paymentMethodIdentifier __typename}...on CustomOnsitePaymentMethod{paymentMethodIdentifier name encryptedAttributes __typename}...on ManualPaymentMethod{id name paymentMethodIdentifier __typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on CustomerCreditCardPaymentMethod{...CustomerCreditCardPaymentMethodFragment __typename}...on PaypalBillingAgreementPaymentMethod{...PaypalBillingAgreementPaymentMethodFragment __typename}...on NoopPaymentMethod{__typename}__typename}__typename}",
            "operationName": "SubmitForCompletion",
            'variables': {
                'input': {
                    "checkpointData": None,
                    'sessionInput': {
                        'sessionToken': self.session_token
                    },
                    'queueToken': self.queue_token,
                    'discounts': {
                        'lines': [],
                        'acceptUnexpectedDiscounts': True
                    },
                    'delivery': {
                        'deliveryLines': [
                            {
                                'destination': {
                                    'streetAddress': {
                                        'address1': profile['shipping_a1'],
                                        'address2': profile['shipping_a2'],
                                        "city": profile['shipping_city'],
                                        "countryCode": get_country_code(profile['shipping_country']),
                                        "postalCode": profile['shipping_zipcode'],
                                        "firstName": profile['shipping_fname'],
                                        "lastName": profile['shipping_lname'],
                                        "zoneCode": profile['shipping_state'],
                                        "phone": self.format_phone2(profile['shipping_phone'])
                                    }
                                },
                                "selectedDeliveryStrategy": {
                                    'deliveryStrategyByHandle': {
                                        'handle': self.delivery_json['handle'],
                                        'customDeliveryRate': self.delivery_json['custom']
                                    },
                                    "options": {
                                        "phone": self.format_phone2(profile['shipping_phone'])
                                    }
                                },
                                "targetMerchandiseLines": {
                                    "lines": [
                                        {
                                            'atIndex': 0
                                        }
                                    ]
                                },
                                "deliveryMethodTypes": [
                                    "SHIPPING"
                                ],
                                "expectedTotalPrice": {
                                    'value': {
                                        'amount': self.delivery_json['amount']['value']['amount'],
                                        'currencyCode': self.delivery_json['amount']['value']['currencyCode']
                                    }
                                },
                                "destinationChanged": True
                            }
                        ],
                        "noDeliveryRequired": [],
                        "useProgressiveRates": True,
                        "prefetchShippingRatesStrategy": None,
                        "interfaceFlow": "SHOPIFY"
                    },
                    "merchandise": {
                        "merchandiseLines": [
                            {
                                "stableId": merch_dict['stableId'],
                                "merchandise": {
                                    "productVariantReference": {
                                        "id": merch_dict['merchandise']['id'],
                                        "variantId": merch_dict['merchandise']['variantId'],
                                        "properties": [],
                                        "sellingPlanId": None,
                                        "sellingPlanDigest": None
                                    }
                                },
                                "quantity": {
                                    "items": {
                                        "value": merch_dict['quantity']['items']['value']
                                    }
                                },
                                "expectedTotalPrice": {
                                    "value": {
                                        "amount": merch_dict['totalAmount']['value']['amount'],
                                        "currencyCode": merch_dict['totalAmount']['value']['currencyCode']
                                    }
                                },
                                "lineComponents": []
                            }
                        ]
                    },
                    "payment": {
                        "totalAmount": {
                            "any": True
                        },
                        "paymentLines": [
                            {
                                "paymentMethod": {
                                    "directPaymentMethod": {
                                        "paymentMethodIdentifier": self.payment_id,
                                        "sessionId": payment,
                                        "billingAddress": {
                                            "streetAddress": {
                                                'address1': profile['billing_a1'],
                                                'address2': profile['billing_a2'],
                                                "city": profile['billing_city'],
                                                "countryCode": get_country_code(profile['billing_country']),
                                                "postalCode": profile['billing_zipcode'],
                                                "firstName": profile['billing_fname'],
                                                "lastName": profile['billing_lname'],
                                                "zoneCode": profile['billing_state'],
                                                "phone": self.format_phone2(profile['billing_phone'])
                                            }
                                        }
                                    },
                                    "giftCardPaymentMethod": None,
                                    "redeemablePaymentMethod": None,
                                    "walletPaymentMethod": None,
                                    "walletsPlatformPaymentMethod": None,
                                    "localPaymentMethod": None,
                                    "paymentOnDeliveryMethod": None,
                                    "paymentOnDeliveryMethod2": None,
                                    "manualPaymentMethod": None,
                                    "customPaymentMethod": None,
                                    "offsitePaymentMethod": None,
                                    "deferredPaymentMethod": None,
                                    "customerCreditCardPaymentMethod": None,
                                    "paypalBillingAgreementPaymentMethod": None
                                },
                                "amount": {
                                    "value": {
                                        "amount": self.checkout_total['amount'],
                                        "currencyCode": self.checkout_total['currencyCode']
                                    }
                                },
                                "dueAt": None
                            }
                        ],
                        "billingAddress": {
                            "streetAddress": {
                                'address1': profile['billing_a1'],
                                'address2': profile['billing_a2'],
                                "city": profile['billing_city'],
                                "countryCode": get_country_code(profile['billing_country']),
                                "postalCode": profile['billing_zipcode'],
                                "firstName": profile['billing_fname'],
                                "lastName": profile['billing_lname'],
                                "zoneCode": profile['billing_state'],
                                "phone": self.format_phone2(profile['billing_phone'])
                            }
                        }
                    },
                    "buyerIdentity": {
                        "buyerIdentity": {
                            "presentmentCurrency":
                                self.latest_response_graphql['data']['session']['negotiate']['result'][
                                    'sellerProposal']['buyerIdentity']['buyerIdentity']['presentmentCurrency'],
                            'countryCode': get_country_code(profile['shipping_country'])
                        },
                        "contactInfoV2": {
                            "emailOrSms": {
                                "value": profile['shipping_email'],
                                "emailOrSmsChanged": False
                            }
                        },
                        "marketingConsent": [],
                        "shopPayOptInPhone": {
                            "number": self.format_phone2(profile['shipping_phone']),
                            "countryCode": get_country_code(profile['billing_country'])
                        }
                    },
                    "tip": {
                        "tipLines": []
                    },
                    "taxes": {
                        "proposedAllocations": None,
                        "proposedTotalAmount": {
                            "value": {
                                "amount": self.tax_total['amount'],
                                "currencyCode": self.tax_total['currencyCode']
                            }
                        },
                        "proposedTotalIncludedAmount": None,
                        "proposedMixedStateTotalAmount": None,
                        "proposedExemptions": []
                    },
                    "note": {
                        "message": None,
                        "customAttributes": []
                    },
                    "localizationExtension": {
                        "fields": []
                    },
                    "nonNegotiableTerms": None,
                    "optionalDuties": {
                        "buyerRefusesDuties": False
                    },
            },
                "attemptToken": f"{self.cart_id}-{round(random.uniform(0, 1), 17)}",
                "metafields": []
            }
        }

        return shipping_data

    def new_poll(self):
        processing_poll = {
            "query": "query PollForReceipt($receiptId:ID!,$sessionToken:String!){receipt(receiptId:$receiptId,sessionInput:{sessionToken:$sessionToken}){...ReceiptDetails __typename}}fragment ReceiptDetails on Receipt{...on ProcessedReceipt{id token classicThankYouPageUrl orderIdentity{buyerIdentifier id __typename}shopPayArtifact{optIn{vaultPhone __typename}__typename}eligibleForMarketingOptIn purchaseOrder{...ReceiptPurchaseOrder __typename}orderCreationStatus{__typename}paymentDetails{creditCardBrand creditCardLastFourDigits __typename}shopAppLinksAndResources{mobileUrl qrCodeUrl canTrackOrderUpdates shopInstallmentsViewSchedules shopInstallmentsMobileUrl installmentsHighlightEligible mobileUrlAttributionPayload shopAppEligible shopAppQrCodeKillswitch shopPayOrder buyerHasShopApp buyerHasShopPay orderUpdateOptions __typename}postPurchasePageRequested postPurchaseVaultedPaymentMethodStatus __typename}...on ProcessingReceipt{id pollDelay __typename}...on ActionRequiredReceipt{id action{...on CompletePaymentChallenge{offsiteRedirect url __typename}__typename}__typename}...on FailedReceipt{id processingError{...on InventoryClaimFailure{__typename}...on InventoryReservationFailure{__typename}...on OrderCreationFailure{paymentsHaveBeenReverted __typename}...on OrderCreationSchedulingFailure{__typename}...on PaymentFailed{code messageUntranslated __typename}...on DiscountUsageLimitExceededFailure{__typename}...on CustomerPersistenceFailure{__typename}__typename}__typename}__typename}fragment ReceiptPurchaseOrder on PurchaseOrder{__typename sessionToken totalAmountToPay{amount currencyCode __typename}delivery{...on PurchaseOrderDeliveryTerms{deliveryLines{__typename deliveryStrategy{handle title description methodType pickupLocation{...on PickupInStoreLocation{name address{address1 address2 city countryCode zoneCode postalCode phone coordinates{latitude longitude __typename}__typename}instructions __typename}__typename}__typename}lineAmount{amount currencyCode __typename}destinationAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}__typename}groupType}__typename}__typename}payment{...on PurchaseOrderPaymentTerms{billingAddress{__typename...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}}paymentLines{amount{amount currencyCode __typename}postPaymentMessage dueAt paymentMethod{...on DirectPaymentMethod{sessionId paymentMethodIdentifier creditCard{brand lastDigits __typename}billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomerCreditCardPaymentMethod{brand displayLastDigits token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}...on PurchaseOrderGiftCardPaymentMethod{code __typename}...on WalletPaymentMethod{name walletContent{...on ShopPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}sessionToken paymentMethodIdentifier __typename}...on PaypalWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}email payerId token expiresAt __typename}...on ApplePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}data signature version __typename}...on GooglePayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}signature signedMessage protocolVersion __typename}...on FacebookPayWalletContent{billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}containerData containerId mode __typename}...on ShopifyInstallmentsWalletContent{autoPayEnabled billingAddress{...on StreetAddress{firstName lastName company address1 address2 city countryCode zoneCode postalCode phone __typename}...on InvalidBillingAddress{__typename}__typename}disclosureDetails{evidence id type __typename}installmentsToken sessionToken __typename}__typename}__typename}...on LocalPaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on PaymentOnDeliveryMethod{additionalDetails paymentInstructions paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on OffsitePaymentMethod{paymentMethodIdentifier name billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on ManualPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on CustomPaymentMethod{additionalDetails name paymentInstructions id paymentMethodIdentifier billingAddress{...on StreetAddress{name firstName lastName company address1 address2 city countryCode zoneCode postalCode coordinates{latitude longitude __typename}phone __typename}...on InvalidBillingAddress{__typename}__typename}__typename}...on DeferredPaymentMethod{orderingIndex displayName __typename}...on PaypalBillingAgreementPaymentMethod{token billingAddress{...on StreetAddress{address1 address2 city company countryCode firstName lastName phone postalCode zoneCode __typename}__typename}__typename}__typename}__typename}__typename}__typename}buyerIdentity{...on PurchaseOrderBuyerIdentityTerms{contactMethod{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}marketingConsent{...on PurchaseOrderEmailContactMethod{email __typename}...on PurchaseOrderSMSContactMethod{phoneNumber __typename}__typename}__typename}__typename}merchandise{merchandiseLines{merchandise{...ProductVariantSnapshotMerchandiseDetails __typename}__typename}__typename}tax{totalTaxAmount{amount currencyCode __typename}__typename}discounts{lines{deliveryAllocations{amount{amount currencyCode __typename}index __typename}__typename}__typename}}fragment ProductVariantSnapshotMerchandiseDetails on ProductVariantSnapshot{variantId options{name value __typename}productTitle title sellingPlan{name id digest deliveriesPerBillingCycle prepaid subscriptionDetails{billingInterval billingIntervalCount billingMaxCycles deliveryInterval deliveryIntervalCount __typename}__typename}__typename}",
            "variables": {
                "receiptId": self.receipt_id,
                "sessionToken": self.session_token
            },
            "operationName": "PollForReceipt"
        }

        return processing_poll

    def fix_graphql(self, req):
        soup = BeautifulSoup(req.text, 'html.parser')
        graphql = soup.find('meta', {'name': 'serialized-graphql'}).get('content')
        return json.loads(graphql)

    def get_checkout_token(self):
        for cookie in self.session.cookies:
            if 'checkout_session_token' in cookie.name:
                token = urllib.unquote(cookie.value)
                return json.loads(token)['token']
        return None