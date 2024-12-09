import mysql.connector  # Connect to MySQL database
import streamlit as st  # Build the frontend
import pandas as pd  # Work with tabular data
import bcrypt
import os  # Use for secure password storage

# Connecting to database
def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user= os.getenv('USERNAME'),
        password= os.getenv('PASSWORD'),
        database="expense_tracker"
    )


def main():
    # User authentication
    if 'user_id' not in st.session_state:
        authentication = ["Register", "Login"]
        authentication_choice = st.sidebar.selectbox("Choose an option:", authentication)
        if authentication_choice == "Register":
            register_user()
        elif authentication_choice == "Login":
            login_user()
    else:
        st.title(f"Welcome User {st.session_state['user_id']}!")

# Main menu with updated options
        menu = [
            "View Expenses",
            "Add Expense",
            "Edit Expense",
            "Delete Expense",
            "View Date-Range Expenses",
            "Generate Report",
            "Search Expenses",
            "Analyze Spending Trends",
            "Set Budget",
            "Transaction Example (Rollback)",
            "Logout"
        ]
        choice = st.sidebar.selectbox("Menu", menu)

        # Map user choices to their respective functions
        if choice == "View Expenses":
            view_expenses_sorted(st.session_state['user_id'])
        elif choice == "Add Expense":
            add_expense(st.session_state['user_id'])
        elif choice == "Edit Expense":
            edit_expense(st.session_state['user_id'])
        elif choice == "Delete Expense":
            delete_expense(st.session_state['user_id'])
        elif choice == "View Date-Range Expenses":
            view_expenses_by_date(st.session_state['user_id'])
        elif choice == "Generate Report":
            generate_report(st.session_state['user_id'])
        elif choice == "Analyze Spending Trends":
            analyze_spending_trends(st.session_state['user_id'])
        elif choice == "Set Budget":
            set_budget(st.session_state['user_id'])
        elif choice == "Transaction Example (Rollback)":
            update_expense_transaction(st.session_state['user_id'])
        elif choice == "Logout":
            st.session_state.pop('user_id', None)
            st.success("Logged out successfully!")




def login_user():
    st.subheader("User Login")
    email = st.text_input("Enter Email:")
    password = st.text_input("Enter Password:", type="password")

    if st.button("Login"):
        with connect_to_db() as connection:
            cursor = connection.cursor()
            query = "SELECT User_ID, Password FROM User WHERE Email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()

            if result:
                user_id, hashed_password = result
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    st.session_state['user_id'] = user_id
                    st.success("Login successful!")
                    main()
                else:
                    st.error("Incorrect password.")
            else:
                st.error("User not found.")


def register_user():
    st.subheader("Register New User")
    username = st.text_input("Enter Username:")
    email = st.text_input("Enter Email:")
    password = st.text_input("Enter Password:", type="password")
    confirm_password = st.text_input("Confirm Password:", type="password")

    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        with connect_to_db() as connection:
            cursor = connection.cursor()
            query = "INSERT INTO User (Username, Email, Password) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, email, hashed_password))
            connection.commit()
            st.success("Registration successful! You can now log in.")

#Sorts Expense by either asc or desc order
def view_expenses_sorted(user_id):
    st.subheader("View Expenses (Sorted)")
    sort_by = st.selectbox("Sort By:", ["Date", "Amount"])
    order = st.radio("Order:", ["Ascending", "Descending"])

    with connect_to_db() as connection:
        cursor = connection.cursor()
        query = f"""
        SELECT Expense_ID, Description, Amount, Date
        FROM Expense
        WHERE User_ID = %s
        ORDER BY {sort_by} {'ASC' if order == 'Ascending' else 'DESC'}
        """
        cursor.execute(query, (user_id,))
        expenses = cursor.fetchall()

        if expenses:
            columns = ["Expense ID", "Description", "Amount", "Date"]
            df = pd.DataFrame(expenses, columns=columns)
            st.table(df)
        else:
            st.warning("No expenses found.")


