import sys
import click
from . import utils


@click.group()
def main():
    "Simple CLI for working with Ether dollar's bank"
    pass


@main.command()
@click.option(
    '--ether',
    type=float,
    callback=utils.check_ether,
    required=True,
    help='The collateral amount in ether')
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def send_eth(ether, private_key):
    "Get Ether dollar loan by sending ether"

    tx_hash = utils.send_eth(utils.addresses['erc20bank'], int(ether * 10**18),
                             private_key)
    return tx_hash


@main.command()
@click.option(
    '--collateral',
    type=float,
    callback=utils.check_ether,
    required=True,
    help='The collateral amount in ether')
@click.option(
    '--dollar',
    type=float,
    callback=utils.check_dollar,
    required=True,
    help='The loan amount in Ether dollar')
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def get_loan(collateral, dollar, private_key):
    "Get Ether dollar loan by depositing ether"

    var = _get_variables()
    if collateral * var['collateralPrice'] < var['collateralRatio'] * dollar:
        click.secho('Error: Insufficient collateral', fg='red')
        click.secho()
        sys.exit()
    func = utils.contracts['erc20bank'].functions.getLoan(
        int(dollar * 10**18))
    utils.approve_collateral(
        utils.addresses['erc20bank'], collateral, private_key)
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option(
    '--collateral',
    type=float,
    callback=utils.check_ether,
    required=True,
    help='The collateral amount')
@click.option(
    '--loan-id',
    type=int,
    callback=utils.check_loan_id,
    required=True,
    help="The loan's ID")
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def increase_collateral(collateral, loan_id, private_key):
    "Increase the loan's collateral"

    func = utils.contracts['erc20bank'].functions.increaseCollateral(loan_id)
    utils.approve_collateral(
        utils.addresses['erc20bank'], collateral, private_key)
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option(
    '--loan-id',
    type=int,
    callback=utils.check_loan_id,
    required=True,
    help="The loan's ID")
@click.option('--collateral', type=float, help='The collateral amount')
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def decrease_collateral(loan_id, collateral, private_key):
    "Decrease the loan's collateral"

    loan = _show(loan_id)
    var = _get_variables()
    if loan['amount'] == 0:
        collateral = loan['collateral']
        func = utils.contracts['erc20bank'].functions.decreaseCollateral(
            loan_id, int(collateral))
        tx_hash = utils.send_transaction(func, 0, private_key)
        return tx_hash
    elif not collateral or collateral < 0:
        click.secho('Error: collateral must be a positive number', fg='red')
        click.secho()
        sys.exit()
    elif (loan['collateral'] * 10**-18 - collateral) * var['collateralPrice'] < var[
            'collateralRatio'] * loan['amount'] / 10.0**18:
        click.secho('Insufficient collateral.', fg='red')
        click.secho()
        sys.exit()
    func = utils.contracts['erc20bank'].functions.decreaseCollateral(
        loan_id, int(collateral * 10**18))
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option(
    '--loan-id',
    type=int,
    callback=utils.check_loan_id,
    required=True,
    help="The loan's ID")
@click.option(
    '--dollar',
    type=float,
    callback=utils.check_dollar,
    required=True,
    help='The loan amount in Ether dollar')
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def settle_loan(loan_id, dollar, private_key):
    "Settle the Ether dollar loan"

    balance = _get_balance(utils.priv2addr(private_key))
    if balance < dollar * 10**18:
        click.secho('Error: Insufficient balance', fg='red')
        click.secho()
        sys.exit()
    loan = _show(loan_id)
    if loan['amount'] < dollar:
        click.secho('The amount exceeds the loan', fg='red')
        click.secho()
        sys.exit()
    utils.approve_dollar(utils.addresses['erc20bank'], dollar, private_key)
    func = utils.contracts['erc20bank'].functions.settleLoan(
        loan_id, int(dollar * 10**18))
    print('Settle loan')
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option(
    '--loan-id',
    type=int,
    callback=utils.check_loan_id,
    required=True,
    help='The loan id')
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def liquidate(loan_id, private_key):
    "Start the liquidation proccess"

    var = _get_variables()
    loan = _show(loan_id)
    if loan['collateral'] * 10**-18 * var['collateralPrice'] > var[
            'collateralRatio'] * loan['amount'] / 10.0**18:
        click.secho('Error: Sufficient collateral', fg='red')
        click.secho()
        sys.exit()
    func = utils.contracts['erc20bank'].functions.liquidate(loan_id)
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option(
    '--dollar',
    type=float,
    callback=utils.check_dollar,
    help="The account's address")
def min_collateral(dollar):
    "Count min collateral for the loan"

    func = utils.contracts['erc20bank'].functions.minCollateral(
        int(dollar * 10**18))
    result = utils.send_eth_call(func, None)
    click.secho(
        'Minimum collateral for getting {0} dollars loan is {1}'.format(
            dollar, round(result * 10**-18, 10)),
        fg='green')
    click.secho()
    return result


@main.command()
def get_balance():
    "Get Ether dollar account's balance"

    result = _get_balance(utils.current_user())
    click.secho('Balance: {} dollar'.format(result / 10.0**18), fg='green')
    click.secho()


