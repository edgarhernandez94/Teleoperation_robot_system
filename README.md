# Robot Teleoperation System

This project is a web-based system designed to manage and teleoperate robots in a laboratory environment. The system includes user authentication, role-based access control, session tracking, and the ability to make reservations or request trials for specific robots. The dashboard provides users with statistics on their robot usage, while administrators can manage user access and view trial requests.

---

## Features

### General Features
- **User Authentication**: Secure login system with roles (`admin` and `user`).
- **Role-based Access Control**: Only `admins` can manage users and approve trial requests.
- **Responsive Design**: Works seamlessly across desktop and mobile devices.
- **Session Tracking**: Logs the time users spend in specific sections.

### User-Specific Features
- **Dashboard**: Provides usage statistics and access to teleoperate robots.
- **Reservations**: Users can book time slots for robots.
- **Trial Requests**: Users without access to a robot can request a trial.

### Admin-Specific Features
- **User Management**: Enable or disable robot access for users, or delete users entirely.
- **Trial Management**: View and manage trial requests from users.

---

## System Architecture

### Backend
- **Framework**: Flask
- **Database**: MongoDB
  - `users`: Stores user data and permissions.
  - `reservations`: Stores booking information.
  - `trial_requests`: Records user requests for robot trials.
  - `user_activity`: Logs user session times for specific sections.

### Frontend
- **HTML & CSS**: Bootstrap for styling, with additional custom styles.
- **JavaScript**: Used for dynamic content updates and AJAX requests.
- **Templates**: Jinja2 templates render server-side dynamic content.

### Data Flow
1. **User Login**: Role and permissions are loaded and stored in the session.
2. **Dashboard**:
   - Displays available robots and usage statistics.
   - Users can access robots they are authorized for.
3. **Reservations**:
   - Users can book time slots for robots.
   - Prevents overlapping reservations.
4. **Trial Requests**:
   - Users can request access to robots they cannot currently access.
   - Requests are stored in the database for admin review.
5. **Admin Panel**:
   - Allows admins to manage user access and trial requests.

---

## Installation

### Prerequisites
1. **Python 3.7+**
2. **MongoDB**
3. **Flask** and required Python libraries:
   ```bash
   pip install flask flask-login pymongo
   ```

### Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Flask app:
   ```bash
   flask run --host=0.0.0.0 --port=8065
   ```

---

## File Structure

```
project/
├── app.py              # Main Flask application
├── templates/          # HTML templates
│   ├── layout.html     # Base layout
│   ├── dashboard.html  # User dashboard
│   ├── manage_users.html  # Admin user management
├── static/             # Static files (CSS, JS, Images)
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

---

## Usage

### User Roles
- **Admin**:
  - Manage user access to robots.
  - Approve or deny trial requests.
- **User**:
  - View dashboard.
  - Make reservations for robots they have access to.
  - Request trials for robots they cannot access.

### Key Endpoints
- **Dashboard**: `/dashboard`
- **Reservations**: `/reservations`
- **Manage Users** (Admin Only): `/manage_users`
- **Request Trial**: `/request_trial?robot=<robot_name>`

---

## Development

### Debugging
To run the app in debug mode:
```bash
flask run --debug
```

### Extending Functionality
- **Add New Robots**:
  - Update the `dashboard.html` and `manage_users.html` templates.
  - Ensure permissions are handled in `app.py`.

---

## Future Enhancements
- **Notifications**: Notify admins of pending trial requests.
- **Advanced Analytics**: Include more detailed graphs and reports.
- **Email Integration**: Send confirmations for reservations and trials.
- **Improved Security**: Add rate limiting and input validation.

---

## License
This project is licensed under the MIT License.
