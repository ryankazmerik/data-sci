#!/bin/bash
set -e

#------------ setup autoshutdown ----------------#
# Everyday at 8:30 pm MST the notebook will autoshutdown if it has been idle for over 2 hours.
IDLE_TIME=7200
wget https://raw.githubusercontent.com/aws-samples/amazon-sagemaker-notebook-instance-lifecycle-config-samples/master/scripts/auto-stop-idle/autostop.py
(crontab -l 2>/dev/null; echo "30 3 * * * /usr/bin/python $PWD/autostop.py --time $IDLE_TIME --ignore-connections") | crontab -


#------------ configure github ------------------#
yum install jq -y
current_user=$(aws sts get-caller-identity)
user_id=$(echo $current_user | jq -r '.UserId')
IFS=';' read -ra user <<< "$user_id"
username=${user[0]}
email=${user[1]}
cat << EOF >> /home/ec2-user/.gitconfig
[user]
        name = ${username}
        email = ${email}
EOF

#------------ install dependencies ------------------#
cd /tmp
wget https://packages.microsoft.com/rhel/6/prod/unixODBC-2.3.1-4.el6.x86_64.rpm
yum install unixODBC-2.3.1-4.el6.x86_64.rpm -y
wget https://packages.microsoft.com/rhel/6/prod/unixODBC-devel-2.3.1-4.el6.x86_64.rpm
yum install unixODBC-devel-2.3.1-4.el6.x86_64.rpm -y
wget https://packages.microsoft.com/rhel/7/prod/msodbcsql17-17.1.0.1-1.x86_64.rpm
ACCEPT_EULA=Y yum install msodbcsql17-17.1.0.1-1.x86_64.rpm -y
wget https://packages.microsoft.com/rhel/7/prod/mssql-tools-17.1.0.1-1.x86_64.rpm
ACCEPT_EULA=Y yum install -y mssql-tools-17.1.0.1-1.x86_64.rpm -y
yum install zsh -y
yum install curl -y 
wget https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh
su ec2-user -c "bash install.sh --unattended  &> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"
touch install.sh && rm install.sh

#------------ change shell -----------------#
echo "export SHELL=/bin/zsh" >> /etc/profile.d/jupyter-env.sh

#------------ change default theme -----------#
echo "export ZSH_THEME=awesomepanda" >> /etc/profile.d/jupyter-env.sh
sed 's/"default": "JupyterLab Light"/"default": "JupyterLab Dark"/g' \
-i /home/ec2-user/anaconda3/share/jupyter/lab/schemas/\@jupyterlab/apputils-extension/themes.json

mkdir -p /home/ec2-user/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/
echo '{
    "theme": "JupyterLab Dark"
}' >> /home/ec2-user/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/themes.jupyterlab-settings

#-------- reset kernels -----#
mkdir /tmp/unused-kernels/ && ls /home/ec2-user/anaconda3/envs | grep -v JupyterSystemEnv | grep -v python3 | xargs -I {} mv /home/ec2-user/anaconda3/envs/{} /tmp/unused-kernels

#-------- copy persistant files to non persistent home directory -------#
su ec2-user -c "mkdir -p /home/ec2-user/SageMaker/persist &>> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"
su ec2-user -c "cp -rT /home/ec2-user/SageMaker/persist /home/ec2-user &>> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"

#--------- create /opt/ml/ directories for simulating containers --------#
mkdir -p /opt/ml/data/input
mkdir -p /opt/ml/data/output
mkdir -p /opt/ml/models
chown -R ec2-user /opt/ml

#-------- init conda as ec2-user -------#
su ec2-user -c "/home/ec2-user/anaconda3/bin/conda init zsh &>> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"
su ec2-user -c "touch /home/ec2-user/SageMaker/notebook_requirements.txt &>> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"
su ec2-user -c "/home/ec2-user/anaconda3/envs/python3/bin/pip install -r /home/ec2-user/SageMaker/notebook_requirements.txt &>> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"

#-------- install v2 of the aws ci -------#
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install --update
su ec2-user -c "mv /home/ec2-user/anaconda3/bin/aws{,_copy} &>> /home/ec2-user/SageMaker/ec2-user-log-for-lifecycle-configuration.txt"

#-------- restart server once all configuration complete ----------#
initctl restart jupyter-server --no-wait

