# INTSTALLATION REQUIREMENTS

# pip intall flask
# pip install psycopg2
# pip install flask flask_sqlalchemy flask_login flask_bcrypt 
# flask_wtf wtforms email_validator



# REQUIRED LIBRARIES

from flask import Flask, render_template, redirect, url_for, request, session
import psycopg2
from datetime import date, timedelta, datetime, time
from flask_login import UserMixin
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from decimal import Decimal
import json
import ast



# APP INITALISATION

# Define app to run staff schedule website
app = Flask(__name__)
# Secret key required for password use
app.config['SECRET_KEY'] = 'thisisasecretkey'



# DATABASE CONNECTION

# Set up connection to database
DB_HOST = ''
DB_NAME = 'Nopalito_DB_1'
DB_USER = 'postgres'
# PUT PASSWORD IN
DB_PASSWORD = ''

# Establish connection to PostgreSQL database
connection = psycopg2.connect(
    host=DB_HOST,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)



# FUNCTIONS

# Function to get staff data
def get_staff_data():
    cursor = connection.cursor()
    cursor.execute('SELECT staff_id, first_name, surname, '
                    'upper(first_name || \' \' || surname) AS NAME, '
                    'job_title, start_date, end_date, wage '
                    'FROM "nopalito_schema"."staff" '
                    'WHERE end_date IS NULL AND uname != \'admin\'')
    staff_data = cursor.fetchall()
    cursor.close()
    return staff_data


# Function to get shifts data
def get_shifts_data():
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM "nopalito_schema"."shifts"')
    shifts_data = cursor.fetchall()
    cursor.close()
    return shifts_data


# Function to get time off data
def get_time_off_data():
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM "nopalito_schema"."time_off" '
                    'WHERE approved = True')
    time_off_data = cursor.fetchall()
    cursor.close()
    return time_off_data


# Function to get monday of week for a given date
def get_mon(d):
    days_sub = d.weekday()
    mon_of_week = d - timedelta(days=days_sub)

    return mon_of_week


# Function to get dates of week from a given monday
def week_values(mon_date):
    week = []
    for i in range(7):
        week.append(str(mon_date + timedelta(days=i)))

    return week


def custom_serializer(obj):
    if isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError('Object of type %s is not JSON serializable' % type(obj))


def add_timedelta(date, days):
    return date + timedelta(days=days)


def str_to_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d').date()

# Create a dictionary with the filter functions and their respective names
custom_filters = {
    'add_timedelta': add_timedelta,
    'str_to_date': str_to_date
}

# Pass the custom_filters dictionary to app.jinja_env.filters
app.jinja_env.filters.update(custom_filters)



# PAGE CREATIONS

# Define route to landing/home page
@app.route('/')
def homepage():
    return render_template('homepage.html')


# Define route to login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        password = request.form['password']

        # Check if the provided username and password exist in the database
        cursor = connection.cursor()

        query = "SELECT staff_id, first_name, surname " \
                "FROM \"nopalito_schema\".\"staff\" " \
                "WHERE uname = %s AND password = %s;"
        cursor.execute(query, (uname, password))
        user = cursor.fetchone()

        cursor.close()

        # If existing login details check whether admin or staff
        if user:
            session['user_id'] = user[0]
            session['first_name'] = user[1]
            session['surname'] = user[2]

            # If admin login redirect to admin page
            if uname == 'admin' and password == 'admin':
                return redirect(url_for('admin_page'))

            # If staff login redirect to staff dashboard
            else:
                return redirect(url_for('dashboard'))

        # Error message if login details not in database
        else:
            return render_template('login.html',
                                    error='Invalid username or password.')

    return render_template('login.html', error=None)


# Define route to staff dashboard page
@app.route('/dashboard')
def dashboard():
    try:
        'user_id' in session
        # Retrieve user data from the session
        staff_id_val = session['user_id']
        first_name = session['first_name']
        surname = session['surname']

        return render_template('dashboard.html', staff_id_val=staff_id_val,
                                first_name=first_name, surname=surname)
    except:
        return redirect(url_for('login'))


