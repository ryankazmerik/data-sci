import boto3

def get_param(name: str, session: boto3.session.Session = None) -> str:
    
    if session is None:
        
        session = boto3.session.Session()
    
    ssm_client = session.client("ssm")
    response = ssm_client.get_parameter(Name=name, WithDecryption=True)
    
    return response["Parameter"]["Value"]