import os
import urllib.parse
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from azure.identity import DefaultAzureCredential
from sqlalchemy import BigInteger, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel, create_engine, insert, or_, select

from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

from config import get_database_engine


class Cards(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    client_id: int
    card_brand: str
    card_type: str
    card_number: str
    expires: date
    cvv: int = Field(default=None, sa_column=Column(SmallInteger()))
    has_chip: str
    num_cards_issued: int = Field(default=None, sa_column=Column(SmallInteger()))
    credit_limit: int = Field(default=None, sa_column=Column(BigInteger()))
    acct_open_date: date
    year_pin_last_changed: int = Field(default=None, sa_column=Column(SmallInteger()))
    card_on_dark_web: str
    source: Optional[str] | None = None


class Transactions(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    date: date
    client_id: int = Field(default=None, sa_column=Column(SmallInteger()))
    card_id: int = Field(default=None, sa_column=Column(SmallInteger()))
    amount: Decimal = Field(default=0, max_digits=18, decimal_places=2)
    use_chip: str
    merchant_id: int
    merchant_city: Optional[str] | None = None
    merchant_state: Optional[str] | None = None
    zip: Optional[int] | None = None
    mcc: Optional[int] | None = None
    errors: Optional[str] | None = None
    source: Optional[str] | None = None


class Users(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    current_age: int | None = Field(default=None, sa_column=Column(SmallInteger()))
    retirement_age: int | None = Field(default=None, sa_column=Column(SmallInteger()))
    birth_year: int | None = Field(default=None, sa_column=Column(SmallInteger()))
    birth_month: int | None = Field(default=None, sa_column=Column(SmallInteger()))
    gender: str
    address: str
    latitude: Decimal = Field(default=0, max_digits=18, decimal_places=2)
    longitude: Decimal = Field(default=0, max_digits=18, decimal_places=2)
    per_capita_income: int
    yearly_income: int
    total_debt: int
    credit_score: int = Field(default=None, sa_column=Column(BigInteger()))
    num_credit_cards: int = Field(default=None, sa_column=Column(SmallInteger()))
    source: Optional[str] | None = None


class DataImport(SQLModel, table=True):
    __tablename__ = "data_import"
    id: str | None = Field(default=None, primary_key=True)
    file_name: str
    size: int = Field(default=None, sa_column=Column(BigInteger()))
    created_at: Optional[datetime] | None = None
    last_modified_date: Optional[datetime] | None = None
    started_at: Optional[datetime] | None = None
    finished_at: Optional[datetime] | None = None
    users_status: Optional[str] | None = None
    cards_status: Optional[str] | None = None
    transactions_status: Optional[str] | None = None


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    id: int | None = Field(default=None, primary_key=True)
    table_name: str
    operation: str
    old_data: dict = Field(default=None, sa_column=Column(JSONB))
    new_data: dict = Field(default=None, sa_column=Column(JSONB))
    changed_at: datetime


class FailedImports(SQLModel, table=True):
    __tablename__ = "failed_imports"
    id: int | None = Field(default=None, primary_key=True)
    table_name: str
    error: str
    source: str


log_changes_function = PGFunction(
    schema="public",
    signature="log_changes()",
    definition="""
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'UPDATE' THEN
            -- Only log if something actually changed
            IF OLD IS DISTINCT FROM NEW THEN
                INSERT INTO audit_log (table_name, operation, old_data, new_data, changed_at) 
                VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), row_to_json(NEW), NOW());
            END IF;
        ELSIF TG_OP = 'INSERT' THEN
            INSERT INTO audit_log (table_name, operation, old_data, new_data, changed_at) 
            VALUES (TG_TABLE_NAME, TG_OP, NULL, row_to_json(NEW), NOW());
        ELSIF TG_OP = 'DELETE' THEN
            INSERT INTO audit_log (table_name, operation, old_data, new_data, changed_at) 
            VALUES (TG_TABLE_NAME, TG_OP, row_to_json(OLD), NULL, NOW());
        END IF;
        
        RETURN COALESCE(NEW, OLD);
    END;
    $$ LANGUAGE plpgsql;
    """,
)


audit_cards_trigger = PGTrigger(
    schema="public",
    signature="audit_cards_trigger",
    on_entity="public.cards",
    is_constraint=False,
    definition="""
    BEFORE INSERT OR UPDATE OR DELETE ON cards
    FOR EACH ROW EXECUTE FUNCTION log_changes()
    """,
)

audit_transactions_trigger = PGTrigger(
    schema="public",
    signature="audit_transactions_trigger",
    on_entity="public.transactions",
    is_constraint=False,
    definition="""
    BEFORE INSERT OR UPDATE OR DELETE ON transactions
    FOR EACH ROW EXECUTE FUNCTION log_changes()
    """,
)

audit_users_trigger = PGTrigger(
    schema="public",
    signature="audit_users_trigger",
    on_entity="public.users",
    is_constraint=False,
    definition="""
    BEFORE INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION log_changes()
    """,
)

audit_data_import_trigger = PGTrigger(
    schema="public",
    signature="audit_data_import_trigger",
    on_entity="public.data_import",
    is_constraint=False,
    definition="""
    BEFORE INSERT OR UPDATE OR DELETE ON data_import
    FOR EACH ROW EXECUTE FUNCTION log_changes()
    """,
)

engine = get_database_engine()
