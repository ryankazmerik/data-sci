from basehandler import BaseHandler

class QAHandler(BaseHandler):
    profile = "QA-DS-Admin"
    environment = "QA"
    subnets = ["subnet-016a23a22d09bac9b", "subnet-03e755df7e78d56f1"]
    security_groups = ["sg-053b15ed15d46581a"]
    role_name = "data-sci-product-propensity-pipeline-t6qwkf"
    aws_account_id = "564285676170"
    role_info = {
        "RoleArn": "arn:aws:iam::564285676170:role/data-sci-product-propensity-pipeline-t6qwkf",
        "RoleSessionName": f"{profile}-session"
    }

    random_bucket_id = {
        "retention": "",
        "product-propensity": "mgwy8o",
        "event-propensity": "j58tuq"
    }

    # def __init__(self) -> None:
    #     super().__init__()

    # def __str__(self) -> str:
    #     return super().__str__()

