#!/usr/bin/env python3
import argparse
import os
import sqlite3
from collections import defaultdict
from datetime import datetime

base_path = f"{os.environ['HOME']}/code/Python/cash_calculator"
backup_path = f"{base_path}/backup_storage.db"
db_path = f"{base_path}/main_storage.db"


def tmp_in_period(args):
    period_data = date_filter(args)
    exclude = args.exclude.split(",") if args.exclude else list()

    reasons_summary = defaultdict(float)
    total_income = 0
    total_outcome = 0
    for _, amount, reason in period_data:
        if any(s in reason for s in exclude):
            continue

        reasons_summary[reason] += amount
        if amount < 0:
            total_outcome += amount
        else:
            total_income += amount

    income = defaultdict(dict)
    outcome = defaultdict(dict)
    for reason, total_amount in reasons_summary.items():
        if total_amount < 0:
            outcome[reason] = {
                "value": abs(total_amount),
                "%": abs(total_amount / total_outcome * 100),
            }
        else:
            income[reason] = {
                "value": total_amount,
                "%": total_amount / total_income * 100,
            }

    formatter = "{:14}|{:6.2f}|{:7.0f}|{:50}|"
    print(formatter.format("total", 100.00, abs(total_outcome), ""))
    for reason, value in sorted(outcome.items(), key=lambda x: -x[1]["%"]):
        percents_bar = "=" * int(value["%"])
        print(
            formatter.format(reason, value['%'], value['value'], percents_bar))


def add_entry(args):
    amount = args.amount
    reason = args.reason
    write_transaction(amount, reason)


def date_filter(args):
    date_lt = args.date_less
    date_gt = args.date_greater
    condition = f"date<'{date_lt}' AND date>'{date_gt}'"
    rows = read_transactions(condition)

    return rows


def write_transaction(amount, reason):
    date = datetime.utcnow().isoformat(sep=" ", timespec="milliseconds")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS cash
        (date datetime, amount real, reason text)
    ''')
    c.execute(f'''
        INSERT INTO cash VALUES
        ('{date}',{amount},'{reason}')
    ''')
    conn.commit()

    conn.close()


def read_transactions(condition):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    rows = c.execute(f'''
        SELECT * FROM cash WHERE {condition}
    ''').fetchall()

    conn.close()

    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="cash")
    subparsers = parser.add_subparsers(help="sub-command help message")

    income_parser = subparsers.add_parser("update", help="update help message")
    income_parser.add_argument("amount", type=float, help="update value help message")
    income_parser.add_argument("reason", type=str, help="update reason help message")
    income_parser.set_defaults(func=add_entry)

    income_in_period_parser = subparsers.add_parser("tmp_in_period", help="tmp_in_period help message")
    income_in_period_parser.add_argument("--date_less", "-lt", type=str, default="3000-01", help="tmp_in_period date_less help message")
    income_in_period_parser.add_argument("--date_greater", "-gt", type=str, default="1900-01", help="tmp_in_period date_greater help message")
    income_in_period_parser.add_argument("--exclude", "-e", type=str, default="", help="tmp_in_period exclude help message")
    income_in_period_parser.set_defaults(func=tmp_in_period)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)
