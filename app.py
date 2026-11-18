
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)

from database import get_db_connection
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from dotenv import load_dotenv
import mysql.connector
import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from datetime import datetime
from datetime import datetime, date, timedelta
from analysis import generate_financial_reports
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")



@app.route("/")
def home():
    return render_template("register.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    message = ""
    message_type = ""

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if not name or not email or not password:
            message = "All fields are required."
            message_type = "danger"

        elif len(password) < 8:
            message = "Password must contain at least 8 characters."
            message_type = "danger"

        elif password != confirm_password:
            message = "Passwords do not match."
            message_type = "danger"

        else:

            connection = None
            cursor = None

            try:
                connection = get_db_connection()
                cursor = connection.cursor()

                hashed_password = generate_password_hash(password)

                query = """
                    INSERT INTO users
                    (full_name, email, password_hash)
                    VALUES (%s, %s, %s)
                """

                cursor.execute(
                    query,
                    (name, email, hashed_password)
                )

                connection.commit()

                message = "Registration successful!"
                message_type = "success"

            except mysql.connector.IntegrityError:
                if connection:
                    connection.rollback()

                message = "Email already registered."
                message_type = "danger"

            except mysql.connector.Error as error:
                if connection:
                    connection.rollback()

                print("REGISTRATION ERROR:", repr(error))

                message = "Database error. Please try again."
                message_type = "danger"

            finally:
                if cursor:
                    cursor.close()

                if connection:
                    connection.close()

    # IMPORTANT: This return must be outside the POST condition.
    return render_template(
        "register.html",
        message=message,
        message_type=message_type
    )


    
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                SELECT user_id, full_name, email, password_hash
                FROM users
                WHERE email = %s
            """

            cursor.execute(query, (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[3], password):

                session["user_id"] = user[0]
                session["user_name"] = user[1]

                return redirect(url_for("dashboard"))

            else:
                flash("Invalid email or password.", "danger")

        except mysql.connector.Error as error:
            print("LOGIN DATABASE ERROR:", repr(error))
            flash("Unable to process login. Try again.", "danger")

        finally:
            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    today = date.today()
    current_month_start = today.replace(day=1)

    # Calculate next month start.
    if current_month_start.month == 12:
        next_month_start = date(
            current_month_start.year + 1, 1, 1
        )
    else:
        next_month_start = date(
            current_month_start.year,
            current_month_start.month + 1,
            1
        )

    # Calculate previous month start.
    if current_month_start.month == 1:
        previous_month_start = date(
            current_month_start.year - 1, 12, 1
        )
    else:
        previous_month_start = date(
            current_month_start.year,
            current_month_start.month - 1,
            1
        )

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Current month financial summary.
        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE WHEN transaction_type = 'income'
                    THEN amount ELSE 0 END
                ), 0) AS total_income,

                COALESCE(SUM(
                    CASE WHEN transaction_type = 'expense'
                    THEN amount ELSE 0 END
                ), 0) AS total_expense,

                COUNT(
                    CASE WHEN transaction_type = 'expense'
                    THEN 1 END
                ) AS expense_count

            FROM transactions

            WHERE user_id = %s
            AND transaction_date >= %s
            AND transaction_date < %s
        """, (
            user_id,
            current_month_start,
            next_month_start
        ))

        current = cursor.fetchone()

        total_income = float(current["total_income"])
        total_expense = float(current["total_expense"])

        balance = total_income - total_expense

        expense_count = current["expense_count"]

        average_expense = (
            total_expense / expense_count
            if expense_count > 0 else 0
        )

        # Previous month financial summary.
        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE WHEN transaction_type = 'income'
                    THEN amount ELSE 0 END
                ), 0) AS total_income,

                COALESCE(SUM(
                    CASE WHEN transaction_type = 'expense'
                    THEN amount ELSE 0 END
                ), 0) AS total_expense

            FROM transactions

            WHERE user_id = %s
            AND transaction_date >= %s
            AND transaction_date < %s
        """, (
            user_id,
            previous_month_start,
            current_month_start
        ))

        previous = cursor.fetchone()

        previous_income = float(previous["total_income"])
        previous_expense = float(previous["total_expense"])

        # Calculate percentage changes.
        income_change = (
            ((total_income - previous_income) / previous_income) * 100
            if previous_income > 0 else None
        )

        expense_change = (
            ((total_expense - previous_expense) / previous_expense) * 100
            if previous_expense > 0 else None
        )

        # Highest expense category this month.
        cursor.execute("""
            SELECT
                COALESCE(c.category_name, 'Uncategorized')
                AS category_name,

                SUM(t.amount) AS total_amount

            FROM transactions t

            LEFT JOIN categories c
                ON t.category_id = c.category_id

            WHERE t.user_id = %s
            AND t.transaction_type = 'expense'
            AND t.transaction_date >= %s
            AND t.transaction_date < %s

            GROUP BY c.category_name

            ORDER BY total_amount DESC

            LIMIT 1
        """, (
            user_id,
            current_month_start,
            next_month_start
        ))

        highest_category = cursor.fetchone()

        # Latest five transactions.
        cursor.execute("""
            SELECT
                t.transaction_id,
                t.amount,
                t.transaction_type,
                t.description,
                t.transaction_date,

                COALESCE(c.category_name, 'Uncategorized')
                AS category_name

            FROM transactions t

            LEFT JOIN categories c
                ON t.category_id = c.category_id

            WHERE t.user_id = %s

            ORDER BY
                t.transaction_date DESC,
                t.created_at DESC

            LIMIT 5
        """, (user_id,))

        recent_transactions = cursor.fetchall()

        return render_template(
            "dashboard.html",

            full_name=(
                session.get("full_name")
                or session.get("name")
                or "User"
            ),

            total_income=total_income,
            total_expense=total_expense,
            balance=balance,

            previous_income=previous_income,
            previous_expense=previous_expense,

            income_change=income_change,
            expense_change=expense_change,

            average_expense=average_expense,
            highest_category=highest_category,

            recent_transactions=recent_transactions,

            current_month=today.strftime("%B %Y")
        )

    finally:
        cursor.close()
        connection.close()



@app.route("/add-transaction", methods=["GET", "POST"])
def add_transaction():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        transaction_type = request.form.get("transaction_type")
        category_name = request.form.get("category_name", "").strip()
        amount = request.form.get("amount", "").strip()
        transaction_date = request.form.get("transaction_date")
        description = request.form.get("description", "").strip()

        if transaction_type not in ["income", "expense"]:
            return "Invalid transaction type.", 400

        if not category_name or not amount or not transaction_date:
            return "Please fill in all required fields.", 400

        try:
            amount = float(amount)

            if amount <= 0:
                return "Amount must be greater than zero.", 400

            datetime.strptime(transaction_date, "%Y-%m-%d")

        except ValueError:
            return "Enter a valid amount and date.", 400

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            user_id = session["user_id"]

            connection.start_transaction()

            # Check whether the category already exists
            cursor.execute("""
                SELECT category_id
                FROM categories
                WHERE user_id = %s
                  AND category_name = %s
                  AND category_type = %s
            """, (user_id, category_name, transaction_type))

            category = cursor.fetchone()

            # Create category if it does not exist
            if category:
                category_id = category[0]
            else:
                cursor.execute("""
                    INSERT INTO categories
                    (user_id, category_name, category_type)
                    VALUES (%s, %s, %s)
                """, (user_id, category_name, transaction_type))

                category_id = cursor.lastrowid

            # Save transaction
            cursor.execute("""
                INSERT INTO transactions
                (user_id, category_id, amount,
                 transaction_type, description, transaction_date)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                category_id,
                amount,
                transaction_type,
                description,
                transaction_date
            ))

            connection.commit()

            return redirect(url_for("dashboard"))

        except Exception as error:
            if connection:
                connection.rollback()

            print("TRANSACTION ERROR:", repr(error))
            return "Unable to save transaction. Check the Flask terminal.", 500

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    return render_template("add_transaction.html")


