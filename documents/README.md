# Festival Poll Application

**Project Group:** UGent – Business Informatics  
**Deadline:** 19 December 2025

---

## Live Application (Render)
https://web-application-2025-group-38.onrender.com/

---

## Project Description
The Festival Poll Application is a web-based platform developed as part of the courses  
**Algorithms & Data Structures** and **Database Systems** at Ghent University.

The application allows festival visitors to suggest artists and genres and participate in
personalized polls. Administrators can manage festival editions and analyze voting results
and genre trends.

The project focuses on database design, data-driven decision making, and algorithmic
recommendation logic.

---

## Features
- User registration and authentication
- Artist and genre suggestions by users
- Personalized polls based on user preferences
- Genre-based scoring using proximity graphs
- Administrative dashboard for managing festivals, artists, and results
- Persistent data storage using PostgreSQL (Supabase)

---

## Technical Stack
- **Backend:** Flask (Python)
- **Database:** PostgreSQL (Supabase)
- **ORM:** SQLAlchemy
- **Database migrations:** Flask-Migrate
- **Recommendation logic:** Genre proximity graphs (Dijkstra algorithm)

---

## Installation Notes
The application requires a PostgreSQL database (Supabase or local).

Before running the application, the following environment variables must be configured:
- `SECRET_KEY`
- `DATABASE_URL`

For detailed dependency information, see the `requirements.txt` file included in the repository.

---

## How to run the app (development)

Follow these steps to run the Flask application locally in development mode.

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

2. **Install dependencies**
 ```bash
 pip install --upgrade pip
 pip install -r requirements.txt
  ```


Configure environment variables
Create a .env file in the project root and set the following variables:
```env
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_APP=app
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@host:port/database
```


Apply database migrations
```bash
flask db upgrade
```


Run the application
```bash
python -m flask run
```


The application will be available at:
http://127.0.0.1:5000

## UI Prototype

https://www.figma.com/proto/W7ggxBZR0r6XMTM07VXhoY/Festival-Poll-UI

## Feedback Sessions

Feedback session 1

https://1drv.ms/v/c/2b685717d1176f31/IQBxG_31p_lXRJI21kKQ5mh0AdafbbOHWf3jbJU5dePd2AQ

Feedback session 2

https://1drv.ms/v/c/2b685717d1176f31/IQBTjrz4G0LHSLUa1lLf--H5AdL4y4DajR6tRvXbqFrV4l0

## Demo

https://1drv.ms/v/c/2b685717d1176f31/IQBXTGSAPZziSo6jY0ZeQqT5ARf0T71pGdcN3ttObiWkPfU


---




