
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)


# =========================
# DATABASE CONNECTION
# =========================

def get_db():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection


# =========================
# CREATE DATABASE
# =========================

def create_database():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL DEFAULT 0
        )
    """)

    # Create default budget if one does not exist
    cursor.execute("SELECT COUNT(*) FROM budget")
    budget_count = cursor.fetchone()[0]

    if budget_count == 0:
        cursor.execute("""
            INSERT INTO budget (amount)
            VALUES (0)
        """)

    connection.commit()
    connection.close()


# =========================
# DASHBOARD
# =========================

@app.route("/")
def home():

    connection = get_db()
    cursor = connection.cursor()

    # Get all expenses
    cursor.execute("""
        SELECT *
        FROM expenses
        ORDER BY id DESC
    """)

    expenses = cursor.fetchall()

    # Calculate total expenses
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """)

    total_expenses = cursor.fetchone()[0]

    # Count transactions
    cursor.execute("""
        SELECT COUNT(*)
        FROM expenses
    """)

    transaction_count = cursor.fetchone()[0]

    # Get budget
    cursor.execute("""
        SELECT amount
        FROM budget
        WHERE id = 1
    """)

    budget_result = cursor.fetchone()

    if budget_result:
        budget = budget_result[0]
    else:
        budget = 0

    # Calculate remaining budget
    remaining_budget = budget - total_expenses

    connection.close()

    return render_template(
        "index.html",
        expenses=expenses,
        total_expenses=total_expenses,
        transaction_count=transaction_count,
        budget=budget,
        remaining_budget=remaining_budget
    )


# =========================
# ADD EXPENSE
# =========================

@app.route("/add", methods=["POST"])
def add_expense():

    date = request.form.get("date")
    category = request.form.get("category")
    description = request.form.get("description")
    amount = request.form.get("amount")

    # Make sure all fields are filled
    if not date or not category or not description or not amount:
        return redirect("/")

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO expenses
        (date, category, description, amount)
        VALUES (?, ?, ?, ?)
    """, (
        date,
        category,
        description,
        amount
    ))

    connection.commit()
    connection.close()

    return redirect("/")


# =========================
# DELETE EXPENSE
# =========================

@app.route("/delete/<int:id>")
def delete_expense(id):

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM expenses
        WHERE id = ?
    """, (id,))

    connection.commit()
    connection.close()

    return redirect("/")


# =========================
# EDIT EXPENSE
# =========================

@app.route("/edit/<int:id>")
def edit_expense(id):

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM expenses
        WHERE id = ?
    """, (id,))

    expense = cursor.fetchone()

    connection.close()

    if expense is None:
        return redirect("/")

    return render_template(
        "edit.html",
        expense=expense
    )


# =========================
# UPDATE EXPENSE
# =========================

@app.route("/update/<int:id>", methods=["POST"])
def update_expense(id):

    date = request.form.get("date")
    category = request.form.get("category")
    description = request.form.get("description")
    amount = request.form.get("amount")

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE expenses
        SET date = ?,
            category = ?,
            description = ?,
            amount = ?
        WHERE id = ?
    """, (
        date,
        category,
        description,
        amount,
        id
    ))

    connection.commit()
    connection.close()

    return redirect("/")


# =========================
# REPORTS
# =========================

@app.route("/reports")
def reports():

    connection = get_db()
    cursor = connection.cursor()

    # Total spending
    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """)

    total_spending = cursor.fetchone()[0]

    # Number of transactions
    cursor.execute("""
        SELECT COUNT(*)
        FROM expenses
    """)

    transaction_count = cursor.fetchone()[0]

    # Spending by category
    cursor.execute("""
        SELECT category,
               SUM(amount) AS total
        FROM expenses
        GROUP BY category
        ORDER BY total DESC
    """)

    category_data = cursor.fetchall()

    # Current month spending
    current_month = datetime.now().strftime("%Y-%m")

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE substr(date, 1, 7) = ?
    """, (current_month,))

    monthly_spending = cursor.fetchone()[0]

    # Monthly spending
    cursor.execute("""
        SELECT substr(date, 1, 7) AS month,
               SUM(amount) AS total
        FROM expenses
        GROUP BY substr(date, 1, 7)
        ORDER BY month
    """)

    monthly_data = cursor.fetchall()

    # Highest spending category
    if category_data:
        highest_category = category_data[0]["category"]
    else:
        highest_category = "None"

    connection.close()

    return render_template(
        "reports.html",
        total_spending=total_spending,
        transaction_count=transaction_count,
        monthly_spending=monthly_spending,
        highest_category=highest_category,
        category_data=category_data,
        monthly_data=monthly_data
    )


# =========================
# SET BUDGET
# =========================

@app.route("/set-budget", methods=["POST"])
def set_budget():

    amount = request.form.get("budget")

    if not amount:
        return redirect("/")

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE budget
        SET amount = ?
        WHERE id = 1
    """, (amount,))

    connection.commit()
    connection.close()

    return redirect("/")


# =========================
# ABOUT PAGE
# =========================

@app.route("/about")
def about():
    return render_template("about.html")


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":
    create_database()

    app.run(
        debug=True
    )