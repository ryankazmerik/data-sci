from basehandler import BaseHandler

class ExploreHandler(BaseHandler):
    profile = "Explore-US-DataScienceAdmin"
    environment = "Explore-US"
    subnets = []
    security_groups = []
    role_name = ""
    aws_account_id = ""
    role_info = {
        "RoleArn": "arn:aws:iam::564285676170:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_StellarDataScienceAdmin_2d775ec3112a605f",
        "RoleSessionName": f"{profile}-session"
    }
    
    random_bucket_id = {
        "retention": "ut8jag",
        "product-propensity": "u8gldf",
        "event-propensity": "tykotu"
    }

    # def __init__(self) -> None:
    #     super().__init__()

    # def __str__(self) -> str:
    #     return super().__str__()

