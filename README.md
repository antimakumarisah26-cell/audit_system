# AI Audit Management System

AI-powered audit management platform with anomaly detection, risk scoring, role-based access control, audit trails, and reporting.

## Features

* AI-based anomaly detection using Isolation Forest
* Real-time Streamlit dashboard
* Role-based authentication (Admin/User)
* Audit trail logging
* CSV data import
* Email alert support
* Risk scoring and compliance monitoring

## Tech Stack

* Python
* Streamlit
* SQLAlchemy
* Scikit-learn
* Pandas
* NumPy
* Loguru
* SQLite / PostgreSQL

## Live Demo

Streamlit App:
https://auditsystem-qdf3zk47faa4hxx4pryanz.streamlit.app/

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/antimakumarisah26-cell/audit_system.git
cd audit_system
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate:

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy:

```bash
copy .env.example .env
```

Update the values in `.env` if required.

### 5. Run the application

```bash
streamlit run main.py
```

The application will start at:

```text
http://localhost:8501
```

## Project Structure

```text
audit_system/
│
├── app/
│   ├── models/
│   ├── pages/
│   ├── services/
│   └── utils/
│
├── tests/
├── main.py
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

Run:

```bash
pytest tests -v
```

## Author

Antima Kumari

Computer Engineering Student
Nepal
