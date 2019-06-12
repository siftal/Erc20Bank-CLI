import click
from . import utils


@click.group()
def main():
    "Simple CLI for oracles to work with Ether dollar"
    pass


@main.command()
@click.option(
    '--collateral-price', type=float, help="The ether price in ether dollar")
@click.option('--collateral-ratio', type=float, help="The collateral ratio")
@click.option(
    '--liquidation-duration',
    type=int,
    help="The liquidation duration in minutes")
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def vote(collateral_price, collateral_ratio, liquidation_duration, private_key):
    "Vote on the variable for setting up Ether Bank"

    assert [collateral_price, collateral_ratio, liquidation_duration
            ].count(None) == 2, "You should set one variable per vote"
    if collateral_price:
        var_code = 0
        value = int(collateral_price * 10**18)
    elif collateral_ratio:
        var_code = 1
        value = int(collateral_ratio * 1000)
    elif liquidation_duration:
        var_code = 2
        value = liquidation_duration * 60
    func = utils.contracts['oracles'].functions.vote(var_code, value)
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option('--oracle', required=True, help="The oracle's address")
@click.option('--score', type=int, required=True, help="The oracle's score")
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def set_score(oracle, score, private_key):
    "Edit oracle's score"

    oracle = utils.w3.toChecksumAddress(oracle)
    func = utils.contracts['oracles'].functions.setScore(oracle, score)
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


@main.command()
@click.option(
    '--private-key',
    callback=utils.check_account,
    help='The privat key to sign the transaction')
def finish_recruiting(private_key):
    "Set recruiting as finished"

    func = utils.contracts['oracles'].functions.finishRecruiting()
    tx_hash = utils.send_transaction(func, 0, private_key)
    return tx_hash


if __name__ == '__main__':
    main()
