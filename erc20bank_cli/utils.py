import os
import sys
import json
import click
from eth_keys import keys
from web3 import Web3, HTTPProvider
from . import config


def get_addresses(erc20bank_addr):
    global addresses
    erc20bank_contract = w3.eth.contract(
        address=w3.toChecksumAddress(config.ERC20BANK_ADDR),
        abi=config.ABIES['erc20bank'])
    addresses = {
        'collateral':
        w3.toChecksumAddress(config.COLLATERAL_ADDR),
        'erc20bank':
        erc20bank_addr,
        'oracles':
        send_eth_call(erc20bank_contract.functions.oraclesAddr(), None),
        'liquidator':
        send_eth_call(erc20bank_contract.functions.liquidatorAddr(), None),
        'etherdollar':
        send_eth_call(erc20bank_contract.functions.etherDollarAddr(), None)
    }
    return addresses


def get_contracts():
    global contracts
    contracts = {
        'collateral':
        w3.eth.contract(
            address=addresses['collateral'], abi=config.ABIES['collateral']),
        'erc20bank':
        w3.eth.contract(
            address=addresses['erc20bank'], abi=config.ABIES['erc20bank']),
        'oracles':
        w3.eth.contract(
            address=addresses['oracles'], abi=config.ABIES['oracles']),
        'liquidator':
        w3.eth.contract(
            address=addresses['liquidator'], abi=config.ABIES['liquidator']),
        'etherdollar':
        w3.eth.contract(
            address=addresses['etherdollar'], abi=config.ABIES['etherdollar'])
    }
    return contracts


def approve_collateral(spender, collateral, private_key):
    print('Approving {} dollars transfer from your account by the contract'.
          format(collateral))
    spender = w3.toChecksumAddress(spender)
    func = contracts['collateral'].functions.approve(spender,
                                                     int(collateral * 10**18))
    tx_hash = send_transaction(func, 0, private_key)
    w3.eth.waitForTransactionReceipt(tx_hash)
    return tx_hash


def approve_dollar(spender, dollar, private_key):
    print('Approving {} dollars transfer from your account by the contract'.
          format(dollar))
    spender = w3.toChecksumAddress(spender)
    func = contracts['etherdollar'].functions.approve(spender,
                                                      int(dollar * 10**18))
    tx_hash = send_transaction(func, 0, private_key)
    w3.eth.waitForTransactionReceipt(tx_hash)
    return tx_hash


def check_account(ctx, param, value):
    if not value and 'ERC20BANK_PRIVATEKEY' in os.environ:
        value = os.environ['ERC20BANK_PRIVATEKEY']
    if not value:
        print(
            'Run:\n\texport ERC20BANK_PRIVATEKEY="your ethereum private key"')
        sys.exit()
    if value.startswith('0x'):
        value = value[2:]
    return value


def check_ether(ctx, param, value):
    if not isinstance(value, (int, float)):
        click.secho('Error: ether must be a number', fg='red')
        click.secho()
        sys.exit()
    elif value <= 0:
        click.secho('Error: ether must be a positive number', fg='red')
        click.secho()
        sys.exit()
    return value


def check_loan_id(ctx, param, value):
    from . import erc20bank
    loan = erc20bank._show(value)
    if not loan:
        click.secho('Invalid loanId.', fg='red')
        click.secho()
        sys.exit()
    return value


def check_liquidation_id(ctx, param, value):
    from . import liquidator
    liquidation = liquidator._active_liquidations(value)
    if not liquidation:
        click.secho('Invalid liquidation id.', fg='red')
        click.secho()
        sys.exit()
    elif liquidation['state'] != 'active':
        click.secho('The liquidation finished.', fg='red')
        click.secho()
        sys.exit()


def check_dollar(ctx, param, value):
    if not isinstance(value, (int, float)):
        click.secho('Error: dollar must be a number', fg='red')
        click.secho()
        sys.exit()
    elif value < 0:
        click.secho('Error: dollar must be a positive number', fg='red')
        click.secho()
        sys.exit()
    return value


def priv2addr(private_key):
    pk = keys.PrivateKey(bytes.fromhex(private_key))
    return pk.public_key.to_checksum_address()


def send_transaction(func, value, private_key):
    transaction = func.buildTransaction({
        'nonce':
        w3.eth.getTransactionCount(priv2addr(private_key)),
        'from':
        priv2addr(private_key),
        'value':
        value,
        'gas':
        config.GAS,
        'gasPrice':
        config.GAS_PRICE
    })
    signed = w3.eth.account.signTransaction(transaction, private_key)
    raw_transaction = signed.rawTransaction.hex()
    tx_hash = w3.eth.sendRawTransaction(raw_transaction).hex()
    rec = w3.eth.waitForTransactionReceipt(tx_hash)
    if rec['status']:
        click.secho('tx: {}'.format(tx_hash), fg='green')
    else:
        click.secho(
            'Reverted!\nError occured during contract execution', fg='green')
    click.secho()
    return tx_hash


def send_eth(contract_addr, value, private_key):
    transaction = {
        'nonce': w3.eth.getTransactionCount(priv2addr(private_key)),
        'from': priv2addr(private_key),
        'value': value,
        'gas': config.GAS,
        'to': contract_addr,
        'gasPrice': config.GAS_PRICE
    }
    signed = w3.eth.account.signTransaction(transaction, private_key)
    raw_transaction = signed.rawTransaction.hex()
    tx_hash = w3.eth.sendRawTransaction(raw_transaction).hex()
    rec = w3.eth.waitForTransactionReceipt(tx_hash)
    if rec['status']:
        click.secho('tx: {}'.format(tx_hash), fg='green')
    else:
        click.secho(
            'Reverted!\nError occured during contract execution', fg='green')
    click.secho()
    return tx_hash


def send_eth_call(func, sender):
    if not sender:
        sender = current_user()
    result = func.call({
        'from': sender,
    })
    return result


def current_user():
    return priv2addr(os.environ['ERC20BANK_PRIVATEKEY'])


def start():
    global addresses, contracts, w3
    w3 = Web3(HTTPProvider(config.INFURA_URL))
    if 'ERC20BANK_PRIVATEKEY' not in os.environ:
        print(
            'Run:\n\t export ERC20BANK_PRIVATEKEY="your ethereum private key"')
        sys.exit()

    if os.path.exists(os.path.expanduser('~/.erc20bank.json')):
        with open(os.path.expanduser('~/.erc20bank.json'), 'r') as f:
            addresses = json.load(f)
    elif 'ERC20BANK_CONTRACTADDRESS' in os.environ:
        try:
            addresses = get_addresses(os.environ['ERC20BANK_CONTRACTADDRESS'])
            with open(os.path.expanduser('~/.erc20bank.json'), 'w') as f:
                f.write(json.dumps(addresses))
        except:
            print('First edit the ERC20BANK_CONTRACTADDRESS and try again')
            sys.exit()
    else:
        addresses = get_addresses(w3.toChecksumAddress(config.ERC20BANK_ADDR))
        with open(os.path.expanduser('~/.erc20bank.json'), 'w') as f:
            f.write(json.dumps(addresses))
    get_contracts()


# we are initalizing some variables here
addresses = contracts = w3 = None
start()


# FIXME: infura not supports filtering of events.
# Here we are hacking web3.py filters to use getLogs rpc endpoint instead.
def dummy(*args, **argsdic):
    if len(args) > 0 and args[0] == 'eth_newFilter':
        return 0
    else:
        return original_request_blocking(*args, **argsdic)


original_request_blocking = w3.manager.request_blocking
w3.manager.request_blocking = dummy
