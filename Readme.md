OMNI Practice Tracker

A Discord-based practice management and analytics application built with Python, SQLite, and the Google Sheets API.

OMNI Practice Tracker is a custom Discord application designed to help competitive esports players record practice sessions, monitor training activity, and review individual and team performance.

The application combines Discord slash commands, database management, automated time tracking, and Google Sheets synchronization into a single practice-management system.

Developer: Pitstopers
Project: OMNI
Status: Core application developed | AWS deployed

Key Features

Practice Management

* Log practice sessions with custom durations, categories, and notes.
* Edit or delete previously recorded sessions.
* Associate Discord users with practice sessions as practice partners.
* Review individual practice history and detailed session information.

Automated Stopwatch

* Start, stop, and check practice timers through Discord.
* Save elapsed practice time automatically.
* Receive automated reminders for extended practice sessions.
* Confirm or correct sessions lasting eight hours or longer.

Analytics & Reporting

* View individual practice statistics.
* Generate leaderboards based on total training time.
* Synchronize recorded practice data with Google Sheets.
* Retrieve session details through unique session IDs.

Data Integrity & Access Control

* SQLite database with relational tables.
* Foreign-key relationships and duplicate-record protection.
* Session ownership checks and role-based viewing permissions.
* Persistent stopwatch records and transaction-based session saving.

Technology Stack

Technology	Purpose
Python	Application logic
discord.py	Discord commands and interactions
SQLite	Persistent data storage
Google Sheets API	Practice data synchronization
asyncio	Asynchronous operations
Git & GitHub	Version control
AWS EC2	Cloud hosting (deployment in progress)
Ubuntu Linux	Cloud server operating system

Architecture

The application follows a simple backend architecture:

Discord User → Python Bot → SQLite Database → Google Sheets

Players interact with Discord slash commands. The Python application processes requests, validates information, and reads or updates the SQLite database.

Practice records are also synchronized with Google Sheets for additional reporting and analysis.

Available Commands

Command	Function
/practice	Log practice time
/stopwatch start	Start a practice timer
/stopwatch stop	Stop and save a timer
/stopwatch status	Check an active timer
/stats	View personal statistics
/history	View recent sessions
/leaderboard	View practice rankings
/session	View session details
/editpractice	Modify a session
/deletepractice	Delete a session
/addpartners	Associate practice partners
/addnotes	Add session notes
/commands	List available commands

Technical Challenges & Solutions

Preventing duplicate records

Implemented unique Discord interaction identifiers to help protect practice data from duplicate processing.

Managing database relationships

Designed separate practice-session and partner tables using SQLite foreign keys, composite uniqueness constraints, and cascading deletion.

Tracking long-running practice sessions

Built a stopwatch system that stores timestamps in SQLite and calculates elapsed time using UTC timestamps.

Integrating external services

Connected the application to Google Sheets and implemented asynchronous synchronization so blocking API operations do not run directly on the bot’s event loop.

Installation & Configuration

The application requires a compatible Python environment, the project dependencies, a Discord bot token, and Google Sheets API credentials.

Sensitive configuration, including the Discord token and service-account credentials, should remain outside version control.

The project initializes its SQLite tables when the bot starts.

Detailed deployment instructions will be added following cloud deployment.

Development Roadmap

* [x]	Core Discord slash commands
* [x]	SQLite session management
* [x]	Practice stopwatch and reminders
* [x]	Google Sheets synchronization
* [x]	Practice partners and session details
* [x]	Fresh database initialization
* [ ]	Complete AWS EC2 deployment
* [ ]	Configure automatic application startup
* [ ]	Implement cloud backup and recovery procedures
* [ ]	Add automated application tests

About This Project

This project was developed to address practical practice-management needs within OMNI while building hands-on experience in Python backend development, databases, API integrations, version control, and cloud infrastructure.

The project is maintained and developed by Pitstopers.