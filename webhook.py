import json
import traceback
from datetime import datetime

import requests

import settings

version = '1.21'

def new_web(status, site_name, image, item_name, profile, price = 'N/A', checkout_time='N/A'):
    title = 'Item Carted'
    color = 16758888
    if status == 'success':
        title = 'Successful Checkout'
        color = 6075075
    elif status == 'failed':
        title = 'Checkout Failed'
        color = 13893632

    embed_to_send = {'embeds': [{'title': title, 'color': color, 'footer': {'text': f'Pi Bot v{version}- {datetime.now().strftime("%I:%M.%S %p")}'},'fields': []}]}

    embed_to_send['embeds'][0]['thumbnail'] = {'url': image}
    embed_to_send['embeds'][0]['fields'].append({'name': 'Site', 'value': site_name})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Item', 'value': item_name})
    embed_to_send['embeds'][0]['fields'].append({'name': 'Profile', 'value': f'||{profile}||'})
    if price != 'N/A':
        embed_to_send['embeds'][0]['fields'].append({'name': 'Price', 'value': price, 'inline': True})
    if checkout_time != 'N/A':
        embed_to_send['embeds'][0]['fields'].append({'name': 'Checkout Speed', 'value': f'{str(round(float(checkout_time), 2))}s', 'inline': True})

    json_to_send = json.dumps(embed_to_send).encode('UTF-8')
    if settings.webhook != "":
        requests.post(settings.webhook, data=json_to_send, headers={'Content-Type': 'application/json'})