# Define route to personal timetable
@app.route('/personal_timetable')
def personal_timetable():

    # Get staff details from database
    staff_data = get_staff_data()

    # Get data from the Shifts table
    shifts_data = get_shifts_data()

    # Get data from the Time Off table
    time_off_data = get_time_off_data()

    # Create a timetable data dictionary to store shift information
    timetable_data = {}

    # Iterate through each shift in the Shifts table
    for shift_data in shifts_data:
        shift_id, start_time_day, end_time_day, staff_id, job = shift_data
        # If staff doesn't have an entry in the dictionary create one
        if staff_id not in timetable_data:
            timetable_data[staff_id] = []
        # Store the shift information in list for each staff member
        timetable_data[staff_id].append({
            'start_time_day': start_time_day,
            'end_time_day': end_time_day
        })

    # Sort shifts for each staff by start_time_day
    for staff_id in timetable_data:
        timetable_data[staff_id].sort(key=lambda x: x['start_time_day'])

    # Empty dictionary to store weeks for which timetable can be seen
    weeks_21 = {}
    # Initalise for current week
    this_monday = get_mon(date.today())

    # Iterate for range of 21 weeks (10 before and 10 after current date) for
    # timetable to be seen defining monday date of each week
    for i in range(-10, 11):
        weeks_21[i] = week_values(this_monday + timedelta(weeks=i))

    # relative week defines week that is being viewed in the
    # timetable (0 being current and default)
    relative_week = int(request.args.get('relative_week',
                        session.get('relative_week', 0)))
    session['relative_week'] = relative_week

    try:
        'user_id' in session
        # Get user data from the session
        staff_id_val = session['user_id']
        first_name = session['first_name']
        surname = session['surname']

        # Call personal timetable view
        return render_template('personal_timetable.html',
                                staff_data=staff_data,
                                timetable_data=timetable_data,
                                time_off_data=time_off_data,
                                weeks_21=weeks_21,
                                relative_week=relative_week,
                                staff_id_val=staff_id_val,
                                first_name=first_name,
                                surname=surname)
    except:
        # If no user details return to dashboard
        return redirect(url_for('dashboard'))


# Define route to request time off
@app.route('/request_t_o', methods=['GET', 'POST'])
def request_t_o():
    # Get user details from session
    if 'user_id' in session:
        staff_id = session['user_id']
        first_name = session['first_name']
        surname = session['surname']

        # If request submitted the run following code
        if request.method == 'POST':
            # Get time off request details from form
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            reason = request.form['reason']

            # Insert request details into Time Off table in database
            cursor = connection.cursor()

            insert_query = "INSERT INTO \"nopalito_schema\".\"time_off\" " \
                            "(staff_id, start_date, end_date, reason) " \
                            "VALUES (%s, %s, %s, %s);"
            cursor.execute(insert_query,
                            (staff_id, start_date, end_date, reason))
            connection.commit()

            cursor.close()

            return redirect(url_for('dashboard'))

        # If the request method is GET (ie no request submitted),
        # render the template with the form
        return render_template('request_t_o.html', first_name=first_name,
                                surname=surname, staff_id=staff_id)
    else:
        return redirect(url_for('login'))


# Define route to admin page
@app.route('/admin_page')
def admin_page():
    try:
        'user_id' in session
        return render_template('admin_page.html')
    except:
        return redirect(url_for('login'))


# Define route to view requests
@app.route('/requests')
def requests():
    if 'user_id' in session:
        # Fetch all unresolved time off requests where 'approved' is null
        cursor = connection.cursor()

        select_query = "SELECT staff_id, start_date, end_date, reason, " \
                        "request_id FROM \"nopalito_schema\".\"time_off\" " \
                        "WHERE approved IS NULL;"
        cursor.execute(select_query)
        unresolved_requests = cursor.fetchall()

        # Fetch all resolved time off requests where 'approved' is not null
        resolved_query = "SELECT staff_id, start_date, end_date, reason, " \
                        "approved, request_id " \
                        "FROM \"nopalito_schema\".\"time_off\" " \
                        "WHERE approved IS NOT NULL;"
        cursor.execute(resolved_query)
        resolved_requests = cursor.fetchall()

        cursor.close()

        return render_template('requests.html',
                                unresolved_requests=unresolved_requests,
                                resolved_requests=resolved_requests)

    return redirect(url_for('login'))


# Define route for processing request approval/denial
@app.route('/process_request/<int:request_id>/<status>', methods=['POST'])
def process_request(request_id, status):
    if 'user_id' in session:

        cursor = connection.cursor()

        # Where request has been approved set to true in database
        # for request id defined
        if status == 'approve':
            update_query = "UPDATE \"nopalito_schema\".\"time_off\" " \
                            "SET approved = TRUE WHERE request_id = %s;"
        # Where request has been declined set to false in database
        # for request id defined
        else:
            update_query = "UPDATE \"nopalito_schema\".\"time_off\" " \
                            "SET approved = FALSE WHERE request_id = %s;"

        cursor.execute(update_query, (request_id,))
        connection.commit()

        cursor.close()

        return redirect(url_for('requests'))

    return redirect(url_for('login'))


