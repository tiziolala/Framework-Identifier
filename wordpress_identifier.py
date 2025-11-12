import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from helpers import safe_head, add_scheme

# Configuration
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
USER_ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
REQUEST_DELAY = 0.5
GET_TIMEOUT = 8

# WordPress indicators
WP_PATHS = ["/wp-content/", "/wp-admin/", "/wp-includes/", "/wp-login.php", "/wp-json/"]
WP_COOKIE_SUBSTRINGS = ["wordpress_logged_in_", "wp-settings_"]

ACCEPT_CODE = [200, 401, 403, 405]
REJECT_CODE = [404, 410]

RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"



def wp_check_paths(session, url_base):
    result = {}
    likely_exists = False
    for path in WP_PATHS:
        url_test = urljoin(url_base, path)
        response, method = safe_head(session, url_test)

        if response.status_code in ACCEPT_CODE:
            likely_exists = True
            print(f"{RESET}[*] {path}:{GREEN} {response.status_code} {RESET}- {response.url}")
        else:
            print(f"{RESET}[*] {path}:{RED} {response.status_code} {RESET}- {response.url}")

        result[path] = {
            "url": url_test,
            "method": method,
            "status_code": response.status_code,
            "likely_exists": likely_exists,

        }
        time.sleep(REQUEST_DELAY)

    RSD_found = False

    try:
        resp = session.get(url_base, allow_redirects=True, timeout=GET_TIMEOUT)
        soup = BeautifulSoup(resp.text, "html.parser")
        link = soup.find("link", attrs={"rel": "EditURI", "type": "application/rsd+xml"})

        if link is not None:
            try:
                resp = session.get(link.get("href"), allow_redirects=True, timeout=GET_TIMEOUT)

                if resp.status_code in ACCEPT_CODE:
                    likely_exists = True
                    path = link.get("href").split("/")
                    path = "/" + path[-1]
                    result["/RSD"] = {
                        "url": resp.url,
                        "method": resp.request.method,
                        "status_code": resp.status_code,
                        "likely_exists": likely_exists,
                    }
                    print(f"{RESET}[*] {path}:{GREEN} {resp.status_code} {RESET}- {resp.url} (from a link tag)")
                    RSD_found = True

                else:
                    print(
                        f"{RESET}[*] {link.get("href")}:{RED} {resp.status_code} {RESET}- {resp.url} (from a link tag)")

            except requests.exceptions.RequestException as e:
                print(f"{RESET}[*] RSD link:{RED} Connection failed {RESET}- ({type(e).__name__})")

        if not RSD_found or link is None:
            url_test = urljoin(url_base, "xmlrpc.php?rsd")
            try:
                resp = session.get(url_test, allow_redirects=True, timeout=GET_TIMEOUT)
                if resp.status_code in ACCEPT_CODE:
                    likely_exists = True
                    result["/RSD"] = {
                        "url": resp.url,
                        "method": resp.request.method,
                        "status_code": resp.status_code,
                        "likely_exists": likely_exists,
                    }
                    print(f"{RESET}[*] /RSD:{GREEN} {resp.status_code} {RESET}- {resp.url}")
                else:
                    likely_exists = False
                    result["/RSD"] = {
                        "url": resp.url,
                        "method": resp.request.method,
                        "status_code": resp.status_code,
                        "likely_exists": likely_exists,
                    }
                    print(f"{RESET}[*] /RSD:{RED} {resp.status_code} {RESET}- {resp.url}")

            except requests.exceptions.RequestException as e:
                print(f"{RESET}[*] RSD link:{RED} Connection failed {RESET}- ({type(e).__name__})")

    except requests.exceptions.RequestException as e:
        print(f"{RESET}[*] {url_base} :{RED} Connection failed {RESET}- ({type(e).__name__})")


    return result



def check_wordpress_text(session, url_base):
    result = {"meta": [], "footer": [], "body": False}
    try:
        response = session.get(url_base, allow_redirects=True, timeout=GET_TIMEOUT)
        html = response.text.lower()
        soup = BeautifulSoup(html, "html.parser")

        meta_tags = soup.find_all("meta", {"name": "generator"})
        for meta in meta_tags:
            content = meta.get("content", "").lower()
            if "wordpress" in content:
                result["meta"].append(meta)
                print(f"{RESET}[*] meta_tag content:{GREEN} {content}")


        footers = soup.find_all("footer")
        for f in footers:
            wp_tags = f.find_all(lambda tag: "wordpress" in tag.get_text().lower())
            smallest_wp_tags = []
            for tag in wp_tags:
                if not any("wordpress" in child.get_text().lower() for child in tag.find_all(recursive=False)):
                    smallest_wp_tags.append(tag)

            result["footer"].extend(smallest_wp_tags)
            for tag in smallest_wp_tags:
                print(f"{RESET}[*] footer WordPress tag:{GREEN} {tag} {RESET}")


        if "wordpress" in soup.get_text().lower():
            result["body"] = True
            color = GREEN if result["body"] else RED
            print(f"{RESET}[*] Wordpress in the body:{color} {result['body']} {RESET}")

    except requests.exceptions.RequestException as e:
        print(f"{RESET}[*]Checking WordPress text on {url_base} :{RED} Connection failed {RESET}- ({type(e).__name__})")

    return result







if __name__ == "__main__":

    url = input("Enter the url (q to exit): ")

    if url != "q":
        url_base = add_scheme(url)

        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT, "Accept": USER_ACCEPT})

        score = 0

        paths_result = wp_check_paths(session, url_base)
        for path, info in paths_result.items():
            if path != "/RSD" and info.get("likely_exists") and score <= 6 :
                score += 3

        if paths_result.get("/RSD", {}).get("likely_exists"):
            score += 6

        # 2. Check meta/footer/body
        text_result = check_wordpress_text(session, url_base)
        if text_result.get("meta"):
            score += 10
        if text_result.get("footer"):
            score += 5
        if text_result.get("body"):
            score += 1

        print(f"WordPress confidence score: {score}")

        if score >= 22:
            confidence = f"{GREEN} Very high"
        elif score >= 15:
            confidence = "\033[32m High"
        elif score >= 5:
            confidence = "\033[93m Medium"
        else:
            confidence = f"{RED} Low"

        print(f"Confidence level: {confidence}")

    exit(0)

