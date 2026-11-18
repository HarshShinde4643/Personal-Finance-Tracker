
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from database import get_db_connection
from datetime import datetime


# ----------------------------------
# PROJECT FOLDERS
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "static" / "charts"

CHART_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="deep")


# ----------------------------------
# FINANCIAL REPORT GENERATOR
# ----------------------------------

def generate_financial_reports(user_id, selected_month):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                t.amount,
                t.transaction_type,
                t.transaction_date,
                COALESCE(c.category_name, 'Uncategorized')
                AS category_name

            FROM transactions t

            LEFT JOIN categories c
                ON t.category_id = c.category_id

            WHERE t.user_id = %s

            ORDER BY t.transaction_date
        """, (user_id,))

        records = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    # ----------------------------------
    # DATA PREPARATION USING PANDAS
    # ----------------------------------

    df = pd.DataFrame(records)

    if df.empty:
        df = pd.DataFrame(columns=[
            "amount",
            "transaction_type",
            "transaction_date",
            "category_name"
        ])

    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce"
    ).fillna(0)

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce"
    )

    df = df.dropna(subset=["transaction_date"])

    selected_period = pd.Period(
        selected_month,
        freq="M"
    )

    monthly_df = df[
        df["transaction_date"].dt.to_period("M")
        == selected_period
    ].copy()

    # Separate income and expenses.
    income_df = monthly_df[
        monthly_df["transaction_type"] == "income"
    ]

    expense_df = monthly_df[
        monthly_df["transaction_type"] == "expense"
    ]

    # ----------------------------------
    # FINANCIAL CALCULATIONS USING NUMPY
    # ----------------------------------

    total_income = float(
        np.sum(income_df["amount"])
    )

    total_expense = float(
        np.sum(expense_df["amount"])
    )

    balance = total_income - total_expense

    average_expense = (
        float(np.mean(expense_df["amount"]))
        if not expense_df.empty else 0.0
    )

    # Savings rate and expense ratio.
    savings_rate = (
        (balance / total_income) * 100
        if total_income > 0 else 0.0
    )

    expense_ratio = (
        (total_expense / total_income) * 100
        if total_income > 0 else 0.0
    )

    # Create unique chart version for browser refresh.
    chart_version = int(datetime.now().timestamp())

    file_prefix = (
        f"user_{user_id}_{selected_month}"
    )

    # ----------------------------------
    # CHART 1: INCOME VS EXPENSES
    # ----------------------------------

    income_expense_path = CHART_DIR / (
        f"{file_prefix}_income_expense.png"
    )

    fig, ax = plt.subplots(figsize=(6, 3.2))

    ax.bar(
        ["Income", "Expenses"],
        [total_income, total_expense],
        color=["#28A36A", "#E85D5D"],
        width=0.5
    )

    ax.set_ylabel("Amount (INR)")
    ax.set_title("Income vs Expenses")

    ax.ticklabel_format(
        style="plain",
        axis="y"
    )

    ax.grid(axis="x", visible=False)

    fig.tight_layout()
    fig.savefig(income_expense_path, dpi=130)
    plt.close(fig)

    # ----------------------------------
    # CHART 2: EXPENSE PIE CHART
    # ----------------------------------

    pie_path = CHART_DIR / (
        f"{file_prefix}_expense_pie.png"
    )

    fig, ax = plt.subplots(figsize=(6, 3.2))

    if not expense_df.empty:

        category_data = (
            expense_df.groupby("category_name")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        ax.pie(
            category_data.values,
            labels=category_data.index,
            autopct="%1.1f%%",
            startangle=90,
            pctdistance=0.75,
            textprops={"fontsize": 8},
            wedgeprops={
                "width": 0.45,
                "edgecolor": "white"
            }
        )

        ax.set_title("Expense Distribution")

    else:
        ax.text(
            0.5, 0.5,
            "No expense data available",
            ha="center",
            va="center"
        )

        ax.axis("off")

    fig.tight_layout()
    fig.savefig(pie_path, dpi=130)
    plt.close(fig)

    # ----------------------------------
    # CHART 3: SIX-MONTH FINANCIAL TREND
    # ----------------------------------

    trend_path = CHART_DIR / (
        f"{file_prefix}_trend.png"
    )

    start_period = selected_period - 5

    trend_df = df[
        (
            df["transaction_date"].dt.to_period("M")
            >= start_period
        )
        &
        (
            df["transaction_date"].dt.to_period("M")
            <= selected_period
        )
    ].copy()

    trend_df["month"] = (
        trend_df["transaction_date"].dt.to_period("M")
    )

    trend_summary = trend_df.pivot_table(
        index="month",
        columns="transaction_type",
        values="amount",
        aggfunc="sum",
        fill_value=0
    )

    months = pd.period_range(
        start=start_period,
        end=selected_period,
        freq="M"
    )

    trend_summary = trend_summary.reindex(
        months,
        fill_value=0
    )

    for transaction_type in ["income", "expense"]:

        if transaction_type not in trend_summary.columns:
            trend_summary[transaction_type] = 0

    trend_summary = trend_summary[
        ["income", "expense"]
    ]

    fig, ax = plt.subplots(figsize=(12, 3.2))

    ax.plot(
        months.strftime("%b %Y"),
        trend_summary["income"].values,
        marker="o",
        linewidth=2,
        label="Income",
        color="#2799D2"
    )

    ax.plot(
        months.strftime("%b %Y"),
        trend_summary["expense"].values,
        marker="o",
        linewidth=2,
        label="Expenses",
        color="#E85D5D"
    )

    ax.set_title("Six-Month Financial Trend")
    ax.set_ylabel("Amount (INR)")

    ax.tick_params(axis="x", rotation=0)

    ax.legend(
        loc="upper left",
        frameon=True
    )

    fig.tight_layout()
    fig.savefig(trend_path, dpi=130)
    plt.close(fig)

    # ----------------------------------
    # CHART 4: CATEGORY-WISE EXPENSES
    # ----------------------------------

    category_path = CHART_DIR / (
        f"{file_prefix}_categories.png"
    )

    fig, ax = plt.subplots(figsize=(6, 3.2))

    if not expense_df.empty:

        category_data = (
            expense_df.groupby("category_name")["amount"]
            .sum()
            .sort_values(ascending=True)
            .reset_index()
        )

        sns.barplot(
            data=category_data,
            x="amount",
            y="category_name",
            color="#5879AA",
            ax=ax
        )

        ax.set_xlabel("Total Expense (INR)")
        ax.set_ylabel("")

    else:

        ax.text(
            0.5, 0.5,
            "No expense data available",
            ha="center",
            va="center"
        )

        ax.axis("off")

    ax.set_title("Category-wise Expenses")

    fig.tight_layout()
    fig.savefig(category_path, dpi=130)
    plt.close(fig)

    # ----------------------------------
    # CHART 5: WEEKLY SPENDING HEATMAP
    # ----------------------------------

    heatmap_path = CHART_DIR / (
        f"{file_prefix}_heatmap.png"
    )

    fig, ax = plt.subplots(figsize=(6, 3.2))

    if not expense_df.empty:

        heatmap_df = expense_df.copy()

        heatmap_df["week"] = (
            (heatmap_df["transaction_date"].dt.day - 1)
            // 7
        ) + 1

        heatmap_df["weekday"] = (
            heatmap_df["transaction_date"].dt.day_name()
        )

        weekday_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday"
        ]

        heatmap_data = heatmap_df.pivot_table(
            index="week",
            columns="weekday",
            values="amount",
            aggfunc="sum",
            fill_value=0
        )

        heatmap_data = heatmap_data.reindex(
            index=[1, 2, 3, 4, 5],
            columns=weekday_order,
            fill_value=0
        )

        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=".0f",
            cmap="YlOrRd",
            linewidths=0.5,
            cbar=False,
            ax=ax
        )

        ax.set_xlabel("Day of Week")
        ax.set_ylabel("Week of Month")
        ax.set_title("Weekly Spending Heatmap")

        ax.tick_params(axis="x", labelrotation=25)

    else:

        ax.text(
            0.5, 0.5,
            "No expense data available",
            ha="center",
            va="center"
        )

        ax.axis("off")

    fig.tight_layout()
    fig.savefig(heatmap_path, dpi=130)
    plt.close(fig)

    # ----------------------------------
    # RETURN REPORT DATA TO FLASK
    # ----------------------------------

    return {

        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "average_expense": average_expense,

        "savings_rate": savings_rate,
        "expense_ratio": expense_ratio,

        "chart_version": chart_version,

        "income_expense_chart": (
            f"charts/{income_expense_path.name}"
        ),

        "pie_chart": (
            f"charts/{pie_path.name}"
        ),

        "category_chart": (
            f"charts/{category_path.name}"
        ),

        "trend_chart": (
            f"charts/{trend_path.name}"
        ),

        "heatmap_chart": (
            f"charts/{heatmap_path.name}"
        )
    }
