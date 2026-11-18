# Personal Finance Tracker

A web-based Personal Finance Tracker built using **Python, Flask, and MySQL** to help users manage their personal finances, track income and expenses, organize transactions, and visualize their financial activities through interactive reports and charts.

The application provides a centralized platform for monitoring financial activities and understanding spending patterns.

---

## Project Overview

The Personal Finance Tracker is designed to simplify personal financial management. Users can register, log in, manage their financial transactions, organize expenses into categories, and view financial summaries through a dashboard.

The project combines backend development, database management, data analysis, and data visualization to provide a practical financial management solution.

##  Key Features

### 1. User Authentication
- User registration and login functionality.
- Secure password hashing.
- Session-based user authentication.
- User-specific financial data.

### 2. Dashboard
- Overview of total income.
- Overview of total expenses.
- Available balance calculation.
- Recent transaction history.
- Financial summary for quick monitoring.

### 3. Transaction Management
- Add income transactions.
- Add expense transactions.
- Store transaction descriptions and dates.
- Assign transactions to categories.
- Manage financial transaction records.

### 4. Category Management
- Organize transactions into categories.
- Separate income and expense categories.
- Manage categories for better financial organization.

### 5. Transaction History
- View recorded financial transactions.
- Track income and expenses.
- Review transaction details and dates.

### 6. Advanced Financial Reports & Data Visualization
- Generate financial reports.
- Analyze income and expense information.
- Visualize financial data using charts.
- Understand spending patterns and financial trends.

## Technologies Used

| Technology | Purpose |

| Python
| Flask
| MySQL  
| HTML5  
| CSS3   
| Bootstrap 
| Pandas 
| NumPy 
| Matplotlib 
| Seaborn 
| Git & GitHub 

## Database Structure

**Database Name:** `personal_finance_tracker`

The application uses MySQL to store user information and financial records.

### Database Tables

**1. Users**
- user_id
- full_name
- email
- password_hash
- created_at

**2. Categories**
- category_id
- user_id
- category_name
- category_type

**3. Transactions**
- transaction_id
- user_id
- category_id
- amount
- transaction_type
- description
- transaction_date
- created_at

**4. Budgets**
- budget_id
- user_id
- category_id
- monthly_limit
- budget_month

##  Project Structure

```text
Personal-Finance-Tracker/
│
├── app.py
├── database.py
├── test_db.py
├── requirements.txt
├── .env
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   ├── register.html
│   ├── transactions.html
│   ├── categories.html
│   └── reports.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │
│   ├── images/
│   │
│   └── charts/
│
└── README.md
```

*Note: This is a representative structure. Adjust the filenames to match your actual repository.*

##  Installation and Setup

Follow these steps to run the project locally.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Personal-Finance-Tracker.git
```

### 2. Navigate to the Project Directory

```bash
cd Personal-Finance-Tracker
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment.

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install Required Libraries

```bash
pip install -r requirements.txt
```

### 5. Configure MySQL Database

Open MySQL and create the database:

```sql
CREATE DATABASE personal_finance_tracker;
```

Configure your database credentials in the `.env` file:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=personal_finance_tracker
DB_PORT=3306
```

Replace the credentials with your local MySQL configuration.

### 6. Run the Application

```bash
python app.py
```

### 7. Open the Application

Visit the following URL in your browser:

```text
http://127.0.0.1:5000/
```

## Python Dependencies

The project uses the following Python libraries:

```text
Flask
mysql-connector-python
python-dotenv
pandas
numpy
matplotlib
seaborn
openpyxl
```

Install them using:

```bash
pip install -r requirements.txt
```

##  Data Analysis and Visualization

The project uses Python data analysis and visualization libraries to process financial records and generate reports.

- **Pandas:** Used for handling and analyzing financial datasets.
- **NumPy:** Used for numerical calculations and data operations.
- **Matplotlib:** Used to generate financial charts and graphs.
- **Seaborn:** Used to create statistical visualizations and improve chart presentation.

These libraries help transform financial transaction data into meaningful visual insights.

##  Security

- Passwords are stored using password hashing instead of plain text.
- User sessions are used for authentication.
- Financial records are associated with individual user accounts.
- Database credentials are configured through environment variables.

##  Project Objectives

- Develop a practical financial management web application.
- Implement Python backend development using Flask.
- Integrate a MySQL relational database.
- Perform financial data analysis using Pandas and NumPy.
- Generate meaningful reports using visualization libraries.
- Understand full-stack application development.

##  Future Enhancements

- Monthly budget tracking and notifications.
- Advanced financial analytics.
- Automated savings recommendations.
- Export financial reports to PDF and Excel.
- Improved financial forecasting.
- Enhanced dashboard with additional visualizations.

##  Author

**Harsh Shinde**

- GitHub: [HarshShinde4643](https://github.com/HarshShinde4643)
- Project: Personal Finance Tracker

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

**Developed using Python, Flask, MySQL, and Data Visualization Technologies.**
