### 🧠 AskIT – AI-Powered Natural Language Database Backend

**AskIT** is an innovative backend API service that empowers users to query their databases and generate insights using natural language. It acts as an intelligent bridge between your users and your data, utilizing advanced LLMs to translate everyday questions into optimized SQL queries, execute them securely, and return actionable, easy-to-understand insights.

---

#### ⚙️ What This Repo Is

This is the backend core for a conversational data analytics platform. It handles:

* 🤖 **Natural Language to SQL (NL2SQL)**: Leverages LLMs to accurately convert user questions into complex database queries.
* 📊 **Automated Insight Generation**: Processes raw database results into meaningful summaries, data points, and natural language responses.
* 🔌 **Database Connection Management**: Securely connects to and manages schemas for various SQL databases (e.g., PostgreSQL, MySQL, SQLite).
* 🛡️ **Query Security & Sanitization**: Implements strict read-only execution environments and query validation to protect your data integrity.
* 🔗 **API-First Design**: Provides a clean RESTful interface, making it easy to plug this AI capability into any frontend dashboard, chat UI, or existing application.

---

#### 🚀 Features

* 💬 **Conversational Analytics**: Allow end-users to "chat" with their data without writing a single line of SQL.
* 🧠 **LLM Integration**: Built-in orchestration for leading language models (like OpenAI, Anthropic, etc.) optimized for schema understanding.
* 🔒 **Safe Execution Guardrails**: Built-in query sanitization ensures that generated queries are safe, performant, and restricted from destructive actions (no DROP or DELETE).
* 📈 **Dynamic Context Injection**: Automatically feeds the LLM relevant database schema context (tables, columns, relationships) to improve query accuracy.
* ⚡ **High Performance**: Optimized for fast schema parsing, minimal latency during LLM handshakes, and quick response times.
* ⚙️ **Extensible Architecture**: Clean separation of API routes, LLM prompt engineering, and database execution logic.

---

#### 📦 Setup & Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-org/askit-backend.git
    cd askit-backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your environment:**
    - Copy `.env.example` to `.env`.
    - Fill in your `DATABASE_URL`, secrets.
    ```bash
    cp .env.example .env
    # (Edit .env with your values)
    ```

5.  **Initialize and migrate the database:**
    ```bash
    flask db init  # Run only once to initialize migrations
    flask db migrate -m "Initial migration"
    flask db upgrade
    ```

6.  **Seed the database with initial data (IMPORTANT):**
    - This command creates the default organization, admin user, roles, and permissions.
    ```bash
    flask seed
    ```

7.  **Run the development server:**
    ```bash
    flask run
    ```
    The server will be running at `http://127.0.0.1:5000`.

---

#### 📁 Repo Structure
```
askit-backend/
├── src/
│ ├── main.py # Flask App Factory
│ ├── extensions.py # Centralized Flask extensions
│ ├── controllers/ # Request handling logic
│ ├── models/ # SQLAlchemy DB models
│ ├── services/ # Business logic
│ ├── routes/ # Blueprint and URL definitions
│ ├── middleware/ # Custom request middleware
│ └── utils/ # Security, decorators, etc.
├── tests/
├── config.py
├── requirements.txt
└── README.md
```
