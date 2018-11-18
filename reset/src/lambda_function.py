#!/usr/bin/env python
# encoding: utf-8

import json
import requests
import os
import logging
from urllib.parse import parse_qs

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logging.basicConfig(format='%(asctime)s- %(name)s- %(message)s')

SLACK_POST_URL = os.environ['SLACK_POST_URL']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
POCKET_CONSUMER_KEY = os.environ['POCKET_CONSUMER_KEY']
POCKET_ACCESS_TOKEN = os.environ['POCKET_ACCESS_TOKEN']

POCKET_GET_API_URL = "https://getpocket.com/v3/get"
POCKET_SEND_API_URL = "https://getpocket.com/v3/send"
HEADERS = {
    'content-type': "application/json;charset = UTF8",
    'x-accept': "application/json",
    'cache-control': "no-cache"
}

def reset():
    try:
        payload = {
            "consumer_key": POCKET_CONSUMER_KEY,
            "access_token": POCKET_ACCESS_TOKEN,
            "tag"         : "twitter",
            "detailType"  : "complete",
            "count"       : 5000
        }
        res = requests.request("POST", POCKET_GET_API_URL, data=json.dumps(payload), headers=HEADERS)
        res.raise_for_status()
        res_json = res.json()
        actions = []
        for item_id in res_json['list'].keys():
            if len(res_json['list'][item_id]['tags']) == 1:
                action = {
                    "action" : "tags_remove",
                    "item_id": item_id,
                    "tags"   : "twitter"
                }
                actions.append(action)
        if len(actions) > 0:
            payload = {
                "consumer_key": POCKET_CONSUMER_KEY,
                "access_token": POCKET_ACCESS_TOKEN,
                "actions"     : actions
            }
            res = requests.request("POST", POCKET_SEND_API_URL, data=json.dumps(payload), headers=HEADERS)
            res.raise_for_status()
        text = "Reset success! %d items were deleted." % len(actions)
        color = "good"
    except:
        text = "Reset failed!"
        color = "#ff0000"
    return { "text": text, "color": color }

def lambda_handler(event, context):
    token = os.environ['SLACK_OUTGOING_WEBHOOK_TOKEN']
    query = parse_qs(event.get('body') or '')
    if query.get('token', [''])[0] != token:
        return { 'statusCode': 400 }
    slackbot_name = 'pocketer'
    if query.get('user_name', [slackbot_name])[0] == slackbot_name:
        return { 'statusCode': 200 }
    content = reset()
    slack_message = {
        'channel'    : SLACK_CHANNEL,
        'attachments': [
            content
        ],
    }
    try:
        req = requests.post(SLACK_POST_URL, data=json.dumps(slack_message))
        logger.info('Message posted to %s', slack_message['channel'])
        return { 'statusCode': 200 }
    except requests.exceptions.RequestException as e:
        logger.error('Request failed: %s', e)
        return { 'statusCode': 400 }