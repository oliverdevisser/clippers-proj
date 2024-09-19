# LAC_FSD_ODV Web Application

This project is a web application built with Flask and uses PostgreSQL as its database. The entire application is containerized using Docker to make the setup and deployment straightforward and easy. This guide will walk you through setting up and running the application on your local machine within a Docker container.

---

## Table of Contents

- [Questions 1-4](#questions-1-4)
- [Question 5: Web Application](#question-5-web-application)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Stopping the Application](#stopping-the-application)
- [Troubleshooting](#troubleshooting)
- [Additional Notes](#additional-notes)
- [Login Credentials](#login-credentials)
- [Conclusion](#conclusion)

---

## Questions 1-4

- **Question 1:** Written in `/scripts/transfer_json_to_db.py`
- **Question 2:** Written in `/sql_scripts/03_basic_queries.sql`
- **Question 3:** Written in `/sql_scripts/04_schedule_queries.sql`
- **Question 4:** Written in `/sql_scripts/05_lineups_queries.sql`

To see the outputs for these questions:
1. Load the app as below
2. Go to PostgreSQL db in Docker (lac_fsd_odv-db-1)
3. Go to Exec, run `psql -U postgres -d lac_fullstack_dev` to connect to db
4. Can check answers as below, use `\dt` to see all tables
question 2: `SELECT * FROM basic_queries;`
question 3: did not save tables, copy from `/sql_scripts/04_schedule_queries.sql` and run to see tables
question 4: a - `SELECT * FROM wide_table;` b - `SELECT * FROM stints_results;` c - `SELECT * FROM stints_results_averages;` d - `SELECT * FROM final_summary;`

---

## Question 5: Web Application

The web application addresses Question 5, providing visualizations and user interactions as specified.

---

## Prerequisites

Before you begin, make sure you have the following installed on your machine:

- **Docker:** You can install Docker from the [official Docker website](https://www.docker.com/get-started).
- **Docker Compose:** Docker Compose is typically bundled with Docker Desktop. Verify its installation by running:

  ```bash
  docker-compose --version


## Project Structure

Here is an overview of the files and directories in this project:

 ```
  LAC_FSD_ODV/
  ├── __pycache__/          # Python bytecode cache (ignored in Docker)
  ├── clean_env/            # Clean virtual environment (optional, not used directly in Docker)
  ├── dev_test_data/        # Sample JSON data to seed the database
  │   ├── game_schedule.json
  │   ├── lineup.json
  │   ├── player.json
  │   ├── roster.json
  │   ├── team_affiliate.json
  │   └── team.json
  ├── scripts/              # Python scripts
  │   └── transfer_json_to_db.py     # Script to transfer JSON data to the database
  ├── sql_scripts/          # SQL scripts to initialize and query the database
  │   ├── 01_create_tables.sql
  │   ├── 03_basic_queries.sql
  │   ├── 04_schedule_queries.sql
  │   └── 05_lineups_queries.sql
  ├── static/               # Static assets such as CSS
  │   └── style.css
  ├── templates/            # HTML templates for the web app
  │   ├── index.html
  │   └── login.html
  ├── .dockerignore         # Files and directories to ignore in Docker builds
  ├── .gitignore            # Files to ignore in git commits
  ├── app.py                # The Flask application
  ├── config.py             # Configuration settings (read NOTE in this file for information about keys)
  ├── docker-compose.yml    # Docker Compose file for managing services
  ├── Dockerfile            # Dockerfile to build the Flask web app image
  ├── README.md             # Project documentation (this file)
  └── requirements.txt      # Python dependencies for the Flask app
```

## Installation
Follow these steps to get the project up and running:

### 1. Clone the Repository
   First, you need to unzip or clone the project directory to your local machine. If it's in a ZIP file, extract it:
```
unzip LAC_FSD_ODV.zip
cd LAC_FSD_ODV
```

### 2. Build the Docker Images
   The project contains a Dockerfile and a docker-compose.yml file. These will help you to set up the Flask app and PostgreSQL database in separate containers.

Build the images:
```
docker-compose build
```
This command reads the Dockerfile and docker-compose.yml file to build the necessary Docker images for the Flask web app and PostgreSQL database.

## Running the Application
Once the images are built, you can run the web application and the PostgreSQL database together in containers.

### 1. Start the Docker Containers
   To start the containers, run:
   
```
docker-compose up
```

This will start two containers:
```
web: The Flask web application container.
db: The PostgreSQL database container.
```
If everything is set up correctly, the web app will be available on http://localhost:5001 (if not try http://localhost:5000).

### 2. Open the Web Application
   Open your web browser and go to:
```
http://localhost:5001
```

You should see the login page for the web application.

## Stopping the Application
To stop the running Docker containers, press Ctrl+C in the terminal where docker-compose up is running.

After, you can stop the containers gracefully by running:
```
docker-compose down
```

This will stop and remove the containers but keep the database volume intact.

## Troubleshooting
Here are some common issues you might encounter and how to resolve them:

### Database connection errors: 
Ensure that the PostgreSQL database is running properly. You can check the logs with:
```
docker-compose logs db
```
### Port conflicts: 
If you have other applications running on port 5000 (for the web app) or 5432 (for PostgreSQL), you may need to change the ports in the docker-compose.yml file.

## Additional Notes
Persistence: The PostgreSQL database stores data in a Docker volume (db_data), so even if you stop the containers, the data will persist. If you want to completely remove the database data, you can run:

```
docker-compose down -v
```

## Accessing the Database: 
You can access the PostgreSQL database using the following credentials (defined in docker-compose.yml):

```
Host: db
Port: 5432
Database: lac_fullstack_dev
Username: postgres
Password: postgres
```

## Login Credentials
The application includes two user accounts for demonstration purposes:

User 1 (Performance Scout):
Username: user_one
Password: password123
User 2 (Assistant Coach):
Username: user_two
Password: 123password

## Security Note:
In a typical production environment, sensitive information such as `SECRET_KEY` and `DATABASE_URL`
wouldn't have some default values like 'your_secret_key', but for this quick example project,
I just used `SECRET_KEY` for ease of setup and testing purposes. In a real-world scenario or with more time, I would remove any default value and use secure, randomly generated key, and securely share sensitive credentials across environments.
"""

## Conclusion
You now have the LAC_FSD_ODV web app running in Docker containers with a PostgreSQL database. Follow the steps outlined above to build, run, and troubleshoot the application.

If you encounter any issues or have questions, feel free to check the logs (docker-compose logs) or reach out for further assistance (olliedevisser@gmail.com ).
