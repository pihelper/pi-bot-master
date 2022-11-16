import json
import traceback
from datetime import datetime

import requests

import settings

def good_web(url, image, site, prod, prof, price, speed):
    embed_to_send = {'embeds': [{'title': 'Successful Checkout!', 'url': url, 'color': 6075075, 'footer': {'text': f'Pi Bot - {datetime.now()}'}, 'fields': []}]}
    if image != '':
        embed_to_send['thumbnail'] = {'url': image}
    embed_to_send['embeds'][0]['fields'].append({'name': 'Module', 'value': site})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Item', 'value': prod})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Profile', 'value': f'||{prof}||'})
    if price != '':
        embed_to_send['embeds'][0]['fields'].append({'name': 'Price', 'value': price, 'inline': True})
    if speed != '':
        embed_to_send['embeds'][0]['fields'].append({'name': 'Checkout Speed', 'value': f'{str(round(float(speed), 2))}s', 'inline': True})

    json_to_send = json.dumps(embed_to_send).encode('UTF-8')

    if settings.webhook != "":
        requests.post(settings.webhook, data=json_to_send, headers={'Content-Type': 'application/json'})

def good_spark_web(url, image, site, prod, prof):
    good = '{ "embeds": [ { "title": "Successful Checkout!", "url": "' + url + '", "color": 6075075, "footer": { "text": "Pi Bot - ' + str(datetime.now()) + '" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Module", "value": "' + site + '" }, { "name": "Product", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||", "inline": true }] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=good.encode('UTF-8'), headers={'Content-Type': 'application/json'})


def failed_web(url, image, site, prod, prof, price, speed):
    embed_to_send = {'embeds': [
        {'title': 'Failed Checkout', 'url': url, 'color': 13893632, 'footer': {'text': f'Pi Bot - {datetime.now()}'}, 'fields': []}]}
    if image != '':
        embed_to_send['thumbnail'] = {'url': image}
    embed_to_send['embeds'][0]['fields'].append({'name': 'Module', 'value': site})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Item', 'value': prod})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Profile', 'value': f'||{prof}||'})
    if price != '':
        embed_to_send['embeds'][0]['fields'].append({'name': 'Price', 'value': price, 'inline': True})
    if speed != '':
        embed_to_send['embeds'][0]['fields'].append(
            {'name': 'Checkout Speed', 'value': f'{str(round(float(speed), 2))}s', 'inline': True})

    json_to_send = json.dumps(embed_to_send).encode('UTF-8')

    if settings.webhook != "":
        requests.post(settings.webhook, data=json_to_send, headers={'Content-Type': 'application/json'})

def failed_spark_web(url, image, site, prod, prof):
    bad = '{ "embeds": [ { "title": "Checkout Decline", "url": "' + url + '", "color": 13893632, "footer": { "text": "Pi Bot - ' + str(datetime.now()) + '" }, "thumbnail": { "url": "' + image + '" }, "fields": [ { "name": "Module", "value": "' + site + '" }, { "name": "Product", "value": "' + prod + '" }, { "name": "Profile", "value": "||' + prof + '||", "inline": true }] } ] }'
    if settings.webhook != "":
        requests.post(settings.webhook, data=bad.encode('UTF-8'), headers={'Content-Type': 'application/json'})

def cart_web(url, image, site, prod, prof):
    embed_to_send = {'embeds': [
        {'title': 'Item Carted', 'url': url, 'color': 16758888, 'footer': {'text': f'Pi Bot - {datetime.now()}'}, 'fields': []}]}
    if image != '':
        embed_to_send['thumbnail'] = {'url': image}
    embed_to_send['embeds'][0]['fields'].append({'name': 'Module', 'value': site})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Item', 'value': prod})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Profile', 'value': f'||{prof}||'})
    json_to_send = json.dumps(embed_to_send).encode('UTF-8')
    if settings.webhook != "":
        requests.post(settings.webhook, data=json_to_send, headers={'Content-Type': 'application/json'})