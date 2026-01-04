import pytest
import pandas as pd


@pytest.fixture
def cards_data():
    file_path = "Sample Financial Transactions Dataset.xlsx"
    cards = pd.read_excel(open(file_path, "rb"), sheet_name="cards")

    return cards


@pytest.fixture
def users_data():
    file_path = "Sample Financial Transactions Dataset.xlsx"
    users = pd.read_excel(open(file_path, "rb"), sheet_name="users")

    return users


@pytest.fixture
def transactions_data():
    file_path = "Sample Financial Transactions Dataset.xlsx"
    transactions = pd.read_excel(
        open(file_path, "rb"), sheet_name="transactions")

    return transactions


def test_cards_data(cards_data):

    expected_columns = [
        "id",
        "client_id",
        "card_brand",
        "card_type",
        "card_number",
        "expires",
        "cvv",
        "has_chip",
        "num_cards_issued",
        "credit_limit",
        "acct_open_date",
        "year_pin_last_changed",
        "card_on_dark_web",
    ]

    assert len(cards_data.columns) == len(expected_columns)
    assert set(cards_data.columns) == set(expected_columns)


def test_users_data(users_data):
    expected_columns = [
        "id",
        "current_age",
        "retirement_age",
        "birth_year",
        "birth_month",
        "gender",
        "address",
        "latitude",
        "longitude",
        "per_capita_income",
        "yearly_income",
        "total_debt",
        "credit_score",
        "num_credit_cards",
    ]

    assert len(users_data.columns) == len(expected_columns)
    assert set(users_data.columns) == set(expected_columns)


def test_transactions_data(transactions_data):
    expected_columns = [
        "id",
        "date",
        "client_id",
        "card_id",
        "amount",
        "use_chip",
        "merchant_id",
        "merchant_city",
        "merchant_state",
        "zip",
        "mcc",
        "errors"
    ]

    assert len(transactions_data.columns) == len(expected_columns)
    assert set(transactions_data.columns) == set(expected_columns)
