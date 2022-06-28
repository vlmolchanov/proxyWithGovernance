from brownie import network, accounts, config, chain

LOCKAL_BLOCKCHAIN_NETWORKS = ["development", "ganache-local"]
MAINNET_FORKED_NETWORKS = ["mainnet-fork"]


def get_account(index=0):
    if (
        network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS
        or network.show_active()
        # in mainnet we also need account with eth, so brownie provide it to us
        in MAINNET_FORKED_NETWORKS
    ):
        return accounts[index]  # use first account in account array
    else:
        return accounts.add(
            config["wallets"]["from_key"]
        )  # accounts.add(private_key) create account with specified pKey.


def encode_function_data(initializer=None, *args):
    """Encodes the function call so we can work with an initializer.
    Args:
        initializer ([brownie.network.contract.ContractTx], optional):
        The initializer function we want to call. Example: `box.store`.
        Defaults to None.
        args (Any, optional):
        The arguments to pass to the initializer function
    Returns:
        [bytes]: Return the encoded bytes.
    """
    if not len(args):
        args = b''

    if initializer:
        return initializer.encode_input(*args)

    return b''


def wait(numberOfBlocks, transaction):
    print(f"Waiting {numberOfBlocks} blocks")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        for block in range(numberOfBlocks):
            get_account().transfer(get_account(), "0 ether")
            print(chain.height)
    else:
        transaction.wait(numberOfBlocks)
