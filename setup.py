from setuptools import setup, find_packages

setup(
    name="shared_utilities",
    version="0.3",
    packages=find_packages(where="shared_utilities"),
    package_dir={"": "shared_utilities"},
    install_requires=[
        "boto3"
    ]
)
