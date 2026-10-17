# FitStart Gym website

The registration form is saved through a Python backend into a local MySQL database. The workout reminders remain in the visitor's browser.

## Local setup on Windows

1. Install **MySQL Server 8.4** from the official MySQL source. In PowerShell opened as Administrator, initialize and start the local-only MySQL service:

   ```powershell
   .\setup_mysql.ps1
   ```

   The script binds MySQL to this PC only and refuses to overwrite an existing database folder or service.
2. Open PowerShell in this folder and install the Python packages:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

3. Initialize the database and create restricted credentials. The script uses a blank password for a fresh local install (or securely prompts for an existing root password), generates random root and app passwords, and saves them in the git-ignored `.env` file:

   ```powershell
   .\.venv\Scripts\python.exe setup_database.py
   ```

4. Start the website and open **http://127.0.0.1:5000**:

   ```powershell
   python app.py
   ```

The MySQL application account is limited to reading the registration count and inserting registrations. Do not publish `.env` or expose the local development server directly to the internet. A public deployment needs a hosted MySQL database, HTTPS, and production-grade hosting/configuration.
