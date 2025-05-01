import boto3
import json
from botocore.exceptions import ClientError

class NovaClient:
    def __init__(self, region_name='us-east-1'):
        self.nova_client = boto3.client('bedrock-runtime', region_name=region_name)
    
    def invoke_model(self, model_id: str, prompt: str, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        try:
            # Prepare request body
            request_body = {
                "schemaVersion": "messages-v1",
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ],
                "inferenceConfig": {
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9
                }
            }
            
            # Call Bedrock Runtime
            response = self.nova_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body)
            )
            
            # Process response
            response_body = json.loads(response['body'].read())
            print("response body: ",response_body)
            
            return response_body
            
        except ClientError as e:
            raise Exception(f"Error invoking Nova model: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")