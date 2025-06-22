# Savings Optimization Backend

This backend is a Python-based application that uses Flask and Pyomo to provide an API for optimizing savings investments. It takes a user's earnings and a list of savings goals, and determines the best allocation across various types of savings accounts to maximize interest returns, while respecting account-specific and regulatory constraints (like ISA limits).

## Features

- **Flask API**: A simple and robust API built with Flask.
- **Pyomo Optimization**: Utilizes Pyomo to model and solve the savings allocation problem.
- **Modular Structure**: The code is organized into services for data fetching and optimization, making it easy to extend.
- **Mock Data**: Includes a mock data service for savings accounts, allowing the application to run without external API dependencies.
- **Configuration Management**: Uses a `config.py` file and `.env` for easy configuration.

## Project Structure

Here is an overview of the key files and directories:

```
backend/
├── app/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── account_data_service.py  # Fetches savings account data (currently mocked).
│   │   └── optimization_service.py  # Contains the Pyomo optimization logic.
│   ├── __init__.py                # Flask application factory.
│   ├── models.py                  # Defines data classes for the application.
│   └── routes.py                  # Defines API endpoints.
├── venv/                          # Python virtual environment.
├── .gitignore
├── config.py                      # Application configuration.
├── requirements.txt               # Python dependencies.
└── run.py                         # Entry point to run the Flask application.
```

## Setup and Installation

Follow these steps to set up the project locally.

### 1. Prerequisites

- Python 3.x
- `pip` and `venv`
- Homebrew (for macOS users to install the solver)

### 2. Install the Optimization Solver

This project uses the `glpk` solver. You need to install it on your system.

**On macOS (using Homebrew):**
```bash
brew install glpk
```

**On Debian/Ubuntu:**
```bash
sudo apt-get install glpk-utils
```

### 3. Set Up the Virtual Environment and Install Dependencies

From the project root (`Quantify Lite`), run the following commands:

```bash
# Create and activate a virtual environment
python3 -m venv backend/venv
source backend/venv/bin/activate

# Install the required Python packages
pip install -r backend/requirements.txt
```

## Running the Application

To start the development server, run the following command from the project root:

```bash
cd backend
source venv/bin/activate
python run.py
```

The application will start on `http://127.0.0.1:5001`.

## API Endpoints

The application exposes the following endpoints:

### Health Check

- **Endpoint**: `/health`
- **Method**: `GET`
- **Description**: A simple endpoint to check if the service is running.
- **Example `curl` command**:
  ```bash
  curl http://127.0.0.1:5001/health
  ```
- **Success Response**:
  ```json
  {
    "status": "healthy"
  }
  ```

### Optimize Savings

- **Endpoint**: `/optimize`
- **Method**: `POST`
- **Description**: Triggers the savings optimization.
- **Request Body**: A JSON object containing the user's annual earnings and a list of their savings goals.
  ```json
  {
    "earnings": 50000,
    "savings_goals": [
      {
        "amount": 10000,
        "horizon": "1 year"
      },
      {
        "amount": 15000,
        "horizon": "Easy access"
      }
    ]
  }
  ```
- **Example `curl` command**:
  ```bash
  curl -X POST -H "Content-Type: application/json" \
  -d '{"earnings": 50000, "savings_goals": [{"amount": 10000, "horizon": "1 year"}]}' \
  http://127.0.0.1:5001/optimize
  ```
- **Success Response**: A JSON object containing the list of investments and the overall status.
  ```json
  {
    "investments": [
      {
        "account_name": "Fixed Rate ISA 2 Year",
        "amount": 20000.0,
        "aer": 7.0,
        "term": "2 Years",
        "is_isa": true,
        "url": "https://www.google.com/search?q=Fixed+Rate+ISA+2+Year"
      },
      {
        "account_name": "Fixed Rate Bond 1 Year",
        "amount": 30000.0,
        "aer": 6.5,
        "term": "1 Year",
        "is_isa": false,
        "url": "https://www.google.com/search?q=Fixed+Rate+Bond+1+Year"
      }
    ],
    "status": "Optimal",
    "total_return": 3350.0
  }
  ```

## How It Works

### 1. API Request
The user sends a `POST` request to the `/optimize` endpoint with their annual earnings and a list of savings goals (amount and horizon).

### 2. Data Processing
The backend currently sums the amounts from all savings goals to determine a single `total_investment` figure. The `earnings` figure is used by the frontend to calculate post-tax returns but is not yet used in the backend optimization logic itself.

### 3. Data Fetching
The `account_data_service` is called to retrieve a list of available savings accounts. Currently, this service returns hardcoded mock data. In a production environment, this would be replaced with calls to a real financial data API.

### 4. Optimization
The `optimization_service` creates a Pyomo `ConcreteModel` with:
- **Variables**: The amount to invest in each account.
- **Objective Function**: Maximize the total interest earned from all investments.
- **Constraints**:
    - The sum of all investments must equal the total calculated from the user's savings goals.
    - Each investment must be within the account's minimum and maximum investment limits.
    - The total investment in ISA accounts cannot exceed the annual limit (e.g., £20,000).

The model is then solved using the `glpk` solver.

### 4. Response
The optimization results, including a detailed list of recommended investments and the total expected return, are formatted into a JSON object and returned to the user.

## Version Control

This project is managed using Git and is hosted on GitHub.

### Cloning the Repository
To get a local copy of the project, clone the repository using the following command:
```bash
git clone https://github.com/samphillips38/quantify-lite-backend.git
cd quantify-lite-backend
```

### Contribution Workflow
If you wish to contribute, please follow this basic workflow:
1.  Create a new branch for your feature or bug fix: `git checkout -b feature/your-feature-name`
2.  Make your changes and commit them with a clear message: `git commit -m "Add some feature"`
3.  Push your branch to the repository: `git push origin feature/your-feature-name`
4.  Open a pull request on GitHub. 

## Deployment on Railway

This application is configured for deployment on [Railway](https://railway.app/).

To deploy this application, you can fork this repository and connect it to a new Railway project. The deployment will be handled automatically by Railway's Nixpacks build process.

The following files are used for the deployment configuration:

- `nixpacks.toml`: This file configures the build environment on Railway and ensures that the `glpk` solver is installed.
- `Procfile`: This file specifies the command to run the application on the server using `gunicorn`.

When you create a service on Railway and point it to this repository, Railway will automatically:
1. Detect the Python application.
2. Install the system packages specified in `nixpacks.toml` (i.e., `glpk`).
3. Install the Python dependencies from `requirements.txt`.
4. Run the application using the command from the `Procfile`. 