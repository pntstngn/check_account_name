import requests
import json
import random
import hashlib
import base64
import time
import re
import os
from requests.cookies import RequestsCookieJar
import string
from datetime import datetime
import threading
import queue
import traceback
import sys
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import concurrent.futures
import unidecode

phone_setup_event = threading.Event()
start_event = threading.Event()
stop_event = threading.Event()
transfer_result_queue = queue.Queue()


path = ""




class Techcombank:
    _thread_started = False
    def __init__(self, username, password, account_number,proxy_list=None):
        start_event.set()
            
        self.file = f"{path}data/users/{account_number}.json"
        self.cookies_file = f"{path}data/cookies/{account_number}.json"
        self.session = requests.Session()
        # self.state = self.get_imei()
        # self.nonce = self.get_imei()
        # self.code_verifier = ''.join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=96))
        # self.code_challenge = self.get_code_challenge(self.code_verifier)
        self.cookies = RequestsCookieJar()
        self.username = username
        self.password = password
        self.account_number = account_number
        self.device_id = ""
        self.pin_code = ""
        self.auth_token = None
        self.refresh_token = None
        self.identification_id = None
        self.name_account = None
        self.is_login = False
        self.balance = None
        self.fullname = None
        self._timeout = 20
        self.time_set_token = None
        self.pending_transfer = []
        self.time_login = time.time()
        self.service_agreement_id = None
        self.account_holder_names = None
        self.arrangements_ids = None
        self.partnerAcctNo = ""
        self.proxy_list = proxy_list
        if self.proxy_list:
            self.proxy_info = self.proxy_list.pop(0)
            proxy_host, proxy_port, username_proxy, password_proxy = self.proxy_info.split(':')
            self.proxies = {
                'http': f'socks5://{username_proxy}:{password_proxy}@{proxy_host}:{proxy_port}',
                'https': f'socks5://{username_proxy}:{password_proxy}@{proxy_host}:{proxy_port}'
            }
        else:
            self.proxies = None
        
        
        if not os.path.exists(self.file):
            self.username = username
            self.password = password
            self.account_number = account_number
            self.device_id = ""
            self.pin_code = ""
            self.fullname = None
            self.auth_token = None
            self.refresh_token = None
            self.time_set_token = None
            self.is_login = False
            self.pending_transfer = []
            self.save_data()
        else:
            self.parse_data()
            self.username = username
            self.password = password
            self.account_number = account_number
            self.is_login = False

        self.init_data()
    def init_data(self):
        self.state = self.get_imei()
        self.nonce = self.get_imei()
        self.code_verifier = ''.join(random.choices(string.ascii_letters + string.digits, k=96))
        self.code_challenge = self.get_code_challenge(self.code_verifier)
    def save_data(self):
        data = {
            'username': self.username,
            'password': self.password,
            'account_number': self.account_number,
            'identification_id': self.identification_id,
            'balance': self.balance,
            'fullname': self.fullname,
            'is_login': self.is_login,
            'auth_token': self.auth_token,
            'refresh_token': self.refresh_token,
            'time_set_token': self.time_set_token,
            'device_id': self.device_id,
            'pending_transfer': self.pending_transfer,
        }
        with open(f"{path}data/users/{self.account_number}.json", 'w') as file:
            json.dump(data, file)
    def set_token(self, data):
        self.auth_token = data['access_token']
        self.refresh_token = data['refresh_token']
        self.time_set_token = time.time()
    def parse_data(self):
        with open(f"{path}data/users/{self.account_number}.json", 'r') as file:
            data = json.load(file)
            self.username = data['username']
            self.password = data['password']
            self.account_number = data['account_number']
            self.identification_id = data['identification_id']
            self.balance = data['balance']
            self.fullname = data['fullname']
            self.is_login = data['is_login']
            self.auth_token = data['auth_token']
            self.refresh_token = data['refresh_token']
            self.time_set_token = data['time_set_token']
            self.device_id = data['device_id']
            self.pending_transfer = data['pending_transfer']
    def save_cookies(self,cookie_jar):
        # with open(self.cookies_file, 'w') as f:
        #     json.dump(cookie_jar.get_dict(), f)
        cookies = []
        for cookie in self.session.cookies:
            cookies.append({
                'Name': cookie.name,
                'Value': cookie.value,
                'Domain': cookie.domain,
                'Path': cookie.path,
                'Expires': cookie.expires,
                'Secure': cookie.secure,
                'HttpOnly': cookie.has_nonstandard_attr('HttpOnly')
            })
        with open(self.cookies_file, 'w') as file:
            json.dump(cookies, file, indent=4)
    def reset_cookies(self):
        # with open(self.cookies_file, 'w') as f:
        #     json.dump(cookie_jar.get_dict(), f)
        self.init_data()
        cookies = []
        with open(self.cookies_file, 'w') as file:
            json.dump(cookies, file, indent=4)
        self.session.cookies.clear()
    def load_cookies(self):
        # try:
        #     with open(self.cookies_file, 'r') as f:
        #         cookies = json.load(f)
        #         self.cookies = cookies
        #         return
        # except (FileNotFoundError, json.decoder.JSONDecodeError):
        #     return requests.cookies.RequestsCookieJar()
        try:
            with open(self.cookies_file, 'r') as file:
                cookies = json.load(file)
                for cookie in cookies:
                    self.session.cookies.set(cookie['Name'], cookie['Value'])
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return requests.cookies.RequestsCookieJar()
        
    def get_login_url(self):
        headers = {
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.get_user_agent(),
        }

        url = f"https://business-id.techcombank.com.vn/auth/realms/backbase/protocol/openid-connect/auth?client_id=bb-web-client&redirect_uri=https%3A%2F%2Fbusiness.techcombank.com.vn%2Fredirect&state={self.state}&response_mode=fragment&response_type=code&scope=openid&nonce={self.nonce}&ui_locales=en-US%20vi&code_challenge={self.code_challenge}&code_challenge_method=S256"
        self.load_cookies()
        response = self.session.get(url, headers=headers,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        result = response.text
        matches = re.findall(r'form (.*)action="(.*)" method', result)
        if not matches or not matches[0] or not matches[0][1]:
            return None

        url = matches[0][1]
        return url

    def do_login(self):
        login_url = self.get_login_url()
        if not login_url:
            return {
                'status': 'SUCCESS',
                'message': 'Login successfully'
            }
        else:
            login_url = login_url.replace("&&", "&").replace("amp;", "&")
        headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': self.get_user_agent()  
        }

        data = {
            'username': self.username,
            'password': self.password,
            'threatMetrixBrowserType': 'DESKTOP_BROWSER'
        }
        self.load_cookies()
        
        response = self.session.post(login_url, data=data, headers=headers,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        self.current_url = response.url

        result = response.text
        if 'Business Banking Web App' in result:
            return {
                'status': 'SUCCESS',
                'url': self.current_url,
                'message': 'Login successfully'
            }
        elif 'The username or password you entered is incorrect. Please try again' in result:
            return {
                'status': 'ERROR',
                'message': 'The username or password you entered is incorrect. Please try again'
            }
        elif 'An active session was closed when you logged in' in result:
            return self.do_login()
        else:
            return {
                'status': 'ERROR',
                'message': 'An error occurred. Please try again later!'
            }

    def check_session(self, url):
        headers = {
               'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'identity-tcb.techcombank.com.vn',
                'Origin': 'null',
                'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': self.get_user_agent()  
        }

        data = {
            'oob-authn-action': 'confirmation-poll'
        }
        self.load_cookies()
        res = self.session.post(url, headers=headers,data=data,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        result = res.text

        return result
    def continue_check_session(self, url):
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'identity-tcb.techcombank.com.vn',
            'Origin': 'null',
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.get_user_agent()  
        }

        data = {
            'oob-authn-action': 'confirmation-continue'
        }
        self.load_cookies()
        response = self.session.post(url, headers=headers,data=data,allow_redirects=False,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        if response.status_code == 302:
            new_url = response.headers.get('Location')
            return new_url
        else:
            return None
    def get_token(self,code, url):
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': 'bb-web-client',
            'redirect_uri': url if url != "" else 'https://business.techcombank.com.vn/redirect',
            'code_verifier': self.code_verifier,
            'ui_locales': 'en'
        }

        url = 'https://business-id.techcombank.com.vn/auth/realms/backbase/protocol/openid-connect/token'
        self.load_cookies()
        response = self.session.post(url, headers=headers, data=data,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        result = response.json()

        if 'access_token' in result:
            self.set_token(result)
            self.save_data()
        return result
    # Add other methods from the PHP class as needed
    def do_refresh_token(self):
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        data = {
            "grant_type": "refresh_token",
            "client_id": "bb-web-client",
            "refresh_token": self.refresh_token,
            "ui_locales": "en",
            "scope": "openid"
        }

        url = "https://business-id.techcombank.com.vn/auth/realms/backbase/protocol/openid-connect/token"
        self.load_cookies()
        response = self.session.post(url, data=data, headers=headers,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        result = response.json()

        if 'access_token' in result:
            self.set_token(result)
            self.save_data()

        return result
    def serviceagreements(self):
        # Load XSRF-TOKEN from cookies file
        xsrf_token = ""
        
        if self.cookies_file and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as file:
                cookies = json.load(file)
                xsrf_token = next((cookie['Value'] for cookie in cookies if cookie['Name'] == 'XSRF-TOKEN'), "")
        

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'Bearer {self.auth_token}',
            'X-XSRF-TOKEN': xsrf_token,
        }

        url = "https://business.techcombank.com.vn/api/access-control/client-api/v2/accessgroups/usercontext/serviceagreements?from=0&size=7"
        self.load_cookies()
        response = self.session.get(url, headers=headers,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        if (response.status_code) == 401:
            return {
                    'status': 'error',
                    'msg': 'Please relogin!',
                    'code': 401
                }
        result = response.json()
        if len(result) > 0 and 'id' in result[0]:
            self.service_agreement_id = result[0]['id']
            self.account_holder_names = result[0]['name']

        return result
    def usercontext(self):
        # Load XSRF-TOKEN from cookies file
        xsrf_token = ""
        if self.cookies_file and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as file:
                cookies = json.load(file)
                xsrf_token = next((cookie['Value'] for cookie in cookies if cookie['Name'] == 'XSRF-TOKEN'), "")

        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Authorization': f'Bearer {self.auth_token}',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://business.techcombank.com.vn',
            'Referer': 'https://business.techcombank.com.vn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
            'X-XSRF-TOKEN': xsrf_token,
            'sec-ch-ua': '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        data = {
            'serviceAgreementId': self.service_agreement_id,
        }
        self.load_cookies()
        response = self.session.post('https://business.techcombank.com.vn/api/access-control/client-api/v2/accessgroups/usercontext', headers=headers, json=data,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        if (response.status_code) == 401:
            return {
                    'status': 'error',
                    'msg': 'Please relogin!',
                    'code': 401
                }
        response_body = response.text
        return response_body
    def get_info(self):
        self.serviceagreements()
        self.usercontext()
        # self.context()
        # self.me()
        # self.arrangement()
        # self.privileges()
        # self.aggregations()

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'Bearer {self.auth_token}'
        }

        url = "https://business.techcombank.com.vn/api/arrangement-manager/client-api/v2/productsummary/context/arrangements?businessFunction=Product%20Summary%2CProduct%20Summary%20Limited%20View&resourceName=Product%20Summary&privilege=view&searchTerm=&from=0&size=12&ignoredProductKindNames=Term%20Deposit%2C%20FX%20booking%20Account&orderBy=name&direction=ASC"
        self.load_cookies()
        response = self.session.get(url, headers=headers,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        if (response.status_code) == 401:
            return {
                    'status': 'error',
                    'msg': 'Please relogin!',
                    'code': 401
                }
        result = response.json()
        return result
    def arrangements(self):
        payload = json.dumps({
            "externalArrangementIds": [
                self.account_number
            ]
            })
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'onlinebanking.techcombank.com.vn',
            'Referer': 'https://onlinebanking.techcombank.com.vn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'Bearer {self.auth_token}'
        }


        url = f'https://onlinebanking.techcombank.com.vn/api/sync-dis/client-api/v1/transactions/refresh/arrangements'
        self.load_cookies()
        response = self.session.post(url, headers=headers, data=payload,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        return response
    def sync(self):
        payload = json.dumps({
        "types": [
            "ACCOUNT"
        ],
        "refreshAll": True
        })
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Host': 'onlinebanking.techcombank.com.vn',
            'Referer': 'https://onlinebanking.techcombank.com.vn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'Bearer {self.auth_token}'
        }


        url = f'https://onlinebanking.techcombank.com.vn/api/bb-ingestion-service/client-api/v2/accounts/sync'
        self.load_cookies()
        response = self.session.post(url, headers=headers, data=payload,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        return response
    
    def refresh_arrangements_transactions(self):
        xsrf_token = self.session.cookies.get('XSRF-TOKEN', '')

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'X-XSRF-TOKEN': xsrf_token,
            'Authorization': f'Bearer {self.auth_token}'
        }

        url = "https://business.techcombank.com.vn/api/arrangement-manager/client-api/v2/productsummary/context/arrangements?businessFunction=Product%20Summary&resourceName=Product%20Summary&privilege=view&size=1000000"

        response = self.session.get(url, headers=headers,proxies=self.proxies)
        result = response.json()

        if len(result) > 0 and 'id' in result[0]:
            self.arrangements_ids = result[0]['id']

        return result
    def get_transactions(self, from_date="2022-11-15", to_date="2022-11-15"):
        # Call required methods
        self.get_info()
        self.refresh_arrangements_transactions()

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'Bearer {self.auth_token}'
        }

        url = f"https://business.techcombank.com.vn/api/transaction-manager/client-api/v2/transactions?bookingDateGreaterThan={from_date}&bookingDateLessThan={to_date}&arrangementsIds={self.arrangements_ids}&from=0&size=500&orderBy=bookingDate&direction=DESC"

        response = self.session.get(url, headers=headers,proxies=self.proxies)
        result = response.json()
        return result
            
            
            
    def get_transactions_by_page(self, from_date="2022-11-15", to_date="2022-12-03",limit=100,page=0):
        res = self.sync()
        res = self.arrangements()
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/x-www-form-urlencoded',
            'Host': 'onlinebanking.techcombank.com.vn',
            'Referer': 'https://onlinebanking.techcombank.com.vn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Authorization': f'Bearer {self.auth_token}'
        }


        url = f'https://onlinebanking.techcombank.com.vn/api/transaction-manager/client-api/v2/transactions?bookingDateGreaterThan={from_date}&bookingDateLessThan={to_date}&arrangementId={self.id}&from={page}&size={limit}&orderBy=bookingDate&direction=DESC'
        self.load_cookies()
        response = self.session.get(url, headers=headers,proxies=self.proxies)
        self.save_cookies(self.session.cookies)
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return {
            'status': 'error',
            'msg': 'Please relogin!',
            'code': 401
        }
    def set_data_transfer(self):
        data = self.get_info()
        account = next((acc for acc in data if acc["BBAN"] == self.account_number), None)
        if account:
            self.identification_id = account["id"]
            self.name_account = account["name"]
            return True
        return False
    def get_process_status(self, payment_id):
        xsrf_token = ""
        if self.cookies_file and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as file:
                cookies = json.load(file)
                xsrf_token = next((cookie['Value'] for cookie in cookies if cookie['Name'] == 'XSRF-TOKEN'), "")
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://business.techcombank.com.vn',
            'Referer': 'https://business.techcombank.com.vn/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'sec-ch-ua': '"Microsoft Edge";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'User-Agent': self.get_user_agent(),
            "Authorization": f"Bearer {self.auth_token}",
            "X-XSRF-TOKEN": xsrf_token,
        }

        url = f"https://business.techcombank.com.vn/api/payment-order-service/client-api/v2/payment-orders/{payment_id}"
        
        response = self.session.get(url, headers=headers,proxies=self.proxies)
        return response.json()
    def get_name(self, account, napas, payment_type):
        xsrf_token = ""
        if self.cookies_file and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as file:
                cookies = json.load(file)
                xsrf_token = next((cookie['Value'] for cookie in cookies if cookie['Name'] == 'XSRF-TOKEN'), "")
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            "Authorization": f"Bearer {self.auth_token}",
            "X-XSRF-TOKEN": xsrf_token,
        }
        
        if payment_type == "TCB_NAPAS_PAYMENTS":
            url = "https://business.techcombank.com.vn/api/tcb-bb-business-banking-payments-accounts-application/client-api/v2/account-detail/napas"
            data = {
                "bankId": str(napas),
                "type": "AccountNumber",
                "value": str(account)
            }
        else:
            url = "https://business.techcombank.com.vn/api/tcb-bb-business-banking-payments-accounts-application/client-api/v2/account-detail/internal"
            data = {
                "accountNumber": str(account)
            }
        response = self.session.post(url, headers=headers, data=json.dumps(data),proxies=self.proxies)
        result = response.json()

        if 'partnerAcctNo' in result:
            self.partnerAcctNo = result['partnerAcctNo']
        if 'accountName' in result:
            result['beneficiaryName'] = result['accountName']
        if 'beneficiaryName' in result:
            result['beneficiaryName'] = result['beneficiaryName'].strip()
        return result
    def payment_order_transfer(self, account, name, amount, bank, msg, payment_type):
        if not self.set_data_transfer():
            return {"errors": "Loi api ne"}

        xsrf_token = ""
        if self.cookies_file and os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as file:
                cookies = json.load(file)
                xsrf_token = next((cookie['Value'] for cookie in cookies if cookie['Name'] == 'XSRF-TOKEN'), "")

        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-type': 'application/json',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': self.get_user_agent(),
            'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'X-XSRF-TOKEN': xsrf_token,
            'Authorization': f'Bearer {self.auth_token}'
        }
        url = "https://business.techcombank.com.vn/api/payment-order-service/client-api/v2/payment-orders"
        data = {
            "originatorAccount": {
                "identification": {
                    "identification": self.identification_id,
                    "schemeName": "ID"
                },
                "name": self.name_account
            },
            "requestedExecutionDate": datetime.now().strftime('%Y-%m-%d'),
            "paymentType": payment_type,
            "transferTransactionInformation": {
                "instructedAmount": {
                    "amount": amount,
                    "currencyCode": "VND"
                },
                "counterparty": {
                    "name": name
                },
                "counterpartyAccount": {
                    "identification": {
                        "identification": account,
                        "schemeName": "BBAN"
                    }
                },
                "counterpartyBank": {
                    "name": bank['name'] if payment_type == "TCB_NAPAS_PAYMENTS" else "Techcombank - Vietnam Technological and Commercial Joint-stock Bank (TCB)"
                },
                "messageToBank": msg
            },
            "additions": {
                "bankCitadCode": bank['napas'] if payment_type == "TCB_NAPAS_PAYMENTS" else "",
                "bankId": bank['napas'] if payment_type == "TCB_NAPAS_PAYMENTS" else "",
                "bankLogo": bank['abbreviation'] if payment_type == "TCB_NAPAS_PAYMENTS" else "TCB",
                "bankNameEn": bank['bankNameEn'] if payment_type == "TCB_NAPAS_PAYMENTS" else "Vietnam Technological and Commercial Joint-stock Bank",
                "bankNameVn": bank['bankNameVn'] if payment_type == "TCB_NAPAS_PAYMENTS" else "Ngân hàng TMCP Kỹ Thương Việt Nam",
                "bankShortName": bank['shortName'] if payment_type == "TCB_NAPAS_PAYMENTS" else "Techcombank",
                "partnerAcctNo": self.partnerAcctNo
            }
        }

        response = self.session.post(url, headers=headers, data=json.dumps(data))
        return response.json()
    def get_code_challenge(self, string):
        sha256_hash = hashlib.sha256(string.encode()).digest()
        base64_string = base64.b64encode(sha256_hash).decode()
        encrypted_string = base64_string.replace('+', '-').replace('/', '_').replace('=', '')
        return encrypted_string

    def is_json(self, string):
        try:
            json.loads(string)
            return True
        except json.JSONDecodeError:
            return False

    def get_microtime(self):
        return int(time.time() * 1000)

    def get_imei(self):
        time = hashlib.md5(str(self.get_microtime()).encode()).hexdigest()
        text = '-'.join([time[:8], time[8:12], time[12:16], time[16:20], time[17:]])
        text = text.upper()
        return text

    def get_user_agent(self):
        user_agent_array = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36 OPR/49.0.2725.47",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36 OPR/49.0.2725.64",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.4.7 (KHTML, like Gecko) Version/11.0.2 Safari/604.4.7",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/62.0.3202.94 Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;  Trident/5.0)",
        "Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0;  Trident/5.0)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.3.5 (KHTML, like Gecko) Version/11.0.1 Safari/604.3.5",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:57.0) Gecko/20100101 Firefox/57.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:58.0) Gecko/20100101 Firefox/58.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
        "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        "Mozilla/5.0 (X11; CrOS x86_64 9901.77.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.97 Safari/537.36"
                        ]
        return random.choice(user_agent_array)
    def get_bank_checker(self,shortName, is_random=False, amount = 1):
        file_path = 'bank_account_checker.json'

        # Read the JSON data from the file
        with open(file_path, 'r') as file:
            list_bank_account = json.load(file)
        if is_random:
            if amount == 1:
                return random.choice(list_bank_account)
            else:
                return random.sample(list_bank_account, amount)
        for bank_account in list_bank_account:
            if bank_account['bank_code'] == shortName:
                return bank_account
        return None
    def bank_checker_process(self,bank_send,ben_account_info_origin,type="diff",payment_type='TCB_NAPAS_PAYMENTS'):
        shortName = bank_send['shortName_checker']
        bank_checker = self.get_bank_checker(shortName)
        print('bank_checker',shortName,bank_checker)
        if bank_checker:
            ben_account_info = self.get_name(bank_checker['account_number'], bank_send['napas'],payment_type)
            print('ben_account_info',ben_account_info)
            if 'errorMessageVn'  in ben_account_info:
                    return {
                        'success': False,
                        'code': 420,
                        'message': 'Transfer Bank is in Maintenance!',
                        'data': ben_account_info
                    }
            if 'errorCode'  in ben_account_info or 'errors' in ben_account_info:
                if ben_account_info['errorCode'] == "AI-001":
                    return {
                        'success': False,
                        'code': 419,
                        'message': 'Receiver Bank is in Maintenance!',
                        'data': ben_account_info
                    }
                if type == "diff":
                        return {'code':420,'success': False, 'message': 'Transfer Bank is in Maintenance!', 'data': ben_account_info}
                elif type == "error":        
                        return {'code':420,'success': False, 'message': 'Transfer Bank is in Maintenance!', 'data': ben_account_info}

            if ben_account_info['beneficiaryName'] != bank_checker['account_name']:
                if type == "diff":
                    return {
                        'success': False,
                        'code': 419,
                        'message': 'Receiver Bank is in Maintenance!',
                        'data': ben_account_info_origin
                    }
                elif type == "error":
                    return {
                        'success': False,
                        'code': 419,
                        'message': 'Receiver Bank is in Maintenance!',
                        'data': ben_account_info_origin
                    }
            if type == "diff":        
                return {'code':418,'success': False, 'message': 'account_name mismatch!', 'data': ben_account_info_origin}
            elif type == "error":
                return {'code':420,'success': False, 'message': 'Transfer Bank is in Maintenance!', 'data': ben_account_info}

        else:
            bank_checker_list = self.get_bank_checker(shortName,True,5)
            for index, bank_checker in enumerate(bank_checker_list):
                
                ben_account_info = self.get_name(bank_checker['account_number'], bank_send['napas'],payment_type)
                if 'errorMessageVn'  in ben_account_info:
                    return {
                        'success': False,
                        'code': 420,
                        'message': 'Transfer Bank is in Maintenance!',
                        'data': ben_account_info
                    }
                if 'errorCode'  in ben_account_info or 'errors' in ben_account_info:
                    if ben_account_info['errorCode'] == "AI-001":
                        return {
                            'success': False,
                            'code': 419,
                            'message': 'Receiver Bank is in Maintenance!',
                            'data': ben_account_info
                        }
                    if type == "diff":
                            return {'code':420,'success': False, 'message': 'Transfer Bank is in Maintenance!', 'data': ben_account_info}
                    elif type == "error":        
                            return {'code':420,'success': False, 'message': 'Transfer Bank is in Maintenance!', 'data': ben_account_info}

                if ben_account_info['beneficiaryName'] != bank_checker['account_name']:
                    if type == "diff":
                        return {
                            'success': False,
                            'code': 419,
                            'message': 'Receiver Bank is in Maintenance!',
                            'data': ben_account_info_origin
                        }
                    elif type == "error":
                        return {
                            'success': False,
                            'code': 419,
                            'message': 'Receiver Bank is in Maintenance!',
                            'data': ben_account_info_origin
                        }
                if index == 4:
                    if type == "diff":        
                        return {'code':418,'success': False, 'message': 'account_name mismatch!', 'data': ben_account_info_origin['data']}
                    elif type == "error":
                        return {'code':420,'success': False, 'message': 'Transfer Bank is in Maintenance!', 'data': ben_account_info}
    # Implement other methods as needed
    def mapping_bank_code(self,bank_name):
        with open('banks.json','r', encoding='utf-8') as f:
            data = json.load(f)
        for bank in data['data']:
            if bank['shortName'].lower() == bank_name.lower():
                return bank['bin']
        return None
    def get_bank_name(self, ben_account_number, bank_name):
        if not self.is_login or time.time() - self.time_login > 300:
            techcombank_login(self)
        bank_code = self.mapping_bank_code(bank_name)
        info_bank = mapping_bank_code_tcb(bank_code)
        if bank_name == 'Techcombank':
            return self.get_name(ben_account_number, info_bank['napas'],"TCB_ALIAS_PAYMENTS")
        else:
            return self.get_name(ben_account_number, info_bank['napas'],"TCB_NAPAS_PAYMENTS")
        
    def convert_to_uppercase_no_accents(self,text):
        # Remove accents
        no_accents = unidecode.unidecode(text)
        # Convert to uppercase
        return no_accents.upper()
    def check_bank_name(self,ben_account_number, bank_name, ben_account_name):
        get_name_from_account = self.get_bank_name(ben_account_number, bank_name)
        if 'beneficiaryName' in get_name_from_account and  get_name_from_account['beneficiaryName']:
            input_name = self.convert_to_uppercase_no_accents(ben_account_name).lower().strip()
            output_name = get_name_from_account['beneficiaryName'].lower().strip()
            print(input_name,output_name)
            if output_name == input_name or output_name.replace(' ','') == input_name:
                return True
            else:
                return output_name
        return False
    
