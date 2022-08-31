import json
import random
import time
import traceback
from os.path import exists
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

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

# Needs two, as a majority of OKDO pages use the ATC value, but some US pages use the shortlink to store PID
def get_pid_new(html):
    soup = BeautifulSoup(html,'html.parser')
    try:
        return soup.find('button', {'name': 'add-to-cart'}).get('value')
    except:
        return soup.find('link', {'rel': 'shortlink'}).get('href').split('=')[1]
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
        self.title = ''

        self.main_site = self.info
        self.status_signal.emit({"msg": "Starting", "status": "normal"})
        self.country = utils.get_country_code(profile['shipping_country'])
        if '/us/' in str(self.info).lower():
            self.site_prefix = '/us'
        elif '/nl/' in str(self.info).lower():
            self.site_prefix = '/nl'
        else:
            self.site_prefix = ''

        if 'okdo.com' not in str(self.info).lower():
            self.status_signal.emit({"msg": "Invalid OKDO link!", "status": "error"})
        elif not exists('./chromedriver.exe'):
            self.status_signal.emit({"msg": "ChromeDriver.exe not found!", "status": "error"})
        else:
            self.monitor()
            # I got lazy
            self.complete_order_browser()

    def monitor(self):
        while True:
            try:
                self.status_signal.emit({"msg": "Checking stock", "status": "checking"})
                # Makes request to page URL
                get_item_page = self.session.get(self.info)
                # Makes sure that request returns a 200 response code
                if get_item_page.status_code == 200:
                    data_json = get_json(get_item_page.text)
                    # If PID isn't stored, obtain from page
                    if self.pid == '':
                        self.pid = get_pid_new(get_item_page.content)
                        print(self.pid)
                    # If item name isn't stored, obtain from page and change product on task to name of item
                    if self.title == '':
                        self.title = check_name(data_json)
                        prod_id = 'UK' if self.site_prefix == '' else str(self.site_prefix).upper()[1:]
                        self.product_signal.emit(f'{self.title} [{prod_id}]')
                    # If item image isn't stored, obtain from page
                    if self.image == '':
                        self.image = check_image(data_json)
                    # Available is either outofstock or instock so we check for 'out'
                    available = 'out' not in check_stock(data_json)
                    if available:
                        # Item ATC form
                        okdo_cart_add = {'product_id': self.pid, 'quantity': str(self.qty), 'action': 'peake_add_to_basket'}
                        self.status_signal.emit({"msg": "Adding to cart", "status": "normal"})
                        # Sends ATC Data
                        cart_req = self.session.post(f'https://www.okdo.com{self.site_prefix}/wp-admin/admin-ajax.php',data=okdo_cart_add).json()
                        if 'error' in cart_req:
                            self.status_signal.emit({"msg": "Error carting", "status": "error"})
                            time.sleep(float(self.error_delay))
                        else:
                            self.status_signal.emit({"msg": "Added to cart", "status": "carted"})
                            if self.settings['webhookcart']:
                                cart_web(str(self.info),self.image,f'OKDO ({str(self.site_prefix).upper()[1:]})', self.title, self.profile["profile_name"])
                        return
                    else:
                        self.status_signal.emit({"msg": "Waiting for restock", "status": "monitoring"})
                        self.update_random_proxy()
                        time.sleep(float(self.monitor_delay))
            except Exception as e:
                self.status_signal.emit({"msg": f"Error on monitor [{get_item_page.status_code}]", "status": "error"})
                self.update_random_proxy()
                time.sleep(float(self.error_delay))

    def complete_order_browser(self):
        try:
            self.status_signal.emit({"msg": "Loading headless browser", "status": "normal"})
            # These are the settings for Selenium
            caps = DesiredCapabilities().CHROME
            caps["pageLoadStrategy"] = 'eager'
            options = Options()
            options.headless = True
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
            driver.get(f"https://okdo.com{self.site_prefix}")

            # Transfers cookies from session to browser
            for cookie in self.session.cookies:
                driver.add_cookie({'name': cookie.name, 'value': cookie.value, 'path': cookie.path})
            # Goes to checkout in browser
            self.status_signal.emit({"msg": "Going to checkout", "status": "normal"})
            driver.get(f"https://okdo.com{self.site_prefix}/checkout")
            self.status_signal.emit({"msg": "Filling shipping info", "status": "normal"})
            profile = self.profile
            # Fills name
            first_name = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#billing_first_name')))
            first_name.send_keys(profile["shipping_fname"])
            #driver.find_element(By.CSS_SELECTOR,'#billing_first_name').send_keys(profile["shipping_fname"])
            driver.find_element(By.CSS_SELECTOR, '#billing_last_name').send_keys(profile["shipping_lname"])
            # Selects country. I had to loop through the countries because some countries contains extra characters
            # ie United States (US) so I just checked to see if the shipping country name was in the option
            select = Select(driver.find_element(By.CSS_SELECTOR, '#billing_country'))
            index = 0
            for value in select.options:
                if profile['shipping_country'].lower() in str(value):
                    select.select_by_index(index)
                    break
                else:
                    index += 1
            # Won't fill your Apt info if it's blank
            if profile['shipping_a2'] != '':
                driver.find_element(By.CSS_SELECTOR,'#billing_address_1').send_keys(profile['shipping_a2'])
            # Fills address
            driver.find_element(By.CSS_SELECTOR, '#billing_address_2').send_keys(profile['shipping_a1'])
            # Fills city
            driver.find_element(By.CSS_SELECTOR, '#billing_city').send_keys(profile['shipping_city'])
            # Only fills state if country is US
            if self.country == 'US':
                Select(driver.find_element(By.CSS_SELECTOR, '#billing_state')).select_by_visible_text(utils.get_state_name(profile['shipping_country'],profile['shipping_state']))
            # Fills zip code
            driver.find_element(By.CSS_SELECTOR, '#billing_postcode').send_keys(profile['shipping_zipcode'])
            # Fills phone
            driver.find_element(By.CSS_SELECTOR, '#billing_phone').send_keys(profile['shipping_phone'])
            # Fills email
            driver.find_element(By.CSS_SELECTOR, '#billing_email').send_keys(profile['shipping_email'])
            # Waits for cookie button to load (incase there is site lag) and clicks it
            cookie_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'body > div.c-notification-bar.c-notification-bar--sequential > div > div > div > div.c-notification-bar__item-actions > div > button.c-button.c-notification-bar__item-button.c-button--white.gdpr-i-agree-button.qa-gdpr-i-agree-button > span')))
            cookie_button.click()
            # Waits for proceed button to load (incase there is site lag) and clicks it
            proceed_button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#maincontent > div.l-grid > aside > div > div.c-order-summary > button.c-button.c-button--shop.c-button--fullwidth.c-order-summary__submit.c-button--icon-right')))
            proceed_button.click()
            self.status_signal.emit({"msg": "Filling card info", "status": "normal"})
            # Waits for Credit Card radio button to load (incase there is site lag) and clicks it
            cc_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#payment > fieldset > ul > li:nth-child(2) > div.fancy-radio.wc_payment_method.payment-methods__radio.payment_method_stripe > label")))
            cc_button.click()
            # Switches to CC Frame
            frame = driver.find_element(By.XPATH,'/html/body/div[1]/div[4]/div[2]/form[2]/main/div[1]/div/div[2]/div/fieldset/ul/li[2]/div[3]/div/fieldset[1]/div[1]/div/iframe')
            driver.switch_to.frame(frame)
            # Clicks CC input and inserts card info
            cc_info = WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.NAME, 'cardnumber')))
            cc_info.click()
            cc_info.send_keys(f'{profile["card_number"]}{profile["card_month"]}{str(profile["card_year"]).replace("20","")}{profile["card_cvv"]}')
            # Switches back to main frame
            driver.switch_to.parent_frame()
            # Sleeps half a second to help CC info properly input
            time.sleep(0.5)
            # Clicks proceed button
            driver.find_element(By.CSS_SELECTOR,'#maincontent > div.l-grid > aside > div > div.c-order-summary.c-order-summary--readonly > button.c-button.c-button--shop.c-button--fullwidth.c-order-summary__submit.c-button--icon-right > span').click()
            # Waits for accept button to load and clicks
            accept = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'#terms-of-sale-accept > div > div > label')))
            accept.click()
            self.status_signal.emit({"msg": "Submitting Order", "status": "normal"})
            # Clicks submit order
            driver.find_element(By.CSS_SELECTOR,'#maincontent > div.l-grid > aside > div > div.c-order-summary.c-order-summary--readonly > button.c-button.c-button--shop.c-button--fullwidth.c-order-summary__submit.c-button--icon-right > span').click()

            processing = False

            # Waits for browser URL to either have order-payment (Fails and redirects back to payment) or order-received (Success)
            while True:
                if 'order-review' in driver.current_url:
                    time.sleep(1)
                elif driver.current_url.endswith('/checkout/#'):
                    if not processing:
                        self.status_signal.emit({"msg": "Processing", "status": "alt"})
                        processing = True
                    time.sleep(1)
                elif 'order-payment' in driver.current_url:
                    self.status_signal.emit({"msg": "Order Failed", "status": "error"})
                    if self.settings['webhookfailed']:
                        failed_spark_web(self.info,self.image,f'OKDO ({str(self.site_prefix).upper()[1:]})',self.title,self.profile['profile_name'])
                    if self.settings['notiffailed']:
                        send_notif(self.title,'fail')
                    break
                elif 'order-received' in driver.current_url:
                    self.status_signal.emit({"msg": "Order Placed", "status": "success"})
                    if self.settings['webhooksuccess']:
                        good_spark_web(str(driver.current_url), self.image, f'OKDO ({str(self.site_prefix).upper()[1:]})', self.title,
                                         self.profile['profile_name'])
                    if self.settings['notifsuccess']:
                        send_notif(self.title,'success')
                    break
            driver.close()
        except Exception:
            self.status_signal.emit({"msg": "Error on browser", "status": "error"})
            print(traceback.format_exc())
            driver.close()


    def update_random_proxy(self):
        if self.proxy_list != False:
            self.session.proxies.update(utils.format_proxy(random.choice(self.proxy_list)))


