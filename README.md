# data-sci
You know, for data science.

## Style Guidelines
All variables should be named using underscores (no camelCase):

<pre>
dim_customer_master_id = 1001
</pre><br/>

All global variables should be named using all caps:

<pre>
DATABASE_NAME = 'stlrflames'
</pre><br/>

All import statements should appear at the top of the notebook or python script in alphabetical order:

<pre>
import awswrangler as wr
import boto3
import json
import matplotlib.pyplot as plt
import pandas as pd
</pre><br/>

All from import statements should appear below the initial import statements, with a line break in between, in alphabetical order:

<pre>
import awswrangler as wr
import boto3
import json

from datetime import datetime
from pycaret.classification import *
</pre><br/>

Any passwords should NEVER be hardcoded in a notebook or script. Either use the `getpass` package to be prompted for your password, or retrieve your credentials using an SSM parameter:

<pre>
PASSWORD = getpass.getpass(prompt='Enter your password')`
</pre><br/>

OR

<pre>
ssm_client = boto3.client("ssm", "us-east-1")

response = ssm_client.get_parameter(Name=f"/customer/model-retention/ai/db-connections/data-sci-retention/database-write", WithDecryption=True,)["Parameter"]["Value"]

params = json.loads(response)
</pre><br/>

Use the print-f standard for all print messages:

<pre>
print(f"The Calgary Flames have {num_fans} in their fan universe.")
</pre><br/>

