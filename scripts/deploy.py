from brownie import Box1, Box2, ProxyAdmin, TransparentUpgradeableProxy, GovernanceToken, TimeLock, Governance, Contract, network, config
from scripts.helpful_scripts import get_account, encode_function_data, wait, LOCKAL_BLOCKCHAIN_NETWORKS, MAINNET_FORKED_NETWORKS
from web3 import Web3, constants
import time

# Priority fee
PRIORITY_FEE = 2000000000

# Voting params
VOTING_DELAY = 1
VOTING_PERIOD = 10
QUORUM_PERCENTAGE = 4

# Time Lock params
TIMELOCK_DELAY = 1  # delay in seconds

# Propose
SET_VAL = 666

proposeState = {
    '0': "Pending",
    '1': "Active",
    '2': "Canceled",
    '3': "Defeated",
    '4': "Succeeded",
    '5': "Queued",
    '6': "Expired",
    '7': "Executed"
}


def main():
    # redeploy all contacts
    redeploy = False

    # deploy initial Box contract with proxy
    box, proxyAdmin, proxy = deploy_initial_box_with_proxy(redeploy)

    # create contract to call
    proxy_box = Contract.from_abi("Box", proxy.address, Box1.abi)

    # call Box contract via proxy
    print("Set val to 7")
    proxy_box.setVal(7, {"from": get_account()})
    print(f"Value in Box contract is {proxy_box.getVal()}")

    # create Governance and delegate all control functionality to TimeLock
    governanceToken, timeLock, governance = deployGovernance(redeploy)

    # Transfer ownership of ProxyAdmin contract to Time Lock contract
    transferOwnership(proxyAdmin, timeLock)

    # ****Propose change of value*****
    # check value in Contract before proposing
    print(f"Value in Box contract is {proxy_box.getVal()}")

    # before proposal we want to delegate all votes to account
    delegateVotes(governanceToken)

    # proposing
    DESCRIPTION = "Propose: Store {0} in Box".format(SET_VAL)
    proposalId, transaction = propose(governance, proxy_box, DESCRIPTION)
    # **********************************

    # wait before voting
    delay = VOTING_DELAY + 2
    wait(delay, transaction)

    # voting
    transaction = vote(governance, proposalId)

    # wait voting to finish
    delay = VOTING_PERIOD + 2
    wait(delay, transaction)

    # check state of proposal
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")

    # queue and execute proposal
    queueAndExecute(proxy_box, governance, DESCRIPTION, proposalId)

    # check value after executing
    print(f"Value in Box contract is {proxy_box.getVal()}")

    # ****Propose change of implementation to Box2*****
    # check value in Contract before proposing
    print(f"Value in Box contract is {proxy_box.getVal()}")
    # deploy new implementation
    box2 = deployBox2()

    # before proposal we want to delegate all votes to account
    delegateVotes(governanceToken)

    # proposing
    DESCRIPTION = "Propose: Change implementation to Box2"
    proposalId, transaction = proposeBox2(
        governance, proxyAdmin, DESCRIPTION, proxy, box2)
    # **********************************

    # wait before voting
    delay = VOTING_DELAY + 2
    wait(delay, transaction)

    # voting
    transaction = vote(governance, proposalId)

    # wait voting to finish
    delay = VOTING_PERIOD + 2
    wait(delay, transaction)

    # check state of proposal
    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governance.state(proposalId)), -1)} state")

    # queue and execute proposal
    queueAndExecute2(proxyAdmin, governance, DESCRIPTION,
                     proposalId, proxy, box2)

    # check value after executing
    proxy_box = Contract.from_abi("Box", proxy.address, Box2.abi)
    print(f"Value in Box contract is {proxy_box.getVal()}")
    tx = proxy_box.increase({"from": get_account()})
    tx.wait(1)
    print(f"Value in Box contract is {proxy_box.getVal()}")


