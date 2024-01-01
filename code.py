import requests
from time import sleep
import time
from web3 import Web3
import json
from gtts import gTTS
import os
from inputimeout import inputimeout 

telegram_token = "6543653320:AAHE5joeufmae7OjqQHXLOZcoUsobSPbCxQ"
telegram_url = f"https://api.telegram.org/bot{telegram_token}"

def speak(text):
    # tts = gTTS(text=text, lang='en')
    # tts.save("audio.mp3")
    # play using ffplay
    # os.system("ffplay -v 10 -nodisp -autoexit audio.mp3")
    params = {"chat_id": "1962360155", "text": text}
    r = requests.get(telegram_url + "/sendMessage", params=params)  

block = 18470711
# read latest block from file if it exists
try:
    with open('latest_block.txt', 'r') as f:
        block = int(f.read())
except:
    pass

def get_deposits_after_block(start_block):
    payload = {}
    payload['module'] = 'account'
    payload['action'] = 'txlist'
    payload['address'] = '0xD37BbE5744D730a1d98d8DC97c42F0Ca46aD7146'
    payload['startblock'] = str(start_block + 1)
    payload['endblock'] = '99999999'
    payload['page'] = '1'
    payload['offset'] = '100'
    payload['sort'] = 'desc'
    payload['apikey'] = 'EQV4WRIT4R4V7TJMXJBJPFDCK18ECS844R'
    latest_block = start_block
    # Write latest block to file
    with open('latest_block.txt', 'w') as f:
        f.write(str(latest_block))
    url = "https://api.etherscan.io/api"

    hash_list = []
    r = requests.get(url, params=payload)
    txs = r.json()['result']
    for tx in txs:
        if 'depositWithExpiry' in tx['functionName']:
            hash_list.append(tx['hash'])
        if int(tx['blockNumber']) > latest_block:
            latest_block = int(tx['blockNumber'])
    return hash_list, latest_block


def is_streaming_swap(memo):
    if len(memo.split(':')) < 4:
        return False
    else:   
        if '/' in memo.split(':')[3]:
            return True
        else:
            return False

def is_swap_limit_order(memo):
    limit = memo.split(':')[3]
    if is_streaming_swap(memo):
        limit = limit.split('/')[0]
    if limit == '0' or limit == '':
        return False
    else:
        return True

def get_contract(add):
    abi_endpoint = f"https://api.etherscan.io/api?module=contract&action=getabi&address={add}&apikey={ETHERSCAN_API_KEY}"
    abi = json.loads(requests.get(abi_endpoint).text)
    contract = w3.eth.contract(address=add, abi=abi["result"])
    return contract


def get_asset_value(asset, amount):
    if int(asset,16) == 0:
        amount /= 1e18
        unit = 'Eth'
    # check if asset is USDC
    elif asset.lower() == '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':
        amount /= 1e6
        unit = 'USDC'
    elif asset.lower() == '0x6b175474e89094c44da98b954eedeac495271d0f':
        amount /= 1e18
        unit = 'DAI'
    elif asset.lower() == '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599':
        amount /= 1e8
        unit = 'WBTC'
    elif asset.lower() == '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9':
        amount /= 1e18
        unit = 'AAVE'
    elif asset.lower() == '0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e':
        amount /= 1e18
        unit = 'YFI'
    #check if asset is USDT
    elif asset.lower() == '0xdac17f958d2ee523a2206206994597c13d831ec7':
        amount /= 1e6
        unit = 'USDT'
    #check if asset is USDP
    elif asset.lower() == '0x8e870d67f660d95d5be530380d0ec0bd388289e1':
        amount /= 1e18
        unit = 'USDP'
    #check if asset is GUSD
    elif asset.lower() == '0x056fd409e1d7a124bd7017459dfea2f387b6d5cd':
        amount /= 1e2
        unit = 'GUSD'
    #check if asset is LUSD
    elif asset.lower() == '0x5f98805a4e8be255a32880fdec7f6728c6568ba0':
        amount /= 1e18
        unit = 'LUSD'
    #check if asset is DAI
    elif asset.lower() == '0x6b175474e89094c44da98b954eedeac495271d0f':
        amount /= 1e18
        unit = 'DAI'
    else:
        token_contract = get_contract(asset)
        decimals = token_contract.functions.decimals().call()
        unit = token_contract.functions.symbol().call()
        # unit = token_contract.name()    
        amount /= pow(10,decimals)
    return amount, unit


