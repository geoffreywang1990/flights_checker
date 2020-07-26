import os
import sys
import time

import boto3
from botocore.exceptions import ClientError




# config sender and receiver
from email_config import SENDER,RECIPIENT
AWS_REGION = "us-east-2"
CHARSET = "UTF-8"



def newest(path):
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    return max(paths, key=os.path.getctime)


def notify_latest_log():
    # The subject line for the email.

    latest_file = newest('log')
    subject = "[TICKET BOT]: {}".format(latest_file)
    attachment = open(latest_file,'r')
    # The email body for recipients with non-HTML email clients.
    body_text = attachment.read()
                
    client = boto3.client('ses',region_name=AWS_REGION)

    #Provide the contents of the email.
    response = client.send_email(
        Destination={
            'ToAddresses': [
                RECIPIENT,
            ],
        },
        Message={
            'Body': {
                'Text': {
                    'Charset': CHARSET,
                    'Data': body_text,
                },
            },
            'Subject': {
                'Charset': CHARSET,
                'Data': subject,
            },
        },
        Source=SENDER,
    )


if __name__ == '__main__':
    while True:
        notify_latest_log()
        time.sleep(7200)
