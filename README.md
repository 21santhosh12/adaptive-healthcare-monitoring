# Adaptive Healthcare Monitoring System

A real-time healthcare monitoring system built with Flask and MongoDB Atlas, featuring live health metrics tracking, trend analysis, and smart alerts.

## Features

- Real-time health metrics monitoring
- Interactive health trends visualization
- Smart health alerts
- Secure authentication system
- Responsive dashboard interface

## Prerequisites

- Python 3.8 or higher
- MongoDB Atlas account
- Modern web browser

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd adaptive-healthcare-monitoring
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure MongoDB:
- The MongoDB connection string is already configured in `config/config.py`
- Make sure your IP address is whitelisted in MongoDB Atlas

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
adaptive-healthcare-monitoring/
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── templates/
│   ├── base.html
│   ├── index.html
│   └── dashboard.html
├── routes/
│   ├── auth.py
│   ├── patient.py
│   └── monitor.py
├── config/
│   └── config.py
├── app.py
├── requirements.txt
└── README.md
```

## Usage

1. Register a new account or log in with existing credentials
2. View real-time health metrics on the dashboard
3. Monitor health trends through interactive charts
4. Receive instant alerts for concerning health metrics

## Security

- Passwords are securely hashed using Werkzeug's security functions
- MongoDB Atlas provides enterprise-grade security
- Session-based authentication
- HTTPS recommended for production deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 