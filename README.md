# The Stellar Algo Data Science Super Fantastic Readme
You know, for data science...

- [Style Guidelines](#style-guidelines)
- [Onboarding](#onboarding)
  - [Setup](#setup)
    - [Installs](#installs)
    - [Git & Repo & Folder Setup](#git--repo--folder-setup)
    - [Conda (Python) Setup](#conda-python-setup)
    - [Visual Studio Code (VSCode) Setup](#visual-studio-code-vscode-setup)
    - [AWS CLI Setup](#aws-cli-setup)
    - [Docker/Terraform/Pyodbc Setup](#dockerterraformpyodbc-setup)
  - [Challenges](#challenges)
    - [RedShift Challenge](#redshift-challenge)
    - [S3 Challenge](#s3-challenge)
    - [SSM Challenge](#ssm-challenge)
    - [Lambda Challenge](#lambda-challenge)

## Style Guidelines
This covers the main style guidelines for work in the Data-Sci repositories. If there is something not covered here then please reach out to someone or refer to [The PEP8 Guidelines](https://pep8.org/)

>❗ Note that the styles in this README overrule the styles in the PEP8 Guidelines.

<br/>

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


When writing functions declare if they are private or public using an underscore as a prefix. This does not change how they are *actually* accessed, it is a suggestion to other programmers (in Java private functions can't be accessed outside the class, in Python its a suggestion). Example:

```python
# Private
def _my_private_function():
    print('This should be called within this module.')

# Public
def my_public_function():
    print('This can be called from outside this module.')
```

Type hinting should be added to functions to help describe what the variable should be or what it is. These can be added by writing a variable in the function parameter with a colon and the data type; the return value is typed with an arrow and the data type at the end of the function. 

This has the following benefits:
* Lets users easily understand parameters & return values without complex names
* Has integration with VSCode to show code suggestions. For example, if you have a parameter that is a dict it will show the functions available for dicts, without typing it wouldn't show anything

Type hinting can be done by following the example below:

```python
def my_function(param_a: str, param_b: int, param_c:Dict[str, int]) -> bool:
    print(f'You can access the variables as you normally would: {param_a}')
    return True
```

White space should be added to the code to match the below requirements:
1. after a function is defined / after the docstring of a function
2. before a function is defined
3. after a control statement (if, while, etc)
4. before a control statement
5. before a return statement
6. between logical groupings of code (if x, y, z work together then they should be grouped, if not made into a function)

See the example below for white space:
```python
import pandas as pd

MY_GLOBAL_VAR = 'Hello world'

def my_function():

    print("hi")
    my_var = 123
    
    return my_var

# This is a logical grouping, with white space above the comment.
conn = my_db_connection()
result = conn.execute("select * from my_db.my_table")
print(result)

if True:
    
    print("True")

```


# Onboarding
The onboarding section will setup the environment, help with working in the environment, and provide challenges to get used to the environment.

## Setup

This section is a WIP. If you find anything missing, please add it or ask **Peter Morrison** to add it. The section will cover the general onboarding to use all of the Data Science environment, if something is not needed, then feel free to skip the step.

### Installs
>❗ **Reminder:** don't just copy-paste without reading commands, especially when they use sudo!

>✏️ **Using vim**<br>
>If you don't know how to edit files in terminal/use vim you can get by with just the following commands - anything in code format is a command to type, brackets are comments for the reader. Arrows will indicate a new command:
>1. `vim your_file_to_edit`
>2. `a` (this lets you go to edit mode + make your changes)
>3. `escape -> :wq` (this will save and exit)
>4. `escape -> :q!` (this will exit without saving)

The following software should be installed (The links may assume you're on Mac. If you're on Windows or Linux please find the correct version):
1. [Visual Studio Code](https://code.visualstudio.com/download)
2. [Home Brew](https://brew.sh/)
3. [iTerm2](https://iterm2.com/downloads.html)
   * This was easier to install through following two guides in the exact order. This will set you up to use the iTerm2 app instead of the built in terminal and it will use zsh as a default with "oh my zsh" as a plugin manager + makes <strike>it look pretty</strike> you a better programmer.
   1. [Terminal Guide 1](https://medium.com/ayuth/iterm2-zsh-oh-my-zsh-the-most-power-full-of-terminal-on-macos-bdb2823fb04c)
   2. [Terminal Guide 2](https://dev.to/ibrahim_s/iterm2-oh-my-zsh-dracula-theme-plugins-2f9e)
      * This one installs the syntax highlighting and autocompletion plugins which are worth installing.
4. [Minicoda (Python)](https://docs.conda.io/en/latest/miniconda.html#:~:text=Miniconda%20is%20a%20free%20minimal,zlib%20and%20a%20few%20others.)
5. [Docker](https://docs.docker.com/desktop/mac/install/)
   * This may need you to run `softwareupdate --install-rosetta` if your computer has an M1 Apple chip.
6. [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
   * This is easier with the CLI than the GUI installation. You can just copy-paste the commands into your terminal 

The following installs won't work if you're on an M1 Mac:
1. [DBeaver Community Edition]()
   1. If so see section on M1 Mac Workarounds


### Git & Repo & Folder Setup
If git isn't pre-installed (check with the terminal `git --version`), then you can install it through brew or by download [Github Desktop](https://desktop.github.com/).

There are only a few repos used, but the best way to keep these managed on your local computer is by having them all in a single folder. For example, I (Peter Morrison) have my folder structure as `Documents/repos/` and inside that folder is where I git clone each Data Science repo.

The repos that are useful to pull are:
* https://github.com/stellaralgo/data-sci
* https://github.com/stellaralgo/datascience-shared-utilities
* https://github.com/stellaralgo/data-sci-product-propensity
* https://github.com/stellaralgo/infrastructure-utilities


### Conda (Python) Setup
Once miniconda is installed you can type in the terminal: `conda create --name stellar python=3.8`

Then to activate the environment you can type `conda activate stellar`.

This is similar to Python's venv library. It creates a new folder with a copy of Python (with the specified version above) and keeps the installed libraries (through `pip install`) isolated. This keeps your scripts running with specific versions rather than getting updates and prevents conflicting libraries from affecting a project.

Generally we work in the `stellar` environment, but you can create a new environment anytime you want a spearate Python environment for a project.

When in a Jupyter notebook ensure that the top-right of the notebook says its running in your conda environment.

### Visual Studio Code (VSCode) Setup
The VSCode setup is largely adding extensions that we use to collaborate and work in the environment. 

Below is the list of required extensions. If you copy-paste the line into the extension search bar you will get the exact plugin. You can also copy paste the whole list and it will show all extensions in one search:
* ms-toolsai.jupyter
* ms-toolsai.jupyter-keymap
* ms-toolsai.jupyter-renderers
* ms-vsliveshare.vsliveshare-pack
* ms-vsliveshare.vsliveshare
* ms-vsliveshare.vsliveshare-audio
* ms-python.python
* ms-python.vscode-pylance
* ms-vscode-remote.remote-containers

Optional Extensions:
* yzhang.markdown-all-in-one
* eamodio.gitlens
* njpwerner.autodocstring

### AWS CLI Setup
After the AWS CLI is installed you want to set up the profiles. When you set up a profile you can specify its name in boto3 to connect using that profile. For example, we will set up in this section a profile for StellarAlgo and for Explore-US to access resources in each.

1. In terminal type `aws configure sso` -> hit enter
2. Type in `https://stellaralgo.awsapps.com/start#/` -> hit enter
3. Type in `us-east-1` -> hit enter
4. Complete auth in the browser window it opened
5. Choose your profile (choose Stellaralgo for now)
6. Choose your role (Choose DataScienceAdmin)
7. Type in `us-east-1` -> hit enter
8. Type in `json` -> hit enter
9. Type in Stellaralgo-DataScienceAdmin (or Explore-US-DataScienceAdmin if you chose that profile) -> hit enter

The prompt should be done now, you can verify this worked by typing in the terminal `cat ~/.aws/config` and it should print out your profile and data like the following (with only one profile though. Complete this again for the other profile):
```
[profile Explore-US-DataScienceAdmin]
sso_start_url = https://stellaralgo.awsapps.com/start
sso_region = us-east-1
sso_account_id = <account id here>
sso_role_name = StellarDataScienceAdmin
region = us-east-1
output = json

[profile Stellaralgo-DataScienceAdmin]
sso_start_url = https://stellaralgo.awsapps.com/start#/
sso_region = us-east-1
sso_account_id = <account id here>
sso_role_name = StellarDataScienceAdmin
region = us-east-1
output = json
```
If any of the above is different then you can update these by editing the file with vim.

### Docker/Terraform/Pyodbc Setup
>This assumes you have installed Docker and the Container extension in the above sections.

Go to the [infrastructure-utilities](https://github.com/stellaralgo/infrastructure-utilities) repo and pull it to your repo folder (or just download as a zip) then extract the two zip files. These two zip files can be used to run docker containers for two separate purposes. The purposes are:
1. **Stellar Developer Dev Container**. This is to access Pyodbc from an M1 Mac.
2. **Stellar Infrastructure Dev Container**. This is to work on Terraform and Docker projects.

To run either of these you must move the unzipped folder called `.devcontainer` to the root folder of a project you want to work on. Then when you open the root folder of the project in VSCode you will see a prompt on the bottom right asking to open the project as a container. If you confirm it will startup the container and let you work within that environment.

Further instructions on working within and activating these environments are available in the folder `.devcontainer`.

I set mine up to have the infrastructure zip in my repos folder and the dev zip in my documents folder (since its less used). (My folder structure goes: `Documents>Repos>{data-sci, data-sci-product-propensity, etc}`)

## Challenges

### RedShift Challenge
We have a database in our qa-app cluster, ds schema, called dummytable. The challenge is to create a notebook in your sandbox that does the following:

* Read the records from this table and display in a pandas dataframe
* Create a new record in the table, following the format of the other records, then display only the new record in a dataframe
* Update an existing record, then display the updated record in a dataframe
* Delete the new record you created, and display all records in a dataframe to ensure it was deleted.
* Be sure to add some markdown documentation, and inline code documentation to describe what your code is doing.
* Once finished, push up to our data-sci git repo


### S3 Challenge
Create an S3 bucket our Explore-US environment: s3://ai-experimentation-td4np7/{your name without the curly brackets}-challenge/

* The challenge is to create a notebook in your sandbox that does the following:
* List the filename of each file in your bucket
* Upload a json file into the bucket, then read the bucket and display the new filename
* Read that file out of the bucket and display the contents.
* Be sure to add some markdown documentation, and inline code documentation to describe what your code is doing.
* Once finished, push up to our data-sci git repo


### SSM Challenge
There is an SSM parameter in our Explore-US environment called: /customer/model-retention/ai/db-connections/data-sci-retention/database-read

The challenge is to create a notebook in your sandbox that does the following:
* Read the value of the SSM parameter
* Use the values in the SSM parameter to form a connection string to the MSSQL database listed in the parameter
* Read the contents of the ds.customerScores table into a dataframe


### Lambda Challenge
Before you start this challenge, upload a json file into your challenge folder in this bucket: s3://ai-experimentation-td4np7

The challenge is to create a new lambda that uses the ‘test-retention-role’ in our Explore-US environment that does the following:
* Create two functions, one called convert_to_parquet and one called convert_to_csv
* Each function should read the json file from the S3 bucket, convert it to the appropriate type (parquet or csv), and then write the file back to the bucket in the new file format.
* Then create a test event that passes in the file type and path to the s3 bucket.