from plaid_integration.service import normalize_transaction


def test_normalize_transaction_maps_expense_to_mock_shape():
    payload = {
        'amount': 12.34,
        'date': '2024-06-15',
        'merchant_name': 'Starbucks',
        'personal_finance_category': {'primary': 'FOOD_AND_DRINK'},
    }

    normalized = normalize_transaction(payload)

    assert normalized['amount'] == 12.34
    assert normalized['date'] == '2024-06-15'
    assert normalized['merchant'] == 'Starbucks'
    assert normalized['category'] == 'Dining'


def test_normalize_transaction_maps_income_to_income_category():
    payload = {
        'amount': -1200.0,
        'date': '2024-06-20',
        'merchant_name': 'Payroll',
        'personal_finance_category': {'primary': 'INCOME'},
    }

    normalized = normalize_transaction(payload)

    assert normalized['amount'] == 1200.0
    assert normalized['category'] == 'Income'
    assert normalized['merchant'] == 'Payroll'
