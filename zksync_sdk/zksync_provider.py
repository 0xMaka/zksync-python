from decimal import Decimal
from enum import Enum
from typing import List, Optional, Tuple, Union

from eth_typing import Address

from zksync_sdk.providers import JsonRPCProvider
from zksync_sdk.types import (AccountState, ContractAddress, EncodedTx, EthOpInfo, Fee,
                              SignatureType, Token, TokenLike, Tokens, TransactionDetails,
                              TxEthSignature, )


class Transaction:
    tx: EncodedTx
    signature: bytes


class EthSignature:
    type: SignatureType
    signature: str


class TxType(Enum):
    withdraw = "Withdraw"
    transfer = "Transfer"
    fast_withdraw = "FastWithdraw"
    change_pub_key = "ChangePubKeyOnchainAuth"


class ZkSyncProvider:
    def __init__(self, provider: JsonRPCProvider):
        self.provider = provider

    async def submit_tx(self, tx: EncodedTx, signature: Optional[TxEthSignature],
                        fast_processing: bool = False) -> str:
        signature = signature.dict() if signature is not None else None
        return await self.provider.request("tx_submit",
                                           [tx.dict(), signature, fast_processing])

    async def get_tokens(self) -> Tokens:
        data = await self.provider.request("tokens", None)
        tokens = [Token(**token) for token in data.values()]
        return Tokens(tokens=tokens)

    async def submit_txs_batch(self, transactions: List[Transaction],
                               signatures: Optional[
                                   Union[List[EthSignature], EthSignature]
                               ] = None):
        if signatures is None:
            signatures = []
        elif isinstance(signatures, EthSignature):
            signatures = [signatures]

        return await self.provider.request("submit_txs_batch", [transactions, signatures])

    async def get_contract_address(self) -> ContractAddress:
        data = await self.provider.request("contract_address", None)
        return ContractAddress(**data)

    async def get_state(self, address: str) -> AccountState:
        data = await self.provider.request("account_info", [address])
        return AccountState(**data)

    async def get_confirmations_for_eth_op_amount(self) -> int:
        return await self.provider.request("get_confirmations_for_eth_op_amount", None)

    async def get_account_nonce(self, address: str) -> Tuple[int, int]:
        state = await self.get_state(address)
        return state.id, state.get_nonce()

    async def get_tx_receipt(self, address: str) -> TransactionDetails:
        return await self.provider.request("tx_info", [address])

    async def get_eth_tx_for_withdrawal(self, withdrawal_hash: str) -> str:
        return await self.provider.request("get_eth_tx_for_withdrawal", [withdrawal_hash])

    async def get_priority_op_status(self, serial_id: int) -> EthOpInfo:
        data = await self.provider.request("ethop_info", [serial_id])
        return EthOpInfo(**data)

    async def get_transactions_batch_fee(self, tx_types: List[TxType], addresses: List[Address],
                                         token_like) -> Fee:

        return await self.provider.request('get_txs_batch_fee_in_wei',
                                           [[tx_type.value for tx_type in tx_types],
                                            addresses, token_like])

    async def get_transaction_fee(self, tx_type: TxType, address: str,
                                  token_like: TokenLike) -> Fee:

        data = await self.provider.request('get_tx_fee', [tx_type.value, address, token_like])
        return Fee(**data)

    async def get_token_price(self, token: Token) -> Decimal:
        data = await self.provider.request('get_token_price', [token.symbol])
        return token.decimal_amount(int(data))
