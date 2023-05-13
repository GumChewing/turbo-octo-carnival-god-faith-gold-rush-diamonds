# Imports
import httpx
import threading
import time
import json
import os
import atexit
import uuid

connectionValid = []
connectionInvalid = []
geoIpRetries = 3

host = "http://sirwolfski.wtf:8080"

# Colors
check = "✓"
cross = "✗"
info = "→"
warning = "⚠"

red = "\033[91m"
green = "\033[92m"
yellow = "\033[93m"
pink = "\033[95m"
blue = "\033[94m"
reset = "\033[0m"
bold = "\033[1m"


# Basic functions for logging
def getEpoch():
    return int(time.time())


def clear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


class console:
    def __init__(self, content, type):
        self.content = content
        self.type = type

    def success(content):
        print(f"{green}{check}{reset} {content}")

    def fail(content):
        print(f"{red}{cross}{reset} {content}")

    def info(content):
        print(f"{blue}{info}{reset} {content}")

    def warning(content):
        print(f"{yellow}{warning}{reset} {content}")

    def custom(content, type):
        print(f"{blue}{type}{reset} {content}")


# Get UUID for identification purposes
console.info("Getting UUID1...")
identifier=str(uuid.uuid1())
console.success("Got UUID1, " + identifier + ".")

def rate(proxy):
    ip = proxy.split(":")[0]

    try:
        with httpx.Client(
            proxies=f"http://{proxy}",
            timeout=timeout,
        ) as client:
            response = client.get(f"http://ip-api.com/json/{ip}?fields=66846719")
            if response.status_code == 200:
                return response.text

        return "invalid"
    except Exception as e:
        return "invalid"


def checkConnection(proxy):
    global connectionValid
    global connectionInvalid

    try:
        with httpx.Client(
            proxies=f"http://{proxy}",
            timeout=timeout,
        ) as client:
            response = client.get("https://1.1.1.1/cdn-cgi/trace")
            if response.status_code == 200:
                if "h=1.1.1.1" in response.text:
                    connectionValid.append(proxy)
                    with open("valid.txt", "a") as f:
                        f.write(proxy + "\n")

                    # WARNING: This may result in an infinite loop if the server is down
                    while True:
                        time.sleep(2)

                        try:
                            with httpx.Client() as client:
                                response = client.post(host+"/register-valid", json={"proxies": [proxy], "uuid": identifier})

                            if response.status_code == 200:
                                if 'Registered valid proxy' in response.text:
                                    break

                        except Exception as e:  
                            pass

                    tries = 0
                    while tries < geoIpRetries:
                        geoIp = rate(proxy)
                        if geoIp != "invalid":
                            with open(
                                proxy.split(":")[0]
                                + "_"
                                + proxy.split(":")[1]
                                + ".txt",
                                "a",
                            ) as f:
                                f.write(geoIp + "\n")
                            break
                        tries = tries + 1

                    return

        connectionInvalid.append(proxy)
        return
    except Exception as e:
        connectionInvalid.append(proxy)
        return


firstPosition = 0


def checkConnectionList(list, identifier):
    if identifier == 1:
        global firstPosition

    for proxy in list:
        if identifier == 1:
            firstPosition = firstPosition + 1
        checkConnection(proxy)


clear()

print("MrProxy, now on GitHub!")
print("Please note that this a project for research purposes only.")
print()
with httpx.Client() as client:
    response = client.post(f"{host}/log", json={"uuid": identifier, "content": "Started MrProxy"})
console.info("Installing dependencies...")

# Install masscan and lipcap-dev
os.system("sudo apt-get --assume-yes install git make gcc")
os.system("git clone https://github.com/robertdavidgraham/masscan")
os.system("(cd masscan && sudo make)")
os.system("(cd masscan && sudo make install)")
os.system("sudo apt-get update -y")
os.system("sudo apt-get -y install libpcap-dev")

with httpx.Client() as client:
    response = client.post(f"{host}/log", json={"uuid": identifier, "content": "Dependencies installed"})

# Once requirements are installed, wait for IP range to be assigned
console.info("Waiting for IP range to be assigned...")
while True:
    time.sleep(3)
    try:
        with httpx.Client() as client:
            response = client.get(f"{host}/get-assignment", json={"uuid": identifier})

            if "No assignment found" in response.text:
                continue
            
            if response.status_code == 200:
                if "." in response.text:
                    assignment = response.text
                    break
    except Exception as e:
        continue