# 1. VIEW AND SEARCH TRANSACTIONS
@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        search = request.args.get("search", "").strip()
        transaction_type = request.args.get("type", "").strip()
        start_date = request.args.get("start_date", "").strip()
        end_date = request.args.get("end_date", "").strip()

        query = """
            SELECT
                t.transaction_id,
                t.amount,
                t.transaction_type,
                t.description,
                t.transaction_date,
                c.category_name
            FROM transactions t
            LEFT JOIN categories c
                ON t.category_id = c.category_id
            WHERE t.user_id = %s
        """

        params = [session["user_id"]]

        if search:
            query += """
                AND (
                    t.description LIKE %s
                    OR c.category_name LIKE %s
                )
            """
            params.extend([f"%{search}%", f"%{search}%"])

        if transaction_type in ["income", "expense"]:
            query += " AND t.transaction_type = %s"
            params.append(transaction_type)

        if start_date:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
                query += " AND t.transaction_date >= %s"
                params.append(start_date)
            except ValueError:
                return "Invalid start date.", 400

        if end_date:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
                query += " AND t.transaction_date <= %s"
                params.append(end_date)
            except ValueError:
                return "Invalid end date.", 400

        if start_date and end_date and start_date > end_date:
            return "Start date cannot be after end date.", 400

        query += """
            ORDER BY t.transaction_date DESC,
                     t.created_at DESC
        """

        cursor.execute(query, tuple(params))
        all_transactions = cursor.fetchall()

        return render_template(
            "transactions.html",
            transactions=all_transactions,
            search=search,
            selected_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )

    except Exception as error:
        print("TRANSACTION HISTORY ERROR:", repr(error))
        return "Unable to load transactions.", 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 2. EDIT TRANSACTION
