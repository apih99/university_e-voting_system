# University Voting System

A comprehensive online platform for managing university student council elections with robust security and user-friendly features.

## Features

- Multi-role user system (Voter, Candidate, Administrator)
- Faculty and General candidate categories
- Secure voting with strict rules
- Real-time election results
- Responsive design with Bootstrap 5
- Profile management with photo upload
- Two-factor authentication support

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd voting-system
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. Apply database migrations:
```bash
cd voting_system
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

1. Access the admin interface at `/admin` to:
   - Create faculties
   - Manage users
   - Set up elections
   - Approve candidates

2. Regular users can:
   - Register as voters
   - Update their profiles
   - View active elections
   - Cast votes
   - View results

3. Candidates can:
   - Register for elections
   - Submit personal statements
   - Upload profile photos

## Security Features

- Role-based access control
- Two-factor authentication
- Secure password handling
- Prevention of duplicate voting
- Student ID validation

## Voting Rules

- Voters can select up to 3 faculty candidates
- Voters can select up to 7 general candidates
- Votes cannot be changed after submission
- Results are published after election end date

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
