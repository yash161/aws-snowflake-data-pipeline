import boto3
from src.utils.secret_manager_utils import SecretManagerUtils
import traceback
import sys
import json
class SendNotification:
    def __init__(self,sns_secret_name):
        self.sns_arn = SecretManagerUtils().get_secret(sns_secret_name)

    def send_sns_notification(self, subject,message):
        print("Starting to Send Notification...")
        region_name = 'us-east-1'
        client = boto3.client(service_name='sns', region_name=region_name)
        try:
            response = client.publish(
                TargetArn=str(self.sns_arn),
                Subject=subject,
                Message=json.dumps(message)
                # MessageStructure="json"
            )
            print("Response: ", response)
        except Exception as e:
            print("Error Sending Notification::")
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)
            print(f"Error [send_sns_notification]: {str(e)}")
            raise e
