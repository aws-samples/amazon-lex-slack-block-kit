# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
This sample demonstrates an implementation of the Lex Code Hook Interface
in order to serve a sample bot which manages orders for flowers.
Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
as part of the 'OrderFlowers' template.

For instructions on how to set up and test this bot, as well as additional samples,
visit the Lex Getting Started documentation http://docs.aws.amazon.com/lex/latest/dg/getting-started.html.
"""
import helper
import time
import datetime
import math
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



""" --- Helper Functions that generates block kit elements --- """
def get_flower_type_block():
	responseBlock = """[
       {
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": " *We have available:*"
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Lilies*\n:star::star::star::star: 1528 reviews\n You can get Lilies for any occasion. Lilies are large and can be used in any bouquet. You can also mix it with any type of flower."
			},
			"accessory": {
				"type": "image",
				"image_url": "https://upload.wikimedia.org/wikipedia/en/a/af/Lily-flower-free.jpg",
				"alt_text": "lilies"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Roses*\n:star::star::star::star: 2082 reviews\n Roses are our most popular choice. You can't go wrong with roses! Roses are beautiful flowers with vivid color. They will embellish any bouquet."
			},
			"accessory": {
				"type": "image",
				"image_url": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Red_Roses.jpg",
				"alt_text": "roses"
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*Tulips*\n:star::star::star::star: 1638 reviews\n This is our second favorite - Tulips are discrete and lovely. They add characters to your bouquets. Order your tulips today!"
			},
			"accessory": {
				"type": "image",
				"image_url": "https://upload.wikimedia.org/wikipedia/commons/1/1b/Pink-Tulips-2009.jpg",
				"alt_text": "tulips"
			}
		},
		{
			"type": "divider"
		},
		{"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "You can choose one of the flower below:"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Lilies",
						"emoji": true
					},
					"value": "lilies"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Roses",
						"emoji": true
					},
					"value": "roses"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Tulips",
						"emoji": true
					},
					"value": "tulips"
				}
			]
		}
	    ]"""
	return responseBlock

def get_pickup_date_block():
	responseBlock = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Pick a date to pick up your flower"
			},
			"accessory": {
				"type": "datepicker",
				"action_id": "datepicker123",
				"initial_date": f'{datetime.date.today()}',
				"placeholder": {
					"type": "plain_text",
					"text": "Select a date"
				}
			}
		}
	]
	return responseBlock

def get_pickup_time_block():
	responseBlock = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Pick a time to pick up your flower"
			},
			"accessory": {
				"type": "timepicker",
				"action_id": "timepicker123",
				"initial_time": "11:40",
				"placeholder": {
					"type": "plain_text",
					"text": "Select a time"
				}
			}
		}
	]
	return responseBlock
	
""" --- Functions that control the bot's behavior --- """
def validate_order_flowers(flower_type, date, pickup_time):
    flower_types = ['lilies', 'roses', 'tulips']
    if flower_type is not None and flower_type.lower() not in flower_types:
        return helper.build_validation_result(False,
                                       'FlowerType',
                                        f'We do not have {flower_type}, would you like a different type of flower? Our most popular flowers are roses.')

    if date is not None:
        if not helper.isvalid_date(date):
            return helper.build_validation_result(False, 'PickupDate', 'I did not understand that, what date would you like to pick the flowers up?')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
            return helper.build_validation_result(False, 'PickupDate', 'You can pick up the flowers from tomorrow onwards.  What day would you like to pick them up?')

    if pickup_time is not None:
        if len(pickup_time) != 5:
            return helper.build_validation_result(False, 'PickupTime', "Not a valid time format.")

        hour, minute = pickup_time.split(':')
        hour = helper.parse_int(hour)
        minute = helper.parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            return helper.build_validation_result(False, 'PickupTime',"Not a valid time format.")

        if hour < 10 or hour > 16:
            # Outside of business hours
            return helper.build_validation_result(False, 'PickupTime', 'Our business hours are from ten a m. to five p m. Can you specify a time during this range?')

    return helper.build_validation_result(True, None, None)

def order_flowers(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    flower_type = helper.get_slots(intent_request)["FlowerType"]
    date = helper.get_slots(intent_request)["PickupDate"]
    pickup_time = helper.get_slots(intent_request)["PickupTime"]
    source = intent_request['invocationSource']
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = helper.get_slots(intent_request)
   
        validation_result = validate_order_flowers(flower_type, date, pickup_time)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            
            #check if request from slack and post block elements based on the slot to be elicited
            if intent_request['requestAttributes'] and 'x-amz-lex:channel-type' in intent_request['requestAttributes'] and intent_request['requestAttributes']['x-amz-lex:channel-type'] == 'Slack':
            	blocks = []
            	channel_id = intent_request['userId'].split(':')[2]
            	if validation_result['violatedSlot'] == 'FlowerType':
            		blocks = get_flower_type_block()
            	
            	if validation_result['violatedSlot'] == 'PickupDate':
            		blocks = get_pickup_date_block()
            	
            	if validation_result['violatedSlot'] == 'PickupTime':
            		blocks = get_pickup_time_block()
            		
            	helper.postInSlack (channel_id, blocks, 'blocks')
            return helper.elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        # Pass the price of the flowers back through session attributes to be used in various prompts defined
        # on the bot model.
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        if flower_type is not None:
            output_session_attributes['Price'] = len(flower_type) * 5  # Elegant pricing model

        return helper.delegate(output_session_attributes, helper.get_slots(intent_request))

    # Order the flowers, and rely on the goodbye message of the bot to define the message to the end user.
    # In a real bot, this would likely involve a call to a backend service.
    return helper.close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': f'Thanks, your order for {flower_type} has been placed and will be ready for pickup by {pickup_time} on {date}'})


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'OrderFlowers':
        return order_flowers(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
