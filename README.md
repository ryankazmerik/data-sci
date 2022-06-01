- [data-sci](#data-sci)
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


### Docker/Terraform/Pyodbc Setup


## Challenges

