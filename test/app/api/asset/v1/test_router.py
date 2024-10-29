from app.module.asset.enum import AccountType, InvestmentBankType
from icecream import ic

class TestGetBankAccounts:
    """
    api: /api/v1/bank-accounts
    method: GET
    """

    async def test_get_bank_accounts(self, client):
        # given
        response = client.get("/api/v1/bank-accounts")

        # when
        response_data = response.json()
        expected_investment_banks = [bank.value for bank in InvestmentBankType]
        expected_account_types = [account.value for account in AccountType]

        # then
        assert response_data["investment_bank_list"] == expected_investment_banks
        assert response_data["account_list"] == expected_account_types


class TestGetStockList:
    """
    api: /api/v1/stocks
    method: GET
    """

    async def test_get_stock_list(self, client, setup_stock):
        # Given
        setup_stock

        # When
        response = client.get("/api/v1/stocks")

        # Then
        response_data = response.json()
        
        expected_stocks = [
            {"name": "애플", "code": "AAPL"},
            {"name": "테슬라", "code": "TSLA"},
            {"name": "삼성전자", "code": "005930"},
        ]

        assert response_data == expected_stocks
