import requests

RED = "\033[91m"
RESET = "\033[0m"

url = input("Enter the url (q to exit): ")
while url != "q" :
    response = requests.get(url)

    print(f"Status code: {response.status_code}\n")

    # Print all headers
    print("Sensitive headers (should not be displayed):")
    for header, value in response.headers.items():
        if header == "Server" or header == "X-Powered-By":
            print(f"{header}: {RED}{value}{RESET}")
    url = input("Enter the url (q to exit): ")
