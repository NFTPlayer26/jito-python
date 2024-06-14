import asyncio
from typing import List

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction, VersionedTransaction
from spl.memo.instructions import MemoParams, create_memo

from jito_searcher_client.convert import tx_to_protobuf_packet
from jito_searcher_client.generated.bundle_pb2 import Bundle
from jito_searcher_client.generated.searcher_pb2 import (
    ConnectedLeadersRequest,
    GetTipAccountsRequest,
    MempoolSubscription,
    NextScheduledLeaderRequest,
    NextScheduledLeaderResponse,
    ProgramSubscriptionV0,
    SendBundleRequest,
    WriteLockedAccountSubscriptionV0,
)
from jito_searcher_client.generated.searcher_pb2_grpc import SearcherServiceStub
from jito_searcher_client.async_searcher import get_async_searcher_client_no_auth

async def mempool_accounts(block_engine_url: str, accounts: List[str]):
    """
    Stream transactions from the mempool if they write-lock one of the provided accounts
    """
    client = await get_async_searcher_client_no_auth(block_engine_url)
    leader: NextScheduledLeaderResponse = await client.GetNextScheduledLeader(NextScheduledLeaderRequest())
    print(f"next scheduled leader is {leader.next_leader_identity} in {leader.next_leader_slot - leader.current_slot} slots")

    stream = client.SubscribeMempool(MempoolSubscription(wla_v0_sub=WriteLockedAccountSubscriptionV0(accounts=accounts)))
    while True:
        response = await stream.read()
        for packet in response.transactions:
            print(VersionedTransaction.from_bytes(packet.data))

async def mempool_programs(block_engine_url: str, programs: List[str]):
    """
    Stream transactions from the mempool if they mention one of the provided programs
    """
    client = await get_async_searcher_client_no_auth(block_engine_url)
    leader: NextScheduledLeaderResponse = await client.GetNextScheduledLeader(NextScheduledLeaderRequest())
    print(f"next scheduled leader is {leader.next_leader_identity} in {leader.next_leader_slot - leader.current_slot} slots")

    stream = client.SubscribeMempool(MempoolSubscription(program_v0_sub=ProgramSubscriptionV0(programs=programs)))
    while True:
        response = await stream.read()
        for packet in response.transactions:
            print(VersionedTransaction.from_bytes(packet.data))

async def next_scheduled_leader(block_engine_url: str):
    """
    Find information on the next scheduled leader.
    """
    client = await get_async_searcher_client_no_auth(block_engine_url)
    next_leader = await client.GetNextScheduledLeader(NextScheduledLeaderRequest())
    print(f"{next_leader=}")

async def connected_leaders(block_engine_url: str):
    """
    Get leaders connected to this block engine.
    """
    client = await get_async_searcher_client_no_auth(block_engine_url)
    leaders = await client.GetConnectedLeaders(ConnectedLeadersRequest())
    print(f"{leaders=}")

async def tip_accounts(block_engine_url: str):
    """
    Get the tip accounts from the block engine.
    """
    client = await get_async_searcher_client_no_auth(block_engine_url)
    accounts = await client.GetTipAccounts(GetTipAccountsRequest())
    print(f"{accounts=}")

async def send_bundle(
    block_engine_url: str,
    payer_kp: Keypair,
    message: str,
    num_txs: int,
    lamports: int,
    tip_account_str: str,
):
    """
    Send a bundle!
    """
    tip_account = Pubkey.from_string(tip_account_str)

    # Initialize client
    client = await get_async_searcher_client_no_auth(block_engine_url)

    # Wait for Jito leader
    is_leader_slot = False
    print("waiting for jito leader...")
    while not is_leader_slot:
        await asyncio.sleep(0.5)
        next_leader: NextScheduledLeaderResponse = await client.GetNextScheduledLeader(NextScheduledLeaderRequest())
        num_slots_to_leader = next_leader.next_leader_slot - next_leader.current_slot
        print(f"waiting {num_slots_to_leader} slots to jito leader")
        is_leader_slot = num_slots_to_leader <= 2

    # Build bundle
    txs: List[Transaction] = []
    for idx in range(num_txs):
        ixs = [
            create_memo(
                MemoParams(
                    program_id=Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"),
                    signer=payer_kp.pubkey(),
                    message=bytes(f"jito bundle {idx}: {message}", "utf-8"),
                )
            )
        ]
        if idx == num_txs - 1:
            # Adds searcher tip on last tx
            ixs.append(
                transfer(TransferParams(from_pubkey=payer_kp.pubkey(), to_pubkey=tip_account, lamports=lamports))
            )
        tx = Transaction.new_signed_with_payer(
            instructions=ixs, payer=payer_kp.pubkey(), signing_keypairs=[payer_kp], recent_blockhash="BLOCKHASH_PLACEHOLDER"
        )
        print(f"{idx=} signature={tx.signatures[0]}")
        txs.append(tx)

    # Note: setting meta.size here is important so the block engine can deserialize the packet
    packets = [tx_to_protobuf_packet(tx) for tx in txs]

    uuid_response = await client.SendBundle(SendBundleRequest(bundle=Bundle(header=None, packets=packets)))
    print(f"bundle uuid: {uuid_response.uuid}")

if __name__ == "__main__":
    # Example usage
    payer_kp = Keypair()  # Replace with your actual Keypair
    asyncio.run(send_bundle(
        block_engine_url="block-engine-url",
        payer_kp=payer_kp,
        message="Your message",
        num_txs=3,
        lamports=1000,
        tip_account_str="TipAccountPubkeyString"
    ))
