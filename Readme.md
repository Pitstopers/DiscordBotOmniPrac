🌌 OMNI Practice Tracker

A cloud-hosted Discord application for competitive sports practice tracking, session management, and performance reporting.

Built with Python, discord.py, SQLite, Google Sheets API, and Amazon Web Services (AWS).

Developer: Pitstopers
Status: Deployed on AWS EC2

Overview

OMNI Practice Tracker is a Discord application developed to help competitive esports players organize, record, and analyze their practice activity.

The application supports manual practice logging, automated stopwatches, session management, individual statistics, and team leaderboards.

It uses SQLite for persistent storage and integrates with Google Sheets for reporting.

The application is deployed on AWS EC2 and uses Linux services, automated database backups, and cloud infrastructure monitoring.

Core Features

Practice Tracking

* Record practice duration, categories, and notes.
* Edit and delete previously recorded sessions.
* Associate practice partners with individual sessions.
* Retrieve practice history and detailed session records.
* Validate practice durations and prevent duplicate interaction submissions.

Automated Stopwatch

* Start and stop practice timers using Discord slash commands.
* Track active timers using persistent SQLite records.
* Receive reminders for extended practice sessions.
* Confirm or correct recorded durations for sessions lasting eight hours or longer.

Statistics and Reporting

* View individual training statistics.
* Rank players by total practice duration.
* Synchronize practice records with Google Sheets.
* Generate spreadsheet-based player summaries.

Security and Data Integrity

* Session ownership checks and role-based access.
* SQLite unique constraints and foreign-key relationships.
* Transaction-based database operations.
* Environment-based credential configuration.

Technology Stack

Technology	Purpose
Python	Backend application development
discord.py	Discord API integration
SQLite	Relational database
Google Sheets API / gspread	Data synchronization and reporting
AWS EC2	Cloud compute
Ubuntu Linux	Server operating system
systemd	Application and scheduled task management
Amazon S3	Off-instance database backups
AWS IAM	Role-based permissions
Amazon CloudWatch	EC2 health monitoring
Amazon SNS	Email notification delivery
Bash	Backup automation
Git / GitHub	Version control and deployment

System Architecture

flowchart TD
    A[Discord Users] --> B[Discord API]
    B <--> C[Python Bot on AWS EC2]
    C <--> D[(SQLite Database)]
    D --> E[Google Sheets Synchronization]
    E --> F[Google Sheets Reports]
    D --> G[SQLite Backup Script]
    H[systemd Daily Timer] --> G
    G --> I[(Amazon S3 Backups)]
    J[AWS IAM Role] -.-> I
    K[CloudWatch EC2 Health Alarm] --> L[Amazon SNS]
    L --> M[Email Notifications]

SQLite is the application’s primary data store. Google Sheets is used for reporting, while S3 stores independent recovery copies.

Discord Commands

Command	Description
/practice	Record a practice session
/stopwatch start	Begin a stopwatch
/stopwatch stop	Stop and save practice time
/stopwatch status	View an active stopwatch
/stats	View individual practice statistics
/history	View recent practice sessions
/leaderboard	Display practice rankings
/session	Retrieve session details
/editpractice	Update an existing practice session
/deletepractice	Delete an owned session
/addpartners	Associate partners with a session
/addnotes	Save additional session notes
/commands	View available commands

Cloud Deployment

AWS EC2

The application runs on an Ubuntu Linux EC2 instance with a dedicated Python virtual environment.

Application updates are retrieved from GitHub using SSH authentication and a read-only repository deploy key.

Application Management

The bot operates as a systemd service configured to:

* Start automatically when Ubuntu boots.
* Restart after application process failures.
* Run independently of an active SSH connection.
* Provide logs through journalctl.

Database Backups

The backup process uses a Bash script to:

1. Create a timestamped SQLite snapshot.
2. Verify database integrity.
3. Upload the validated backup to Amazon S3.
4. Remove local backups older than seven days following a successful upload.

A systemd timer is configured to run the backup process daily.

A database recovery test was completed using a backup downloaded from S3.

Cloud Security

The AWS deployment implements:

* SSH key-based server authentication.
* Restricted SSH inbound access through an EC2 security group.
* Private S3 storage.
* IAM role-based S3 access with limited permissions.
* File permissions protecting application credentials.
* AWS CloudWatch alarms for EC2 health monitoring.
* Amazon SNS integration for notifications.
* AWS billing monitoring.

Monitoring scope: The CloudWatch alarm monitors EC2 health. Application-level Google Sheets synchronization monitoring is a possible future enhancement.

Development Setup

Requirements

* Compatible Python 3 version
* Discord application and bot token
* Google Sheets API service-account credentials
* Python packages listed in requirements.txt

Install Dependencies

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

Environment Configuration

Create a .env file containing:

DISCORD_TOKEN=your_discord_token
GOOGLE_SHEETS_ID=your_spreadsheet_id

Place the authorized Google service-account JSON file at the location expected by sheets_sync.py.

Never commit production credentials or private player databases to version control.

Run the Application

python bot.py

The application initializes missing SQLite tables during startup.

Maintenance

Check Application Status

sudo systemctl status omni-practice

View Application Logs

sudo journalctl -u omni-practice -n 50 --no-pager

Check Backup Schedule

systemctl list-timers --all

Update Application Code

Production changes are developed locally, committed to GitHub, pulled onto EC2, and applied through the application service.

Technical Challenges

Dependency compatibility: Resolved differences between local and Ubuntu Python environments.

Database integrity: Implemented unique interaction identifiers, relational constraints, and transactional operations.

Persistent time tracking: Used SQLite and UTC timestamps to preserve active stopwatch sessions.

Cloud reliability: Configured automatic application startup, failure restarts, database backup scheduling, and off-instance recovery.

Credential management: Separated sensitive configuration from source code and used an IAM role instead of permanent AWS access keys for S3 access.

Future Improvements

* [ ]	Automated application-level integration tests
* [ ]	Google Sheets synchronization failure alerts
* [ ]	GitHub Actions deployment workflow
* [ ]	Additional observability and monitoring
* [ ]	Expanded practice analytics

Project Purpose

OMNI Practice Tracker combines esports team operations with practical software development and cloud infrastructure management.

The project demonstrates hands-on experience in Python backend development, relational databases, external API integration, Linux administration, AWS deployment, application security, and disaster recovery.

Developed by Pitstopers.