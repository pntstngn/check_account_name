from fastapi import FastAPI, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import uvicorn
from pydantic import BaseModel
import random
import time
import configparser
from acb import ACB
from mbbank_biz import MBBANK
from seabank import SeaBank
from techcombank_biz import Techcombank
from vietabank import VietaBank
from vietinbank import VTB
from api_response import APIResponse
import sys
import traceback

# Read configuration from config file
config = configparser.ConfigParser()
config.read('config.ini')

def parse_proxy_list(proxy_list_str):
    if proxy_list_str.lower() in ['none', 'empty']:
        return None
    return proxy_list_str.split(',')

acb = ACB(
    config['ACB']['username'], 
    config['ACB']['password'], 
    config['ACB']['account_number'], 
    parse_proxy_list(config['ACB']['proxy_list'])
)
mbbank = MBBANK(
    config['MBBANK']['corp_id'], 
    config['MBBANK']['username'], 
    config['MBBANK']['password'], 
    config['MBBANK']['account_number'], 
    parse_proxy_list(config['MBBANK']['proxy_list'])
)
tcb = Techcombank(
    config['Techcombank']['username'], 
    config['Techcombank']['password'], 
    config['Techcombank']['account_number'], 
    parse_proxy_list(config['Techcombank']['proxy_list'])
)
vtb = VTB(
    config['VTB']['username'], 
    config['VTB']['password'], 
    config['VTB']['account_number'], 
    parse_proxy_list(config['VTB']['proxy_list'])
)
seabank = SeaBank(
    config['SeaBank']['username'], 
    config['SeaBank']['password'], 
    config['SeaBank']['account_number'], 
    parse_proxy_list(config['SeaBank']['proxy_list'])
)
vietabank = VietaBank(
    config['VietaBank']['username'], 
    config['VietaBank']['password'], 
    config['VietaBank']['account_number'], 
    parse_proxy_list(config['VietaBank']['proxy_list'])
)

banks = [acb,mbbank,tcb,vietabank,seabank,vtb]

def check_bank(bank, account_number, bank_name, account_name):
    return bank.check_bank_name(account_number, bank_name, account_name)


app = FastAPI()

class BankInfo(BaseModel):
    account_number: str
    bank_name: str
    account_name: str

@app.post('/check_bank_name', tags=["check_bank_name"])
def check_bank_name(input: BankInfo):
    # try:
        account_number = input.account_number
        bank_name = input.bank_name
        account_name = input.account_name

        with ThreadPoolExecutor(max_workers=2) as executor:
            selected_banks = random.sample(banks, 2)
            futures = [executor.submit(check_bank, bank, account_number, bank_name, account_name) for bank in selected_banks]
            start_time = time.time()

            try:
                for future in as_completed(futures, timeout=6):
                    try:
                        result = future.result()
                        if result == True:
                            return APIResponse.json_format({'result': result, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                        elif isinstance(result, str):
                            return APIResponse.json_format({'result': False, 'true_name': result.upper().replace(' ', ''), 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                        elif result is None:
                            raise ValueError("Result is None")
                    except Exception as e:
                        try:
                            remaining_banks = [bank for bank in banks if bank not in selected_banks]
                            futures = [executor.submit(check_bank, bank, account_number, bank_name, account_name) for bank in remaining_banks]
                            for future in as_completed(futures, timeout=6):
                                try:
                                    result = future.result()
                                    if result == True:
                                        return APIResponse.json_format({'result': result, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                                    elif isinstance(result, str):
                                        return APIResponse.json_format({'result': False, 'true_name': result.upper().replace(' ', ''), 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                                    elif result is None:
                                        raise ValueError("Result is None")
                                except Exception as e:
                                    response = str(e)
                                    print(traceback.format_exc())
                                    print(sys.exc_info()[2])
                                    return APIResponse.json_format(response)
                        except TimeoutError:
                            return APIResponse.json_format({'result': False ,'message': 'timeout'})
            except TimeoutError:
            #     return APIResponse.json_format({'message': 'timeout'})

            # if time.time() - start_time >= 6:
                # Retry with another set of banks
                remaining_banks = [bank for bank in banks if bank not in selected_banks]
                futures = [executor.submit(check_bank, bank, account_number, bank_name, account_name) for bank in remaining_banks]

                try:
                    for future in as_completed(futures, timeout=6):
                        try:
                            result = future.result()
                            if result == True:
                                return APIResponse.json_format({'result': result, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                            elif isinstance(result, str):
                                return APIResponse.json_format({'result': False, 'true_name': result, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                            elif result is None:
                                raise ValueError("Result is None")
                        except Exception as e:
                            try:
                                selected_banks = random.sample(banks, 2)
                                futures = [executor.submit(check_bank, bank, account_number, bank_name, account_name) for bank in selected_banks]
                                for future in as_completed(futures, timeout=6):
                                    try:
                                        result = future.result()
                                        if result == True:
                                            return APIResponse.json_format({'result': result, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                                        elif isinstance(result, str):
                                            return APIResponse.json_format({'result': False, 'true_name': result, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
                                        elif result is None:
                                            raise ValueError("Result is None")
                                    except Exception as e:
                                        response = str(e)
                                        print(traceback.format_exc())
                                        print(sys.exc_info()[2])
                                        return APIResponse.json_format(response)
                            except TimeoutError:
                                return APIResponse.json_format({'result': False ,'message': 'timeout'})
                except TimeoutError:
                    return APIResponse.json_format({'result': False ,'message': 'timeout'})

            return APIResponse.json_format({'result': False})
    # except Exception as e:
    #     response = str(e)
    #     print(traceback.format_exc())
    #     print(sys.exc_info()[2])
    #     return APIResponse.json_format(response)

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=3000)


    # account_number = "024042205"
    # bank_name = "MBBank"
    # account_name = "tran duy quang"

    # with ThreadPoolExecutor(max_workers=2) as executor:
    #     while True:
    #         selected_banks = random.sample(banks, 2)
    #         futures = [executor.submit(check_bank, bank, account_number, bank_name, account_name) for bank in selected_banks]
    #         start_time = time.time()

    #         for future in as_completed(futures, timeout=5):
    #             try:
    #                 result = future.result()
    #                 if result:
    #                     print({'result': True, 'bank': str(selected_banks[futures.index(future)].__class__.__name__)})
    #                     break
    #             except Exception as e:
    #                 continue

    #         if time.time() - start_time >= 5:
    #             continue

    #         print(({'result': False}))
    #         break