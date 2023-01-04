""" A lambda function handler to make requests to the
    Global Entry appointments API for a number of specified
    location IDs. These IDs will be set via an environment
    variable for the  lambda.

    Expected environment variables:

    * LOCATION_IDS - A comma separated list of integer location IDs, e.g.:
      '1234,2345'.
    * SNS_TOPIC_ARN - The ARN for the SNS topic that will publish the message
      containing any appointments. This is defined as part of the
      CloudFormation stack created via SAM.

"""
from os import environ
from typing import Dict, List, Optional
import json

from boto3 import client as boto3_client
import requests


LOCATION_IDS = environ.get('LOCATION_IDS').split(',')
SNS_TOPIC_ARN = environ.get('SNS_TOPIC_ARN')


def get_all_locations() -> Dict[str, str]:
    """ Return a mapping of all location IDs to a human readable string. """
    locations_response = requests.get(
        'https://ttp.cbp.dhs.gov/schedulerapi/locations/',
    )
    locations_response.raise_for_status()

    return {str(location['id']): location['name']
            for location in locations_response.json()}


def request_location_appointment(location_id: str) -> Optional[str]:
    """ Make a request to the Global Entry API for a single
        location:

        Response structure:

        ```
        [{'locationId': 7960,
          'startTimestamp': '2023-07-12T09:30',
          'endTimestamp': '2023-07-12T09:45',
          'active': true,
          'duration': 15,
          'remoteInd': false
        }]
        ```
    """
    request_json = {'limit': 1,
                    'locationId': location_id,
                    'minimum': 1,
                    'orderBy': 'soonest'}

    response = requests.get('https://ttp.cbp.dhs.gov/schedulerapi/slots',
                            params=request_json)
    response.raise_for_status()

    response_json = response.json()

    if len(response_json) > 0:
        next_appointment = response_json[0].get('startTimestamp')
    else:
        next_appointment = None

    return next_appointment


def get_appointments(locations_mapping: Dict[str, str],
                     location_ids: List[str]) -> Dict[str, str]:
    """ Make a request to the Global Entry /schedulerapi/slots endpoint
        for each specified location ID. If there is an appointment, place
        it in a dictionary, under the location name key.

    """
    appointments_dict = {}

    for location_id in location_ids:
        location_appointment = request_location_appointment(location_id)
        location_name = locations_mapping.get(location_id)

        if location_appointment is not None and location_name is not None:
            appointments_dict[location_name] = location_appointment

    return appointments_dict


def get_formatted_message(appointment_dict: Dict[str, str]) -> str:
    """ Construct a formatted multiline string with an entry for
        each location that has an available appointment.

    """
    return '\n'.join([f'* {location}: {appointment_datetime}'
                      for location, appointment_datetime
                      in appointment_dict.items()])


def publish_message(appointments_dict: Dict[str, str]):
    """ Only called if there is an appointment available at at least one
        specified location.

    """
    sns_client = boto3_client('sns')
    sns_client.publish(TopicArn=SNS_TOPIC_ARN,
                       Message=get_formatted_message(appointments_dict),
                       Subject='Global Entry soonest appointments')


def handler(event, context):
    """ The handler for a lambda that is triggered on a schedule. This
        function will find a mapping of all Global Entry locations,
        find the soonest appointment for each location that is specified
        in the `LOCATION_IDS` environment variable and then, if there are
        any available appointments, a message will be published to an SNS
        topic.

    """
    # Get mapping of locations IDs to human readable names:
    locations_mapping = get_all_locations()

    if LOCATION_IDS is not None:
        appointments_dict = get_appointments(locations_mapping, LOCATION_IDS)
    else:
        appointments_dict = {}

    # Pubish message to SNS topic if there are any appointments
    if len(list(appointments_dict.keys())) > 0:
        publish_message(appointments_dict)
        response_body = json.dumps(appointments_dict)
    else:
        response_body = 'No appointments found for specified locations.'

    return {'body': response_body, 'statusCode': 200}