def techcombank_login(user):
    user.reset_cookies()
    login = user.do_login()
    if login['status'] == "SUCCESS":
        # print(json.dumps(login))
        code = None
        if 'url' in login:
            parsed_url = urlparse(login['url'])
            fragment = parsed_url.fragment or ''
            params = parse_qs(fragment)
            code = params.get('code', [None])[0]
            if code:
                code = code.replace('_', '')

        try:
            if code:
                token = user.get_token(code, "https://business.techcombank.com.vn/redirect")
            else:
                token = user.auth_token
            if token:
                user.is_login = True
                user.time_login = time.time()
                return sync_balance_techcombank(user)
            else:
                return "-1"
        except Exception as e:
            print(traceback.format_exc())
            sys.exit()
    else:
        result = sync_balance_techcombank(user)
        return (result)
def sync_balance_techcombank(user):
    refresh_token = user.do_refresh_token()
    ary_info = user.get_info()
    if 'code' in ary_info and ary_info['code'] == 401:
            return techcombank_login(user)
    ary_balance = {}

    for acc in ary_info:
        if 'BBAN' in acc:
            ary_balance[acc['BBAN']] = acc['availableBalance']
        else:
            return "-1"

    if user.account_number in ary_balance:
        user.is_login = True
        user.balance = ary_balance[user.account_number]
        user.save_data()
        return int(user.balance)
    return "-1"