def queueAndExecute(boxContract, governanceContract, description, proposalId):
    encryptedCalldata = boxContract.setVal.encode_input(SET_VAL,)
    descriptionHash = Web3.keccak(text=description).hex()
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.queue([boxContract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account()})
    else:
        tx = governanceContract.queue([boxContract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)

    delay = TIMELOCK_DELAY + 3
    print(f"Sleeping for {delay} seconds")
    time.sleep(delay)

    wait(TIMELOCK_DELAY + 1, tx)

    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governanceContract.state(proposalId)), -1)} state")

    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.execute([boxContract.address], [0], [
                                        encryptedCalldata], descriptionHash, {"from": get_account()})
    else:
        tx = governanceContract.execute([boxContract.address], [0], [
                                        encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)


def queueAndExecute2(proxyAdminContract, governanceContract, description, proposalId, proxy, box2):
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyAdminContract.upgrade.encode_input(
        proxy, box2.address,)
    descriptionHash = Web3.keccak(text=description).hex()
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.queue([proxyAdminContract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account()})
    else:
        tx = governanceContract.queue([proxyAdminContract.address], [0], [
            encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)

    delay = TIMELOCK_DELAY + 3
    print(f"Sleeping for {delay} seconds")
    time.sleep(delay)

    wait(TIMELOCK_DELAY + 1, tx)

    print(
        f"Proposal {proposalId} is in {proposeState.get(str(governanceContract.state(proposalId)), -1)} state")

    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.execute([proxyAdminContract.address], [0], [
                                        encryptedCalldata], descriptionHash, {"from": get_account()})
    else:
        tx = governanceContract.execute([proxyAdminContract.address], [0], [
                                        encryptedCalldata], descriptionHash, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)


def vote(governanceContract, proposalId):
    vote = int(1)  # 1 = For
    reason = "I want so"
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.castVoteWithReason(
            proposalId, vote, reason, {"from": get_account()})
    else:
        tx = governanceContract.castVoteWithReason(
            proposalId, vote, reason, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    voteReason = tx.events["VoteCast"]["reason"]
    voteSupport = tx.events["VoteCast"]["support"]
    voteWeight = tx.events["VoteCast"]["weight"]
    # 0 = Against, 1 = For, 2 = Abstain
    voteDesc = {
        '0': "Against",
        '1': "For",
        '2': "Abstain"
    }
    print(
        f"You voted {voteDesc.get(str(voteSupport), -1)}, having weight = {voteWeight}, reason = {voteReason}")
    # return transaction receipt to use wait on it (istead of time)
    return tx


def propose(governanceContract, boxContract, description):
    print(description)
    # encrypt function name and args to bytes array
    encryptedCalldata = boxContract.setVal.encode_input(SET_VAL,)
    # function propose(address[] memory targets,uint256[] memory values,bytes[] memory calldatas,string memory description)
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.propose([boxContract.address], [
                                        0], [encryptedCalldata], description, {"from": get_account()})
    else:
        tx = governanceContract.propose([boxContract.address], [
                                        0], [encryptedCalldata], description, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    # Read proposal ID from emited event
    proposalId = tx.events["ProposalCreated"]["proposalId"]
    print(f"Proposal {proposalId} is created")
    print(description)
    return proposalId, tx


def proposeBox2(governanceContract, proxyAdminContract, description, proxy, box2):
    print(description)
    # encrypt function name and args to bytes array
    encryptedCalldata = proxyAdminContract.upgrade.encode_input(
        proxy, box2.address,)
    # function propose(address[] memory targets,uint256[] memory values,bytes[] memory calldatas,string memory description)
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = governanceContract.propose([proxyAdminContract.address], [
                                        0], [encryptedCalldata], description, {"from": get_account()})
    else:
        tx = governanceContract.propose([proxyAdminContract.address], [
                                        0], [encryptedCalldata], description, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    # Read proposal ID from emited event
    proposalId = tx.events["ProposalCreated"]["proposalId"]
    print(f"Proposal {proposalId} is created")
    print(description)
    return proposalId, tx


def delegateVotes(governanceToken):
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        governanceToken.delegate(
            get_account(), {"from": get_account()})
    else:
        governanceToken.delegate(
            get_account(), {"from": get_account(), "priority_fee": PRIORITY_FEE})
    # delegating if moving some voting power - creates checkPoint
    print(f"Checkpoints: {governanceToken.numCheckpoints(get_account())}")


def transferOwnership(proxyAdmin, timeLock):
    print("Transfering ownership to TimeLock")
    tx = proxyAdmin.transferOwnership(
        timeLock, {"from": get_account()})
    tx.wait(1)


def deploy_initial_box_with_proxy(redeployFlag):
    # deploy Box contract
    if len(Box1) <= 0 or redeployFlag:
        box = deployBox1()
    else:
        box = Box1[-1]
    print(f"Box1 contract deployed at {box.address}")

    # deploy ProxyAdmin contract
    if len(ProxyAdmin) <= 0 or redeployFlag:
        proxyAdmin = deployProxyAdmin()
    else:
        proxyAdmin = ProxyAdmin[-1]
    print(f"ProxyAdmin contract deployed at {proxyAdmin.address}")

    # deploy Proxy contract

    if len(TransparentUpgradeableProxy) <= 0 or redeployFlag:
        encoded_initializer = encode_function_data()
        proxy = deployProxy(box, proxyAdmin, encoded_initializer)
    else:
        proxy = TransparentUpgradeableProxy[-1]
    print(f"Proxy contract deployed at {proxy.address}")

    return box, proxyAdmin, proxy


def deployGovernance(redeploy):

    # deploy Governance Token
    if len(GovernanceToken) <= 0 or redeploy:
        governanceToken = deployGovernanceToken()
    else:
        governanceToken = GovernanceToken[-1]
    print(f"Governance token contract deployed at {governanceToken.address}")

    # deploy Time Lock contract
    if len(TimeLock) <= 0 or redeploy:
        timeLock = deployTimeLock()
    else:
        timeLock = TimeLock[-1]
    print(f"TimeLock contract deployed at {timeLock.address}")

    # deploy Governance Token
    if len(Governance) <= 0 or redeploy:
        governance = deployGovernanceContract(
            governanceToken, timeLock, VOTING_DELAY, VOTING_PERIOD, QUORUM_PERCENTAGE)
        # Set up Time Lock roles
        setUpTimeLockContract(timeLock, governance)
    else:
        governance = Governance[-1]
    print(f"Governance contract deployed at {governance.address}")

    return governanceToken, timeLock, governance


def deployBox1():
    print("Deploying Box1 contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        box = Box1.deploy(
            {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        box = Box1.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return box


def deployBox2():
    print("Deploying Box1 contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        box = Box2.deploy(
            {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        box = Box2.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return box


def deployProxyAdmin():
    print("Deploying Proxy Admin contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        proxyAdmin = ProxyAdmin.deploy(
            {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        proxyAdmin = ProxyAdmin.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return proxyAdmin


def deployProxy(box, proxyAdmin, encoded_initializer):
    print("Deploying Proxy contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        proxy = TransparentUpgradeableProxy.deploy(box.address, proxyAdmin.address, encoded_initializer,
                                                   {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        proxy = TransparentUpgradeableProxy.deploy(box.address, proxyAdmin.address, encoded_initializer,
                                                   {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return proxy


def deployGovernanceToken():
    print("Deploying Governance Token contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        governanceToken = GovernanceToken.deploy(
            {"from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        governanceToken = GovernanceToken.deploy(
            {"from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return governanceToken


def deployTimeLock():
    print("Deploying TimeLock contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        timeLock = TimeLock.deploy(TIMELOCK_DELAY, [], [], {"from": get_account(
        )}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        timeLock = TimeLock.deploy(TIMELOCK_DELAY, [], [], {"from": get_account(
        ), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return timeLock


def deployGovernanceContract(token, timeLock, votingDelay, votingPeriod, quorumPercentage):
    print("Deploying Governance contract ...")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        governance = Governance.deploy(token, timeLock, votingDelay, votingPeriod, quorumPercentage,  {
            "from": get_account()}, publish_source=config["networks"][network.show_active()].get("verify", False))
    else:
        governance = Governance.deploy(token, timeLock, votingDelay, votingPeriod, quorumPercentage,  {
            "from": get_account(), "priority_fee": PRIORITY_FEE}, publish_source=config["networks"][network.show_active()].get("verify", False))
    return governance


def setUpTimeLockContract(timeLockContract, governanceContract):
    # SetUp roles for proposer, executor, timelock_admin
    print(
        f"Setting proposer to Governance contract({governanceContract.address})")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = timeLockContract.grantRole(
            timeLockContract.PROPOSER_ROLE(), governanceContract.address, {"from": get_account()})
    else:
        tx = timeLockContract.grantRole(
            timeLockContract.PROPOSER_ROLE(), governanceContract.address, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    print(f"Setting executor to anyone")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = timeLockContract.grantRole(timeLockContract.EXECUTOR_ROLE(),
                                        constants.ADDRESS_ZERO, {"from": get_account()})
    else:
        tx = timeLockContract.grantRole(timeLockContract.EXECUTOR_ROLE(),
                                        constants.ADDRESS_ZERO, {"from": get_account(), "priority_fee": PRIORITY_FEE})
    tx.wait(1)
    print(f"Deleting our account from Time Lock admins. No we can do nothing")
    if network.show_active() in LOCKAL_BLOCKCHAIN_NETWORKS or network.show_active() in MAINNET_FORKED_NETWORKS:
        tx = timeLockContract.revokeRole(
            timeLockContract.TIMELOCK_ADMIN_ROLE(), get_account(), {
                "from": get_account()}
        )
    else:
        tx = timeLockContract.revokeRole(
            timeLockContract.TIMELOCK_ADMIN_ROLE(), get_account(), {
                "from": get_account(), "priority_fee": PRIORITY_FEE}
        )
    tx.wait(1)
