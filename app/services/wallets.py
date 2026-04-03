from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Wallet
from app.schemas import OperationType, WalletOperationRequest


class WalletService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_wallet(self, wallet_id: UUID) -> Wallet:
        wallet = await self.session.scalar(
            select(Wallet).where(Wallet.id == wallet_id)
        )
        if wallet is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )
        return wallet

    async def apply_operation(
        self,
        wallet_id: UUID,
        payload: WalletOperationRequest,
    ) -> Wallet:
        async with self.session.begin():
            if payload.operation_type == OperationType.DEPOSIT:
                wallet = await self._deposit(
                    wallet_id=wallet_id,
                    amount=payload.amount,
                )
            else:
                wallet = await self._withdraw(
                    wallet_id=wallet_id,
                    amount=payload.amount,
                )
        return wallet

    async def _deposit(self, wallet_id: UUID, amount) -> Wallet:
        statement = (
            update(Wallet)
            .where(Wallet.id == wallet_id)
            .values(balance=Wallet.balance + amount)
            .returning(Wallet)
        )
        result = await self.session.execute(statement)
        wallet = result.scalar_one_or_none()
        if wallet is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )
        return wallet

    async def _withdraw(self, wallet_id: UUID, amount) -> Wallet:
        statement = (
            update(Wallet)
            .where(Wallet.id == wallet_id, Wallet.balance >= amount)
            .values(balance=Wallet.balance - amount)
            .returning(Wallet)
        )
        result = await self.session.execute(statement)
        wallet = result.scalar_one_or_none()

        if wallet is not None:
            return wallet

        wallet_exists = await self.session.scalar(
            select(Wallet.id).where(Wallet.id == wallet_id)
        )
        if wallet_exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet not found",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds",
        )
