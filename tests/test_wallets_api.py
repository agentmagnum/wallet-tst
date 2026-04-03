import asyncio
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_wallet_balance(client: AsyncClient, wallet_factory):
    wallet_id = await wallet_factory(Decimal("125.50"))

    response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(wallet_id),
        "balance": "125.50",
    }


@pytest.mark.asyncio
async def test_deposit_and_withdraw(client: AsyncClient, wallet_factory):
    wallet_id = await wallet_factory()

    deposit_response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "100.00"},
    )
    withdraw_response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": "40.00"},
    )

    assert deposit_response.status_code == 200
    assert deposit_response.json()["balance"] == "100.00"
    assert withdraw_response.status_code == 200
    assert withdraw_response.json()["balance"] == "60.00"


@pytest.mark.asyncio
async def test_withdraw_fails_when_balance_is_not_enough(
    client: AsyncClient,
    wallet_factory,
):
    wallet_id = await wallet_factory(Decimal("50.00"))

    response = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": "70.00"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Insufficient funds"}


@pytest.mark.asyncio
async def test_concurrent_deposits_are_accumulated(
    client: AsyncClient,
    wallet_factory,
):
    wallet_id = await wallet_factory()

    responses = await asyncio.gather(
        *[
            client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": "100.00"},
            )
            for _ in range(10)
        ]
    )

    assert all(response.status_code == 200 for response in responses)

    balance_response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert balance_response.status_code == 200
    assert balance_response.json()["balance"] == "1000.00"


@pytest.mark.asyncio
async def test_concurrent_withdrawals_do_not_allow_overspending(
    client: AsyncClient,
    wallet_factory,
):
    wallet_id = await wallet_factory(Decimal("300.00"))

    responses = await asyncio.gather(
        *[
            client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": "100.00"},
            )
            for _ in range(5)
        ]
    )

    success_responses = [response for response in responses if response.status_code == 200]
    failed_responses = [response for response in responses if response.status_code == 400]

    assert len(success_responses) == 3
    assert len(failed_responses) == 2
    assert all(
        response.json()["detail"] == "Insufficient funds"
        for response in failed_responses
    )

    balance_response = await client.get(f"/api/v1/wallets/{wallet_id}")

    assert balance_response.status_code == 200
    assert balance_response.json()["balance"] == "0.00"
