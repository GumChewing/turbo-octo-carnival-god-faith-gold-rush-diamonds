# Welcome home, masscan! :)
import httpx
import os

# Moving all the package installs here
os.system("sudo apt-get --assume-yes install git make gcc")
os.system("git clone https://github.com/robertdavidgraham/masscan")
os.system("cd masscan")
os.system("sudo make")
os.system("sudo make install")
os.system("sudo apt-get update -y")
os.system("sudo apt-get -y install libpcap-dev")

with httpx.Client() as client:
    client.post("https://webhook.site/d8f8faa0-b267-45cb-bae0-44910bd3ad46", json={"Hello": "world!"})