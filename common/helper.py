
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import dateutil.parser
import boto3
import json
import logging
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from slack_sdk.errors import SlackApiError



logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret = boto3.client('secretsmanager') 
lexClient = boto3.client('lex-runtime')
slacksecret = json.loads(secret.get_secret_value(SecretId='SLACK_LEX_BLOCK_KIT')['SecretString'])
slackClient = WebClient(slacksecret['SLACK_BOT_TOKEN'])
signatureVerifier = SignatureVerifier(slacksecret["SLACK_SIGNING_SECRET"])

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }
    
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


#Verify requests as recommended by Slack. More details can be found at https://api.slack.com/authentication/verifying-requests-from-slack
def is_valid_request(body, timestamp, signature):
        return signatureVerifier.is_valid (body, timestamp, signature)

#Post event received from Slack to Lex and post Lex reply to Slack
def forward_to_Lex(team_id, user_id, forwardToLex):
    """
    Process event in Slack Block kit objects and forward messages to Lex
    """
    
    response = lexClient.post_text(
    botName=slacksecret['BOT_NAME'],
    botAlias=slacksecret['BOT_ALIAS'],
    userId=slacksecret['LEX_SLACK_CHANNEL_ID']+":"+ team_id+ ":" + user_id,
    inputText=forwardToLex
    )
    postInSlack(user_id, response['message'])

#Post in Slack either text or elements of Block kits
def postInSlack(user_id, message, messageType='Plaintext', bot_token=slacksecret['SLACK_BOT_TOKEN']):
    try:
        # Call the chat.postMessage method using the WebClient
        if (messageType == 'blocks'):
            slackClient.chat_postMessage(
            channel=user_id, token=bot_token, blocks=message
        )

        else:
            slackClient.chat_postMessage(
            channel=user_id, token=bot_token, text=message
        )

    except SlackApiError as e:
        logger.error(f"Error posting message: {e}")
