from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas import WalletOperationRequest, WalletResponse
from app.services.wallets import WalletService


router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


@router.post("/{wallet_id}/operation", response_model=WalletResponse)
async def apply_wallet_operation(
    wallet_id: UUID,
    payload: WalletOperationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> WalletResponse:
    service = WalletService(session)
    wallet = await service.apply_operation(wallet_id=wallet_id, payload=payload)
    return WalletResponse.model_validate(wallet)


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> WalletResponse:
    service = WalletService(session)
    wallet = await service.get_wallet(wallet_id=wallet_id)
    return WalletResponse.model_validate(wallet)