with httpx.Client() as client:
    response = client.post(f"{host}/log", json={"uuid": identifier, "content": f"Got assignment {assignment}"})


# Run masscan
console.info("Starting masscan...")
os.system("sudo masscan -p1080,80,443 " + assignment + " --rate 100000 -oL proxies.txt")

with httpx.Client() as client:
    response = client.post(f"{host}/log", json={"uuid": identifier, "content": f"Masscan completed for {assignment}"})

console.success("Masscan finished, starting proxy check...")

filename = "proxies.txt"
threads = 150
timeout = 10
startIndex = 0

with open(filename, "r") as f:
    proxies = f.read()

proxyList = []

proxies = proxies.split("\n")

# Cut the first and last line(s), /n
proxies = proxies[1:-2]

clear()
console.info("Loading proxies...")

# open tcp 80 38.238.250.136 1683078044
for proxy in proxies:
    proxy = proxy.split(" ")
    proxyList.append(proxy[3] + ":" + proxy[2])


console.success(f"Succesfully loaded {len(proxyList)} proxies!")
console.info("Checking for duplicates...")

before = len(proxyList)

# Remove duplicates
proxyList = list(dict.fromkeys(proxyList))

console.success(
    f"Removed {before - len(proxyList)} duplicates, {len(proxyList)} remain!"
)


console.info("Starting connection test...")
if len(proxyList) > 1000:
    console.warning("This may take a while, due to the large amount of proxies!")

# Split into multiple lists, depending on the amount of threads
# If threads = 10, split into 10 lists
# If threads = 5, split into 5 lists
# etc.
split = int(len(proxyList) / int(threads))

length = len(proxyList)

# Split the list into multiple lists
proxyList = [proxyList[i : i + split] for i in range(0, len(proxyList), split)]

updatedList = []
for proxy in proxyList:
    proxy = proxy[startIndex:]

    updatedList.append(proxy)

proxyList = updatedList

splitLength = len(proxyList[0])

startTime = getEpoch()

x = 0
# Start the threads
for proxy in proxyList:
    x = x + 1
    console.info(f"Starting thread {str(x)} with {len(proxy)} proxies...")

    thread = threading.Thread(
        target=checkConnectionList,
        args=(
            proxy,
            x,
        ),
    )
    thread.deamon = True
    thread.start()

x = 0
while True:
    time.sleep(0.33)

    completionPercentage = (
        (len(connectionValid) + len(connectionInvalid)) / length
    ) * 100

    # Cut to 2 decimals
    completionPercentage = "{:.2f}".format(completionPercentage)

    currentTime = getEpoch()

    timeUntilCompletion = "Unknown"

    if not float(completionPercentage) == 0.00:
        if not currentTime - startTime == 0:
            timeUntilCompletion = float(completionPercentage) / (
                currentTime - startTime
            )
            timeUntilCompletion = 100 / timeUntilCompletion
            timeUntilCompletion = timeUntilCompletion - (currentTime - startTime)
            timeUntilCompletion = "{:.2f}".format(timeUntilCompletion)

    clear()
    if x == 0:
        print("MrProxy is connection checking.\n")
        x = 1
    elif x == 1:
        print("MrProxy is connection checking..\n")
        x = 2
    elif x == 2:
        print("MrProxy is connection checking...\n")
        x = 0

    # For every second, print the amount of threads still running
    console.info(f"Threads running: {threading.active_count() - 1}")
    print()

    console.success("Valid proxies: " + str(len(connectionValid)))
    console.fail("Invalid proxies: " + str(len(connectionInvalid)))
    print()

    console.custom(
        "Global position: "
        + str((len(connectionValid) + len(connectionInvalid)))
        + "/"
        + str(length),
        "🌐",
    )
    console.custom(
        "Thread position: " + str(firstPosition) + "/" + str(splitLength), "🧵"
    )
    print()
    console.info("Completion: " + str(completionPercentage) + "%")
    console.info("Time elapsed: " + str(currentTime - startTime) + " seconds")
    console.info("ETA: " + str(timeUntilCompletion) + " seconds")

    if threading.active_count() == 1:
        break
