# Festival Poll Application

Project Group: UGent – Business Informatics  
Deadline: 19 December 2025

---

## Render
Live application (Render):  https://l.messenger.com/l.php?u=https%3A%2F%2Fweb-application-2025-group-38.onrender.com%2F&h=AT3e3ZhH20CHVgDHSRl6ZXiUHUyVKqxE-xh6gpcsl8dSrvFK4cTMyrTlYEpqNI93Ym9ZIHyCds-yjkmei5qvQyz8TEORjR_-BuaKwDdEnIyP9AHAU5u3SL352fu4UMSYxUmh1CVZUj1TK8mENA1EcA

---

## Project Description
The Festival Poll Application is a web-based platform developed as part of the courses **Algorithms & Data Structures** and **Database Systems** at Ghent University.

The application allows festival visitors to suggest artists and genres and participate in personalized polls. Administrators can manage festival editions and analyze voting results and genre trends.

The project focuses on database design, data-driven decision making, and algorithmic recommendation logic.

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
- Backend: Flask (Python)  
- Database: PostgreSQL (Supabase)  
- ORM: SQLAlchemy  
- Database migrations: Flask-Migrate  
- Recommendation logic based on genre proximity graphs (Dijkstra algorithm)

---

## Installation Notes
For detailed dependency information, see the `requirements.txt` file included in the repository.

The application requires a PostgreSQL database (Supabase).

Before running the application, the following environment variables must be configured:
- `SECRET_KEY`
- `DATABASE_URL`

Database migrations must be executed before first use.

To start the application locally:
1. Activate the virtual environment  
2. Run the Flask application  

---

## UI Prototype
This UI prototype was created at the beginning of the project, when the application concept was still simple and before further feature expansions.

UI prototype link:  
https://www.figma.com/proto/W7ggxBZR0r6XMTM07VXhoY/Festival-Poll-UI?node-id=153-3&p=f&t=7Sc9zphd5GY6wjPU-1&scaling=min-zoom&content-scaling=fixed&page-id=1%3A1378

---

## Feedback Sessions
Feedback session 1:  
https://1drv.ms/v/c/2b685717d1176f31/IQBxG_31p_lXRJI21kKQ5mh0AdafbbOHWf3jbJU5dePd2AQ?e=I6AKKw  

Feedback session 2:  
https://1drv.ms/v/c/2b685717d1176f31/IQBTjrz4G0LHSLUa1lLf--H5AdL4y4DajR6tRvXbqFrV4l0?e=74jDEu  

---

## Demo
https://1drv.ms/v/c/2b685717d1176f31/IQBXTGSAPZziSo6jY0ZeQqT5ARf0T71pGdcN3ttObiWkPfU?e=5kPvPL