def add_expense(user_id):
    st.subheader("Add Expense")
        # Fetching and display the Category table
    with connect_to_db() as connection:
        cursor = connection.cursor()
        query_fetch_category = "SELECT Category_ID, Category_Name FROM Category"
        cursor.execute(query_fetch_category)
        categories = cursor.fetchall()

        if categories:
            category_columns = ["Category ID", "Category Name"]
            category_df = pd.DataFrame(categories, columns=category_columns)
            st.write("### Available Categories")
            st.table(category_df)
        else:
            st.warning("No categories found. Please add categories first.")
    # Inputs for adding a new expense
    description = st.text_input("Enter Expense Description:")
    amount = st.number_input("Enter Amount:", min_value=0.0)
    date = st.date_input("Enter Date:")
    category_id = st.number_input("Enter Category ID:", min_value=1, step=1)  # Use Category_ID

    if st.button("Add Expense"):
        with connect_to_db() as connection:
            cursor = connection.cursor()

            # Insert new expense into the database
            query_insert = """
            INSERT INTO Expense (Amount, Date, Description, User_ID, Category_ID)
            VALUES (%s, %s, %s, %s, %s)
            """  # Use Category_ID
            cursor.execute(query_insert, (amount, date, description, user_id, category_id))
            connection.commit()
            st.success("Expense added successfully!")

            # Fetching and display all expenses for the user
            query_fetch = "SELECT Expense_ID, Description, Amount, Date FROM Expense WHERE User_ID = %s"
            cursor.execute(query_fetch, (user_id,))
            expenses = cursor.fetchall()

            if expenses:
                columns = ["Expense ID", "Description", "Amount", "Date"]
                df = pd.DataFrame(expenses, columns=columns)
                st.write("### Current Expenses")
                st.table(df)
            else:
                st.warning("No expenses found for this user.")


def edit_expense(user_id):
    st.subheader("Edit Expense")
    expense_id = st.number_input("Expense ID:", min_value=1, step=1)
    new_description = st.text_input("New Description:")
    new_amount = st.number_input("New Amount:", min_value=0.01)
    new_date = st.date_input("New Date:")
    
    # Fetching and displaying current expenses for the user
    with connect_to_db() as connection:
        cursor = connection.cursor()
        query_fetch = "SELECT Expense_ID, Description, Amount, Date FROM Expense WHERE User_ID = %s"
        cursor.execute(query_fetch, (user_id,))
        expenses = cursor.fetchall()

        if expenses:
            columns = ["Expense ID", "Description", "Amount", "Date"]
            df = pd.DataFrame(expenses, columns=columns)
            st.write("### Current Expenses")
            st.table(df)
        else:
            st.warning("No expenses found for this user.")
            return

    if st.button("Update Expense"):
        with connect_to_db() as connection:
            cursor = connection.cursor()
            query = "UPDATE Expense SET Description = %s, Amount = %s, Date = %s WHERE Expense_ID = %s AND User_ID = %s"
            cursor.execute(query, (new_description, new_amount, new_date, expense_id, user_id))
            connection.commit()
            st.success("Expense updated successfully.")

            cursor.execute(query_fetch,(user_id,))
            updated_expense = cursor.fetchall()
            
            if updated_expense:
                updated_df = pd.DataFrame(updated_expense, columns=columns)
                st.write("### Updated Expenses")
                st.table(updated_df)
            else:
                st.warning("No expenses found for this user.")