@app.route("/edit-transaction/<int:transaction_id>",
           methods=["GET", "POST"])
def edit_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                t.*,
                c.category_name
            FROM transactions t
            LEFT JOIN categories c
                ON t.category_id = c.category_id
            WHERE t.transaction_id = %s
              AND t.user_id = %s
        """, (transaction_id, session["user_id"]))

        transaction = cursor.fetchone()

        if not transaction:
            return "Transaction not found.", 404

        if request.method == "POST":

            transaction_type = request.form.get("transaction_type")
            category_name = request.form.get("category_name", "").strip()
            amount_input = request.form.get("amount", "").strip()
            transaction_date = request.form.get("transaction_date")
            description = request.form.get("description", "").strip()

            if transaction_type not in ["income", "expense"]:
                return "Invalid transaction type.", 400

            if not category_name or not amount_input or not transaction_date:
                return "Please fill in all required fields.", 400

            if len(category_name) > 100 or len(description) > 255:
                return "Text fields exceed their allowed length.", 400

            try:
                amount = Decimal(amount_input)

                if not amount.is_finite() or amount <= 0:
                    return "Amount must be greater than zero.", 400

                if amount.as_tuple().exponent < -2 or amount > Decimal("99999999.99"):
                    return "Enter a valid amount.", 400

                datetime.strptime(transaction_date, "%Y-%m-%d")

            except (InvalidOperation, ValueError):
                return "Enter a valid amount and date.", 400

            connection.start_transaction()

            cursor.execute("""
                SELECT category_id
                FROM categories
                WHERE user_id = %s
                  AND category_name = %s
                  AND category_type = %s
            """, (
                session["user_id"],
                category_name,
                transaction_type
            ))

            category = cursor.fetchone()

            if category:
                category_id = category["category_id"]
            else:
                cursor.execute("""
                    INSERT INTO categories
                    (user_id, category_name, category_type)
                    VALUES (%s, %s, %s)
                """, (
                    session["user_id"],
                    category_name,
                    transaction_type
                ))

                category_id = cursor.lastrowid

            cursor.execute("""
                UPDATE transactions
                SET category_id = %s,
                    amount = %s,
                    transaction_type = %s,
                    description = %s,
                    transaction_date = %s
                WHERE transaction_id = %s
                  AND user_id = %s
            """, (
                category_id,
                amount,
                transaction_type,
                description or None,
                transaction_date,
                transaction_id,
                session["user_id"]
            ))

            connection.commit()

            return redirect(url_for("transactions"))

        return render_template(
            "edit_transaction.html",
            transaction=transaction
        )

    except Exception as error:
        if connection:
            connection.rollback()

        print("EDIT TRANSACTION ERROR:", repr(error))
        return "Unable to edit transaction.", 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 3. DELETE TRANSACTION
@app.route("/delete-transaction/<int:transaction_id>",
           methods=["POST"])
def delete_transaction(transaction_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM transactions
            WHERE transaction_id = %s
              AND user_id = %s
        """, (transaction_id, session["user_id"]))

        connection.commit()

        if cursor.rowcount == 0:
            return "Transaction not found.", 404

        return redirect(url_for("transactions"))

    except Exception as error:
        if connection:
            connection.rollback()

        print("DELETE TRANSACTION ERROR:", repr(error))
        return "Unable to delete transaction.", 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.route("/categories", methods=["GET", "POST"])