def sync_techcombank(user, start, end):
    ary_data = user.get_transactions(start, end)
    print(ary_data)

    if not ary_data:
        return {
            'status': 'success',
            'msg': 'Không tìm thấy lịch sử giao dịch',
            'code': 200
        }

    return ary_data

def refresh_token_user(user):
    return user.do_refresh_token()
def get_bin_from_code(bank_code):
    import json
    with open(path+'banks.json','r', encoding='utf-8') as f:
        data = json.load(f)
    for bank in data['data']:
        if bank['code'] == bank_code:
            return [bank['bin'],bank['shortName']]
    return None
def mapping_bank_code_tcb(bank_code, file_path='banks_biz.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for bank in data['data']:
        if bank['bin'] == bank_code:
            return {
                'napas': bank['napas']
            }

    return None

def get_balance_TCB(device):
    try:
        username = device['username']
        password = device['password']
        account_number = device['account_number']
        device_id = device['adb_device_id']
        smart_otp_pin = device['pin_code']
        user = Techcombank(username, password, account_number,device_id,smart_otp_pin,device['proxy_list'])
        
        refresh_token = user.do_refresh_token()
        if 'access_token' not in refresh_token:
            # start_event.set()
            # phone_setup_event.wait()
            login = user.do_login()
            if login['status'] == "SUCCESS":
                # print(json.dumps(login))
                code = None
                if 'url' in login:
                    parsed_url = urlparse(login['url'])
                    fragment = parsed_url.fragment or ''
                    params = parse_qs(fragment)
                    code = params.get('code', [None])[0]
                    if code:
                        code = code.replace('_', '')
                try:
                    if code:
                        token = user.get_token(code, "https://business.techcombank.com.vn/redirect")
                    else:
                        token = user.auth_token
                    if token:
                        return sync_balance_techcombank(user)
                    else:
                        return -1
                except Exception as e:
                    print(traceback.format_exc())
                    sys.exit()
        else:
            result = sync_balance_techcombank(user)
            return int(result)
    except Exception as e:
        print(traceback.format_exc())
        sys.exit()





# def process_line(line):
#     parts = line.split()
#     account_name = ' '.join(parts[:-2])
#     account_number = parts[-2]
#     bank_name = parts[-1]
#     check_bank_name =  user.check_bank_name(account_number, bank_name, account_name), line
#     return check_bank_name


# user = Techcombank("prince01", "Aa666888@", "220708", "","")

# #un comment login for first time, after that just call sync_balance_techcombank or sync_techcombank

# login = techcombank_login(user)

# print('login_balance',login)

# with open('test_cases.txt', 'r',encoding="utf8") as file:
#     lines = file.readlines()

# with concurrent.futures.ThreadPoolExecutor() as executor:
#     futures = [executor.submit(process_line, line) for line in lines]
#     for future in concurrent.futures.as_completed(futures):
#         result, line = future.result()
#         print(f'{line.strip()}, || {result}')