def delete_expense(user_id):
    st.subheader("Delete Expense")
    
    with connect_to_db() as connection:
        cursor = connection.cursor()
        
        # Fetch and display current expenses for the user
        query_fetch = "SELECT Expense_ID, Description, Amount, Date FROM Expense WHERE User_ID = %s"
        cursor.execute(query_fetch, (user_id,))
        expenses = cursor.fetchall()
        
        if expenses:
            columns = ["Expense ID", "Description", "Amount", "Date"]
            df = pd.DataFrame(expenses, columns=columns)
            st.write("### Current Expenses")
            st.table(df)
        else:
            st.warning("No expenses found for this user.")
            return
    
    # Input to delete a specific expense
    expense_id = st.number_input("Expense ID to delete:", min_value=1, step=1)
    
    if st.button("Delete Expense"):
        with connect_to_db() as connection:
            cursor = connection.cursor()
            
            # Check if the expense exists
            query_check = "SELECT * FROM Expense WHERE Expense_ID = %s AND User_ID = %s"
            cursor.execute(query_check, (expense_id, user_id))
            existing_expense = cursor.fetchone()
            
            if existing_expense:
                # Proceed with deletion
                query_delete = "DELETE FROM Expense WHERE Expense_ID = %s AND User_ID = %s"
                cursor.execute(query_delete, (expense_id, user_id))
                connection.commit()
                st.success("Expense deleted successfully.")
            else:
                st.warning("Expense ID does not exist for the current user.")
                return
            
            # Fetch and display updated expenses
            cursor.execute(query_fetch, (user_id,))
            updated_expenses = cursor.fetchall()
            
            if updated_expenses:
                updated_df = pd.DataFrame(updated_expenses, columns=columns)
                st.write("### Updated Expenses")
                st.table(updated_df)
            else:
                st.warning("No expenses remaining for this user.")
    


def view_expenses_by_date(user_id):
    st.subheader("View Expenses by Date Range")
    start_date = st.date_input("Start Date:")
    end_date = st.date_input("End Date:")

    if st.button("View Expenses"):
        with connect_to_db() as connection:
            cursor = connection.cursor()
            query = "SELECT * FROM Expense WHERE User_ID = %s AND Date BETWEEN %s AND %s"
            cursor.execute(query, (user_id, start_date, end_date))
            expenses = cursor.fetchall()

            if expenses:
                columns = [col[0] for col in cursor.description]
                df = pd.DataFrame(expenses, columns=columns)
                st.table(df)
            else:
                st.warning("No expenses found for this date range.")



def generate_report(user_id):
    st.subheader("Generate Monthly Spending Report")
    month = st.number_input("Select Month:", min_value=1, max_value=12, step=1)
    year = st.number_input("Enter Year:", min_value=2000, max_value=2100, step=1)

    if st.button("Generate Report"):
        with connect_to_db() as connection:
            cursor = connection.cursor()
            query = """
            SELECT Category.Category_Name, SUM(Expense.Amount) AS Total_Spent
            FROM Expense
            JOIN Category ON Expense.Category_ID = Category.Category_ID
            WHERE Expense.User_ID = %s AND MONTH(Expense.Date) = %s AND YEAR(Expense.Date) = %s
            GROUP BY Category.Category_Name
            """
            cursor.execute(query, (user_id, month, year))
            data = cursor.fetchall()

            if data:
                st.write(f"### Spending Report for {year}-{month:02d}")
                column_names = ["Category", "Total Spent"]
                report_df = pd.DataFrame(data, columns=column_names)
                st.table(report_df)
            else:
                st.warning("No data found for the given period.")

#Analyzing spendature
def analyze_spending_trends(user_id):
    st.subheader("Analyze Spending Trends")
    with connect_to_db() as connection:
        cursor = connection.cursor()
        query = """
            SELECT MONTH(Date) AS Month, SUM(Amount) AS Total_Spent
            FROM Expense
            WHERE User_ID = %s
            GROUP BY MONTH(Date)
            ORDER BY Month
        """
        cursor.execute(query, (user_id,))
        trends = cursor.fetchall()

        if trends:
            df = pd.DataFrame(trends, columns=["Month", "Total Spent"])
            st.line_chart(df.set_index("Month"))
        else:
            st.warning("No spending data available.")