def categories():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        error = None

        if request.method == "POST":
            category_name = request.form.get("category_name", "").strip()
            category_type = request.form.get("category_type", "").strip().lower()

            if not category_name:
                error = "Category name is required."
            elif len(category_name) > 100:
                error = "Category name cannot exceed 100 characters."
            elif category_type not in ["income", "expense"]:
                error = "Please select a valid category type."
            else:
                # Check whether this category already exists for this user.
                cursor.execute("""
                    SELECT category_id
                    FROM categories
                    WHERE user_id = %s
                    AND LOWER(category_name) = LOWER(%s)
                    AND category_type = %s
                """, (session["user_id"], category_name, category_type))

                existing_category = cursor.fetchone()

                if existing_category:
                    error = "This category already exists."
                else:
                    cursor.execute("""
                        INSERT INTO categories
                        (user_id, category_name, category_type)
                        VALUES (%s, %s, %s)
                    """, (session["user_id"], category_name, category_type))

                    connection.commit()
                    return redirect(url_for("categories", message="Category added successfully."))

        cursor.execute("""
            SELECT category_id, category_name, category_type
            FROM categories
            WHERE user_id = %s
            ORDER BY category_type, category_name
        """, (session["user_id"],))

        category_list = cursor.fetchall()

        return render_template(
            "categories.html",
            categories=category_list,
            error=error,
            message=request.args.get("message")
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


@app.route("/delete-category/<int:category_id>", methods=["POST"])
def delete_category(category_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Confirm that this category belongs to the logged-in user.
        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = %s AND user_id = %s
        """, (category_id, session["user_id"]))

        category = cursor.fetchone()

        if not category:
            return "Category not found.", 404

        # Do not delete categories already used by transactions.
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE category_id = %s AND user_id = %s
        """, (category_id, session["user_id"]))

        usage = cursor.fetchone()

        if usage["total"] > 0:
            return redirect(url_for(
                "categories",
                error="This category is used in transactions and cannot be deleted."
            ))

        cursor.execute("""
            DELETE FROM categories
            WHERE category_id = %s AND user_id = %s
        """, (category_id, session["user_id"]))

        connection.commit()

        return redirect(url_for(
            "categories",
            message="Category deleted successfully."
        ))

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


@app.route("/reports")
def reports():
    if "user_id" not in session:
        return redirect(url_for("login"))

    selected_month = request.args.get(
        "month", datetime.today().strftime("%Y-%m")
    )

    # Validate the selected month.
    try:
        datetime.strptime(selected_month, "%Y-%m")
    except ValueError:
        selected_month = datetime.today().strftime("%Y-%m")

    try:
        report_data = generate_financial_reports(
            session["user_id"],
            selected_month
        )

        return render_template(
            "reports.html",
            selected_month=selected_month,
            report=report_data
        )

    except Exception as error:
        print("REPORT GENERATION ERROR:", repr(error))
        return f"Unable to generate financial reports: {error}", 500



@app.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully.", "success")

    return redirect(url_for("login"))


    return render_template(
        "register.html",
        message=message,
        message_type=message_type
    )


if __name__ == "__main__":
    app.run(debug=True)
