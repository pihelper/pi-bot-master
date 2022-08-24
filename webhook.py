import requests

import settings

def good_web(url, image, site, prod, prof, price):
    good = '{ "embeds": [ { "title": "Successful Checkout!", "url": "' + url + '", "color": 6075075, "footer": { "text": "Pi Bot" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Module", "value": "' + site + '" }, { "name": "Product", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||", "inline": true }, { "name": "Price", "value": "$' + price + '", "inline": true } ] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=good.encode('UTF-8'), headers={'Content-Type': 'application/json'})

def good_spark_web(url, image, site, prod, prof):
    good = '{ "embeds": [ { "title": "Successful Checkout!", "url": "' + url + '", "color": 6075075, "footer": { "text": "Pi Bot" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Module", "value": "' + site + '" }, { "name": "Product", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||", "inline": true }] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=good.encode('UTF-8'), headers={'Content-Type': 'application/json'})


def failed_web(url, image, site, prod, prof, price):
    bad = '{ "embeds": [ { "title": "Checkout Decline", "url": "' + url + '", "color": 13893632, "footer": { "text": "Pi Bot" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Module", "value": "' + site + '" }, { "name": "Product", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||", "inline": true }, { "name": "Price", "value": "$' + price + '", "inline": true } ] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=bad.encode('UTF-8'), headers={'Content-Type': 'application/json'})

def failed_spark_web(url, image, site, prod, prof):
    bad = '{ "embeds": [ { "title": "Checkout Decline", "url": "' + url + '", "color": 13893632, "footer": { "text": "Pi Bot" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Module", "value": "' + site + '" }, { "name": "Product", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||", "inline": true }] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=bad.encode('UTF-8'), headers={'Content-Type': 'application/json'})

def cart_web(url, image, site, prod, prof):
    cart = '{ "embeds": [ { "title": "Item Carted", "url": "' + url + '", "color": 16758888, "footer": { "text": "Pi Bot" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Site", "value": "' + site + '" }, { "name": "Item", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||" } ] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=cart.encode('UTF-8'), headers={'Content-Type': 'application/json'})