def set_budget(user_id):
    st.subheader("Set Budget")
    category_id = st.number_input("Category ID:", min_value=1, step=1)
    limit_amount = st.number_input("Enter Budget Limit:", min_value=0.0)

    #Fetching the expense table 
    with connect_to_db() as connection:
        cursor = connection.cursor()
        
        # Fetch and display current expenses for the user
        query_fetch = "SELECT Expense_ID, Description, Amount, Date FROM Expense WHERE User_ID = %s"
        cursor.execute(query_fetch, (user_id,))
        expenses = cursor.fetchall()
        
        if expenses:
            columns = ["Expense ID", "Description", "Amount", "Date"]
            df = pd.DataFrame(expenses, columns=columns)
            st.write("### Current Expenses")
            st.table(df)
        else:
            st.warning("No expenses found for this user.")
            return

    if st.button("Set Budget"):
        with connect_to_db() as connection:
            cursor = connection.cursor()

            # Insert budget into the Budget table
            query_budget = "INSERT INTO Budget (Limit_Amount, User_ID, Category_ID) VALUES (%s, %s, %s)"
            cursor.execute(query_budget, (limit_amount, user_id, category_id))
            connection.commit()
            st.success("Budget set successfully!")

            # Check total expenses for the category
            query_total_expenses = """
            SELECT SUM(Amount) 
            FROM Expense 
            WHERE User_ID = %s AND Category_ID = %s
            """
            cursor.execute(query_total_expenses, (user_id, category_id))
            total_expenses = cursor.fetchone()[0] or 0

            # If total expenses exceed the budget, log an alert
            if total_expenses > limit_amount:
                alert_message = f"Budget Exceeded for Category ID {category_id}"
                query_alert = """
                INSERT INTO alert (Alert_Message, Date, User_ID) 
                VALUES (%s, CURDATE(), %s)
                """
                cursor.execute(query_alert, (alert_message, user_id))
                connection.commit()
                st.warning(f"Alert: {alert_message}")
            else:
                st.success(f"Budget is within limit. Total expenses: ${total_expenses:.2f}")

            # Fetch and display alerts for the user
            query_fetch_alerts = "SELECT Alert_Message, Date FROM alert WHERE User_ID = %s"
            cursor.execute(query_fetch_alerts, (user_id,))
            alerts = cursor.fetchall()

            if alerts:
                st.write("### Alerts")
                alert_df = pd.DataFrame(alerts, columns=["Message", "Date"])
                st.table(alert_df)

            

def update_expense_transaction(user_id):
    st.subheader("Update Expense with Transaction")
    
    # Fetch and display current expenses
    with connect_to_db() as connection:
        cursor = connection.cursor()
        query_fetch = "SELECT Expense_ID, Description, Amount, Date FROM Expense WHERE User_ID = %s"
        cursor.execute(query_fetch, (user_id,))
        expenses = cursor.fetchall()

        if expenses:
            columns = ["Expense ID", "Description", "Amount", "Date"]
            df = pd.DataFrame(expenses, columns=columns)
            st.write("### Current Expenses")
            st.table(df)
        else:
            st.warning("No expenses found for this user.")
            return

    # Inputs for updating an expense
    expense_id = st.number_input("Expense ID to Update:", min_value=1, step=1)
    new_amount = st.number_input("New Amount:", min_value=0.01)

    # Performing transaction with rollback simulation
    if st.button("Update with Transaction"):
        with connect_to_db() as connection:
            try:
                cursor = connection.cursor()
                connection.start_transaction()

                # Update query
                query_update = "UPDATE Expense SET Amount = %s WHERE Expense_ID = %s AND User_ID = %s"
                cursor.execute(query_update, (new_amount, expense_id, user_id))

                # Simulate rollback
                connection.rollback()
                st.success("Transaction rolled back successfully!")

                # Display table again to confirm no changes
                cursor.execute(query_fetch, (user_id,))
                updated_expenses = cursor.fetchall()

                if updated_expenses:
                    updated_df = pd.DataFrame(updated_expenses, columns=columns)
                    st.write("### Updated Expenses (After Rollback)")
                    st.table(updated_df)
                else:
                    st.warning("No expenses remaining for this user.")
            except mysql.connector.Error as e:
                st.error(f"Transaction failed: {e}")




if __name__ == "__main__":
    main()
