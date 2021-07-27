# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import helper
import json
from urllib.parse import unquote

def lambda_handler(event, context):
    """Verify requests received from Slack and then forward them to Lex if signature valid

    Raise Unauthorized exception if expected header values missing

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    403 Error if invalid Token
    """
    try:
        messAtt = event['Records'][0]['messageAttributes']
        timestamp = messAtt['timestamp']['stringValue']
        requestBody = event['Records'][0]['body']
        slack_signature = messAtt['signature']['stringValue']
        isFromSlack = helper.is_valid_request(requestBody, timestamp, slack_signature)
    except KeyError:
        return {
                "statusCode": 400,
                "body": {"message": "Bad request"}
            }
    except ValueError:
        return {
                "statusCode": 401,
                "body": {"message": "Unauthorized"}
            }

    
    if (isFromSlack):
            process_event(requestBody)
            return {
                "statusCode": 200,
                "body": {"message": "Request is being processed"}
            }
    else:
        return {
                "statusCode": 403,
                "body": {"message": "Unauthorized"}
            }


def process_event(event):
    """
    Process event in Slack Block kit objects and forward messages to Lex
    """
    unquoteEvent = unquote(event)
    payload = json.loads(unquoteEvent[8:])
    actions = payload["actions"]
    team_id = payload["team"]["id"]
    user_id = payload["user"]["id"]
    action_type = actions[0]["type"]
    if action_type == "button":    
       forwardToLex = actions[0]["value"]
    elif action_type == 'datepicker':
        forwardToLex = actions[0]['selected_date']
    elif action_type == 'timepicker':
        selected_time = actions[0]['selected_time'] 
        if selected_time < "12:00":
            selected_time += " AM"
        if selected_time == "12:00":
            selected_time = "12:00 PM"
        forwardToLex = selected_time
    else:
        forwardToLex = "None"
    helper.forward_to_Lex(team_id, user_id, forwardToLex)

