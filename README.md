# FilterProject

A fullstack web application for filtering and managing project opportunities using AI and keyword-based logic. The system supports user authentication, admin/user roles, and integrates a React frontend with a Django/MySQL backend.

---

## Features

- User authentication (JWT-based)
- Admin and user roles
- Filtered and rejected opportunities
- Keyword management (add, update, delete)
- Data visualization (basic)
- AI-powered and keyword-based filtering

---

## Tech Stack

- **Frontend:** React, Axios, CSS
- **Backend:** Django, Django REST Framework, MySQL, SQLAlchemy, Pandas, Scikit-learn, Sentence Transformers
- **Database:** MySQL

---

## Setup Instructions

### Backend

1. **Install dependencies:**
   ```bash
   cd Backend
   python -m venv .venv
   .\.venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```
2. **Configure MySQL database** in `Backend/filterproject/settings.py` (set DB name, user, password).
3. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
4. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```
5. **Run the backend server:**
   ```bash
   python manage.py runserver
   ```

### Frontend

1. **Install dependencies:**
   ```bash
   cd Frontend
   npm install
   ```
2. **Run the frontend:**
   ```bash
   npm start
   ```
   The app will be available at [http://localhost:3000](http://localhost:3000).

---

## Usage

- Log in as an admin to manage users and keywords.
- View filtered and rejected opportunities.
- Add or remove keywords to refine filtering.
- Use the re-filter button to reapply filters after updating keywords.

---

## Project Structure

```
FilterProject/
  Backend/      # Django backend (API, models, filtering logic)
  Frontend/     # React frontend (UI, pages)
  .venv/        # Python virtual environment (not tracked)
  data.json     # (optional) Data export/import file
```

---

## License

This project is licensed under the MIT License. 