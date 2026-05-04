import json
import urllib.parse
from workflow import app
from datetime import datetime
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
table = dynamodb.Table('ClaimsTable')


def lambda_func(event,context):

    for record in event['Records']:
        bucket=record['s3']['bucket']['name']
        key=urllib.parse.unquote_plus(record['s3']['object']['key'])

        print(f"triggered by file :{key} in bucket: {bucket}")

        test_input = {
            "property_id": "PROP_10",
            "user_id": "USER",
            "check_in_url": "image copy.png",   
            "check_out_url":key,
            "anamolies": [],
            "is_image_clear": False,
            "total_claim_value": 0,
            "status": "Starting Pipeline via S3 Trigger"
        }

        final_state=app.invoke(test_input)
        try:
            anamoly=json.dumps(final_state['anamolies'])

            processed_anamolies = json.loads(anamoly)
            value=final_state.get('total_claim_value',0)
            value=str(value)
            total_value=Decimal(value)

            table.put_item(
                Item={'user_id': final_state['user_id'],
                    'property_id': final_state['property_id'],
                    'timestamp': datetime.now().isoformat(),
                    'total_claim': total_value,
                    'status': final_state['status'],
                    'anamolies': processed_anamolies,
                    'check_out_image': key
                }
            )
            print(f"data saved to Dynamodb {final_state['user_id']}")
        except Exception as e:
            print(f"dynamodb Error: {e}")

    return "complete"