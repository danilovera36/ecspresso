import os
import boto3

class SSMClient:
    def __init__(self):
        self.client = boto3.client("ssm", region_name=os.getenv("AWS_REGION"))
    
    def put_parameter(self, name, value):
        self.client.put_parameter(Name=name, Value=value, Type="SecureString", Overwrite=True)
        return f"arn:aws:ssm:{os.getenv('AWS_REGION')}:{os.getenv('AWS_ACCOUNT_ID')}:parameter{name}"
    
    def get_arn(self, name):
        return f"arn:aws:ssm:{os.getenv('AWS_REGION')}:{os.getenv('AWS_ACCOUNT_ID')}:parameter{name}"