# Define route to new shift creation
@app.route('/new_shift', methods=['GET', 'POST'])
def new_shift():
    cursor = connection.cursor()

    # Get and transform availability data from database
    query = "SELECT * FROM \"nopalito_schema\".\"availability\";"
    cursor.execute(query)
    avail_data = cursor.fetchall()
    avail_data_json = json.dumps(avail_data, default=custom_serializer)

    # Get and transform staff data from database
    # query = "SELECT staff_id, first_name, surname, job_title, start_date, " \
    #         "end_date, wage FROM \"nopalito_schema\".\"staff\";"
    # cursor.execute(query)
    # staff_data = cursor.fetchall()
    staff_data = get_staff_data()
    staff_data_json = json.dumps(staff_data, default=custom_serializer)

    # Get and transform time off data from database
    time_off = get_time_off_data()
    time_off_json = json.dumps(time_off, default=custom_serializer)

    # Get and transform shifts data from database
    shifts_data = get_shifts_data()
    shifts_data_json = json.dumps(shifts_data, default=custom_serializer)

    # If new shift creation posted then run following
    if request.method == 'POST':
        # Get selected staff ids from checkboxes
        selected_staff_ids_str = request.form['staff_ids']
        selected_staff_ids = ast.literal_eval(selected_staff_ids_str)

        # Get shift submission details
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        date_value = request.form['date']
        job_value = request.form['job']

        # Insert new shift into database
        cursor = connection.cursor()
        insert_query = "INSERT INTO \"nopalito_schema\".\"shifts\" " \
                        "(staff_id, start_time_day, end_time_day, job) " \
                        "VALUES (%s, %s, %s, %s);"
        for staff_id in selected_staff_ids:
            cursor.execute(insert_query, (staff_id,
                                            f"{date_value} {start_time}",
                                            f"{date_value} {end_time}",
                                            job_value))

        connection.commit()
        cursor.close()

        return redirect(url_for('new_shift'))

    return render_template('new_shift_orig.html', avail_data=avail_data_json,
                            staff_data=staff_data_json, time_off=time_off_json,
                            shifts_data=shifts_data_json)


# Define route to registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    # If registration submitted run following
    if request.method == 'POST':
        # Get details from submission form
        first_name = request.form['first_name']
        surname = request.form['surname']
        phone_number = request.form['phone_number']
        ni_number = request.form['ni_number']
        job = request.form['job']
        uname = request.form['username']
        password = request.form['password']
        ############################################################################### need to add in other detail here and below and in html

        # Check if the username already exists in the database
        cursor = connection.cursor()

        query = "SELECT staff_id FROM \"nopalito_schema\".\"staff\" " \
                "WHERE uname = %s;"
        cursor.execute(query, (uname,))
        existing_user = cursor.fetchone()

        # If username already exists return error
        if existing_user:
            cursor.close()
            return render_template('register.html',
                                    error='Username already exists.')

        # If the username is unique, add the new user to the database
        length_query = "SELECT COUNT(staff_id) FROM \"nopalito_schema\".\"staff\";"
        cursor.execute(length_query)
        num_ids = cursor.fetchone()
        new_id = num_ids[0] + 1

        insert_query = "INSERT INTO \"nopalito_schema\".\"staff\" " \
                        "(staff_id, first_name, surname, start_date, phone_number, " \
                        "ni_number, job_title, uname, password) " \
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        cursor.execute(insert_query, (new_id, first_name, surname, datetime.today(),
                                    phone_number, ni_number, job, uname, password))
        connection.commit()

        cursor.close()

        # Redirect the user to the login page after successful registration.
        return redirect(url_for('login'))

    return render_template('register.html', error=None)


# Define route to timetable view
@app.route('/timetable')
def timetable():
    cursor = connection.cursor()

    # Get data from Staff table
    staff_data = get_staff_data()

    # Get data from the Shifts table
    shifts_data = get_shifts_data()

    # Get data from the Time Off table
    time_off_data = get_time_off_data()

    # Create a timetable data structure to store shift information
    timetable_data = {}

    # Iterte over each shift entry in table
    for shift_data in shifts_data:
        shift_id, start_time_day, end_time_day, staff_id, job = shift_data
        # If staff id not in dictionary already then add new key
        if staff_id not in timetable_data:
            timetable_data[staff_id] = []
        # Assign shift to appropriate staff id in list
        timetable_data[staff_id].append({
            'start_time_day': start_time_day,
            'end_time_day': end_time_day
        })

    # Sort shifts for each staff by start_time_day
    for staff_id in timetable_data:
        timetable_data[staff_id].sort(key=lambda x: x['start_time_day'])

    # Empty dictionary to store weeks for which timetable can be seen
    weeks_21 = {}
    # Initalise for current week
    this_monday = get_mon(date.today())

    # Iterate for range of 21 weeks (10 before and 10 after current date)
    # for timetable to be seen defining monday date of each week
    for i in range(-10, 11):
        weeks_21[i] = week_values(this_monday + timedelta(weeks=i))

    # relative week defines week that is being viewed in the timetable
    # (0 being current and default)
    relative_week = int(request.args.get('relative_week',
                                        session.get('relative_week', 0)))
    session['relative_week'] = relative_week

    return render_template('timetable.html', staff_data=staff_data,
                            timetable_data=timetable_data,
                            time_off_data=time_off_data,
                            weeks_21=weeks_21,
                            relative_week=relative_week)


# def str_to_date(date_str):
#     return datetime.strptime(date_str, '%Y-%m-%d').date()

# # Pass str_to_date function to html for use
# app.jinja_env.filters['str_to_date'] = str_to_date

if __name__ == '__main__':
    app.run(debug=True)