def match_output_token(asset, output_token):
    if asset == 'RUNE':
        if output_token ==  'THOR.RUNE' or output_token == 'r':
            return True
        else:
            return False
    elif asset == 'BTC':
        if 'BTC' in output_token or output_token == 'b':
            return True
        else:
            return False
    elif asset == 'THOR':
        if 'ETH/THOR' in output_token or 'ETH.THOR' in output_token:
            return True
        else:
            return False
    elif asset == 'XDEFI':
        if 'XDEFI' in output_token:
            return True
        else:
            return False
    elif asset == 'TGT':
        if 'TGT' in output_token:
            return True
        else:
            return False
    elif asset == 'FOX':
        if 'FOX' in output_token:
            return True
        else:
            return False
    


def print_details(output_token, order_size, hash, input_symbol, memo):
    print(f'conversion to {output_token} for ${order_size} from token {input_symbol} is starting soon')
    print(f'hash: {hash}')
    print(f'memo: {memo}')
    alert_count = 0
    while(True):
        try:
            alert_count += 1
            speak(f'Alert! Alert! conversion to {output_token} for ${order_size} is starting soon')
            inputimeout(prompt='Press enter to acknowledge: ', timeout=60)
            break
        except:
            print('timeout, sounding alert again')
            if alert_count > 2:
                break
            continue

    print('*'*80)

# price dict
price_dict = {}
price_dict['DAI'] = 1
price_dict['USDC'] = 1
price_dict['USDT'] = 1
price_dict['USDP'] = 1
price_dict['GUSD'] = 1
price_dict['LUSD'] = 1
price_dict['WBTC'] = 37100
price_dict['AAVE'] = 80
price_dict['YFI'] = 10000
price_dict['Eth'] = 2000
price_dict['THOR'] = 0.39
price_dict['TGT'] = 0.02
price_dict['FOX'] = 0.02
price_dict['XDEFI'] = 0.16
price_dict['RUNE'] = 0.23
price_dict['DPI'] = 0.23
price_dict['SNX'] = 2.8

def get_price(token):
    if token in price_dict:
        return price_dict[token]
    else:
        return 0.001


#etherscan api
ETHERSCAN_API_KEY = 'EQV4WRIT4R4V7TJMXJBJPFDCK18ECS844R'
# infura API key
API_KEY = "d0f3b77ed8084c0397ad4f78f3352a41"
# change endpoint to mainnet or ropsten or any other of your account
url = f"https://mainnet.infura.io/v3/{API_KEY}"

w3 = Web3(Web3.HTTPProvider(url))
res = w3.is_connected()
print('*'*80)

while(True):
    try:
        old_block = block
        hash_list, block = get_deposits_after_block(block)
        if block == old_block:
            sleep(30)
            continue
        print(f'block: {block}')
        for hash in hash_list:
            tx = w3.eth.get_transaction(hash)

            # Create Web3 contract object
            contract = get_contract(tx['to'])

            # Decode input data using Contract object's decode_function_input() method
            func_obj, func_params = contract.decode_function_input(tx["input"])
            memo = func_params['memo']
            if memo.split(':')[0] != '=' and memo.split(':')[0] != 'SWAP' and memo.split(':')[0] != 's':
                continue
            # print asset value and unit
            asset = func_params['asset']
            # print(hash)
            amount = func_params['amount']
            amount, unit = get_asset_value(asset, amount)
            total_order_size = int(amount * get_price(unit))
            # print(amount, unit, '$', total_order_size)
            # print('is streaming swap:', is_streaming_swap(func_params['memo']))
            # print('is swap limit order:', is_swap_limit_order(func_params['memo']))
            output_token = func_params['memo'].split(':')[1]
            if total_order_size > 25000:
                print(memo, ' $', total_order_size,  hash, 'from', unit)
            # if is_swap_limit_order(memo):
            #     continue

            if match_output_token('RUNE', output_token) and total_order_size > 250000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('THOR', output_token) and total_order_size > 25000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('XDEFI', output_token) and total_order_size > 5000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('TGT', output_token) and total_order_size > 5000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('FOX', output_token) and total_order_size > 5000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('BTC', output_token) and total_order_size > 2000000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('ETH', output_token) and total_order_size > 1000000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('ATOM', output_token) and total_order_size > 100000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif match_output_token('SNX', output_token) and total_order_size > 5000:
                print_details(output_token, total_order_size, hash, unit, memo)
            elif total_order_size > 500000:
                print_details(output_token, total_order_size, hash, unit, memo)
        sleep(30)
    except:
        print('error')
        sleep(30)
        pass