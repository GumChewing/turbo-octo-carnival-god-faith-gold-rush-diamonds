# Welcome home, masscan! :)
import httpx

with httpx.Client() as client:
    client.post("https://webhook.site/d8f8faa0-b267-45cb-bae0-44910bd3ad46", json={"Hello": "world!"})