import requests
import logging
import logging.config
import json
import time
import datetime
import os

logging.config.fileConfig('./conf/log.conf')
logger = logging.getLogger('server')

def get_all_contracts():
    url = 'https://explorer.eoseco.com/api/contracts'
    res = requests.get(url)
    if res.status_code != 200:
        logger.error('request response code error [url=%s] [code=%d]' %(url, res.status_code))
        return None
    try:
        res_json = json.loads(res.text)
    except Exception, ex:
        logger.exception('request response data error [url=%s] [data=%s]' %(url, res.text))
        return None
    return res_json

def get_contracts_file():
    return './data/contracts'

def load_contracts():
    contracts_dict = {}
    contracts_file = get_contracts_file()
    if not os.path.exists(contracts_file):
        return {}
    with open(contracts_file, 'r') as contracts:
        for contract in contracts:
            (current_time_str, contract_name, contract_hash) = contract.split('\t')
            if contract_name is None or contract_hash is None:
                continue
            contracts_dict[contract_name.strip()] = contract_hash.strip()
    return contracts_dict

def save_contract(contract_name, contract_hash):
    contracts_file = get_contracts_file()
    current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(contracts_file, 'a+') as contracts:
        contracts.write('%s\t%s\t%s\n' %(current_time_str, contract_name, contract_hash))

def broadcast_message(message):
    bot_token = '646392590:AAFXnqR_1qbM8yG3dmLJx8sX6BTdrLinwjM'
    api_url = 'https://api.telegram.org/bot%s/sendMessage' %(bot_token)
    request_data = {
        'chat_id' : '@EOSContractStatus',
        'text' : message
    }
    res = requests.get(api_url, params = request_data)
    if res.status_code != 200:
        logger.error('broadcast_message failed http code error [url=%s] [code=%d]' %(res.url, res.status_code)) 
        return None
    try:
        res_json = json.loads(res.text)
        if res_json['ok'] is not True:
            logger.error('broadcast message failed response data fail [url=%s] [data=%s]' %(res.url, res.text))
            return None
    except Exception, ex:
        logger.exception('broadcast message failed response data error [url=%s] [data=%s]' %(res.url, res.text))
        return None
    logger.info('broadcast_message success [url=%s] [response=%s]' %(res.url, res.text))

contracts_alias = None
def get_contract_alias(contract_name):
    global contracts_alias
    if contracts_alias is None:
        contracts_alias = {}
        contracts_alias_file = './data/alias'
        with open(contracts_alias_file, 'r') as f:
            for contract_alias in f:
                (contract_name, alias) = contract_alias.split('\t')
                contracts_alias[contract_name.strip()] = alias.strip()
    if contract_name in contracts_alias:
        return contracts_alias[contract_name]
    else:
        return None

def daemon():
    pid = os.getpid() 
    pid_file = './logs/pid.log'
    with open(pid_file, 'w') as f:
        f.write(str(pid))

    contracts_dict = load_contracts()
    loop_interval = 60
    loop_stop = False
    while not loop_stop:
        try:
            contracts = get_all_contracts() 
            for contract in contracts:
                try:
                    contract_name = contract['contract']
                    contract_hash = contract['hash']
                    contract_alias= get_contract_alias(contract_name)
                    contract_alias= "" if contract_alias is None else "(%s)" %(contract_alias)
                except Exception, ex:
                    logger.exception('get contract info failed [contract=%s]' %(contract))
                    continue
                if contract_name not in contracts_dict:
                    contracts_dict[contract_name] = contract_hash 
                    save_contract(contract_name, contract_hash)
                    logger.info('new contract add [contract_name=%s] [contract_hash=%s]' %(contract_name, contract_hash))
                    broadcast_message('contract "%s%s" add to the chain' %(contract_name, contract_alias))
                if contract_hash != contracts_dict[contract_name]:
                    logger.info('exist contract change [contract_name=%s] [old_hash=%s] [new_hash=%s]' %(contract_name, contracts_dict[contract_name], contract_hash))
                    contracts_dict[contract_name] = contract_hash
                    save_contract(contract_name, contract_hash)
                    broadcast_message('contract "%s%s" changed' %(contract_name, contract_alias))

            logger.info('loop interval finish [contracts_num=%d] [loop_interval=%d]' %(len(contracts_dict), loop_interval))
            time.sleep(loop_interval)
        except Exception, ex:
            logger.exception('monitor loop caught unknown exception : %s' %(ex)) 
        except KeyboardInterrupt:
            logger.info('receive KeyboardInterrupt signal. loop finish')
            loop_stop = True

if __name__ == '__main__':
    pid = os.fork()
    if pid != 0:
        logger.info('start children server finish [pid=%d]' %(pid))
    else:
        daemon()