@main.command()
@click.option('--owner', required=True, help="The account's address")
@click.option('--spender', required=True, help="The account's address")
def allowance(owner, spender):
    "Get Ether dollar account's balance"

    owner = utils.w3.toChecksumAddress(owner)
    spender = utils.w3.toChecksumAddress(spender)
    func = utils.contracts['etherdollar'].functions.allowance(owner, spender)
    result = utils.send_eth_call(func, spender)
    click.secho('Allowance: {} dollar'.format(result / 10.0**18), fg='green')
    click.secho()
    return result


@main.command()
@click.option('--loan-id', required=True, type=int, help='The loan id')
def show(loan_id):
    "Show the specified loan"

    loan = _show(loan_id)
    if not int(loan['recipient'], 0):
        click.secho('There is no loan.', fg='red')
        click.secho()
    else:
        click.secho('loanId:\t\t{}'.format(loan_id), fg='green')
        click.secho(
            'collateral:\t{} ether'.format(
                round(loan['collateral'] * 10**-18, 10)),
            fg='green')
        click.secho(
            'amount:\t\t{} dollar'.format(loan['amount'] * 10**-2), fg='green')
        click.secho('state:\t\t{}'.format(loan['state']), fg='green')
        click.secho()


@main.command()
def loans_list():
    "Get list of account's loans"

    account = utils.current_user()
    result = _loans_list(account=account)
    for loan in sorted(result, key=lambda loan: loan['loanId']):
        click.secho('loanId:\t\t{}'.format(loan['loanId']), fg='green')
        click.secho(
            'collateral:\t{}'.format(
                round(loan['collateral'] * 10**-18, 10)),
            fg='green')
        click.secho(
            'amount:\t\t{} dollar'.format(round(loan['amount'] * 10**-18, 10)), fg='green')
        click.secho('state:\t\t{}'.format(loan['state']), fg='green')
        click.secho()
    if not result:
        click.secho('There is no loan.', fg='green')
    click.secho()


@main.command()
def liquidatable_loans():
    "Get list of liquidatable loans"

    result = []
    var = _get_variables()
    res = _loans_list()
    for loan in sorted(res, key=lambda loan: loan['loanId']):
        if loan['state'] == 'active' and loan['collateral'] * 10**-18 * var[
                'collateralPrice'] * 10.0**18 < var['collateralRatio'] * loan['amount']:
            result.append(loan)
            click.secho('loanId:\t\t{}'.format(loan['loanId']), fg='green')
            click.secho(
                'collateral:\t{}'.format(
                    round(loan['collateral'] * 10**-18, 10)),
                fg='green')
            click.secho(
                'amount:\t\t{} dollar'.format(loan['amount'] * 10**-2),
                fg='green')
            click.secho()
    if not result:
        click.secho('There is no liquidatable loan.', fg='green')
    click.secho()


@main.command()
def get_variables():
    "Get the current variables' value"

    result = _get_variables()
    click.secho(
        'collateralRatio:\t{}'.format(result['collateralRatio']), fg='green')
    click.secho(
        'collateralPrice:\t{} ether dollar'.format(
            result['collateralPrice']),
        fg='green')
    click.secho(
        'liquidationDuration:\t{} minute'.format(
            result['liquidationDuration']),
        fg='green')
    click.secho()


def _loans_list(account=None):
    result = {}
    if account:
        filters = {'recipient': account}
    else:
        filters = None
    loan_filter = utils.contracts['erc20bank'].events.LoanGot.createFilter(
        fromBlock=1, toBlock='latest', argument_filters=filters)
    loans = utils.w3.eth.getLogs(loan_filter.filter_params)
    for loan_bytes in loans:
        loan = loan_filter.format_entry(loan_bytes)
        loan_id = loan['args']['loanId']
        result[loan_id] = _show(loan_id)

    return list(result.values())


def _show(loan_id):
    loan_params = ['recipient', 'collateral', 'amount', 'state']
    loan_satates = ['active', 'under liquidation', 'liquidated', 'settled']
    loan = dict(
        zip(
            loan_params,
            utils.send_eth_call(
                utils.contracts['erc20bank'].functions.loans(loan_id), None)))
    loan['state'] = loan_satates[loan['state']]
    loan['loanId'] = loan_id
    return loan


def _get_variables():
    result = {
        'collateralRatio':
        utils.send_eth_call(
            utils.contracts['erc20bank'].functions.collateralRatio(),
            None) / 1000.0,
        'collateralPrice':
        utils.send_eth_call(
            utils.contracts['erc20bank'].functions.collateralPrice(),
            None) / 10.0**18,
        'liquidationDuration':
        utils.send_eth_call(
            utils.contracts['erc20bank'].functions.liquidationDuration(),
            None) / 60.0
    }
    return (result)


def _get_balance(account):
    account = utils.w3.toChecksumAddress(account)
    func = utils.contracts['etherdollar'].functions.balanceOf(account)
    result = utils.send_eth_call(func, account)
    return result


if __name__ == '__main__':
    main()
