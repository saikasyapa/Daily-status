from flask import Flask,request,render_template,redirect,url_for,flash,session,Response,send_file,Request
import psycopg2
from datetime import datetime,timedelta
from io import StringIO
import csv
import io
import pandas as pd
import logging
logging.basicConfig(level=logging.DEBUG)
from flask import make_response
import math
from sqlalchemy import create_engine
from urllib.parse import quote
import pytz
# from flask_mail import Mail, Message


app = Flask(__name__)
app.secret_key = 'magnasoft'

############################################ Connection To Database ###############################

def get_db_connection():
    conn = psycopg2.connect(
        dbname='MTAG_Request',
        user = 'postgres',
        password= 'dev',
        host='10.10.10.163',
        port='5432'
    )
    return conn

myusername = 'postgres'
mypassword = 'dev'
myhost = '10.10.10.163'
myport = '5432'
mydatabase = 'MTAG_Request'


password_encoded = quote(mypassword)


engine = create_engine(f'postgresql://{myusername}:{password_encoded}@{myhost}:{myport}/{mydatabase}')


# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'xxxxx'
# app.config['MAIL_PASSWORD'] = 'xxxxxx'
# app.config['MAIL_DEFAULT_SENDER'] = 'xxxxx'

# mail = Mail(app)



########################### Defining a function to create a Register table whenever the host is changed ##################################################



def create_table_if_not_exist():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS master_user (
                s_no SERIAL PRIMARY KEY,
                employee_name VARCHAR(100) UNIQUE,
                employee_id VARCHAR(10) UNIQUE,
                email VARCHAR(50) UNIQUE,
                designation VARCHAR(20),
                username VARCHAR(50) UNIQUE,
                password VARCHAR(50)
                )
            """)
    conn.commit()
    cur.close()
    conn.close()


########################################## Registration Page ####################################

@app.route("/registerform",methods=['GET','POST'])
def registerform():
    if request.method == 'POST':
        employee_name = request.form['employee_name']
        employee_id = request.form['employee_id']
        email = request.form['email']
        designation = request.form['designation']
        username = request.form['username']
        password = request.form['password']
        
        create_table_if_not_exist()

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute ("""INSERT INTO master_user (employee_name,employee_id,email,designation,username,password) VALUES (%s,%s,%s,%s,%s,%s)""",
                        (employee_name, employee_id, email, designation, username, password))
            conn.commit()
            # msg = Message('Successfully Registered For MTAG Request Page',
            #               recipients=[email])
            # msg.html = f"""
            # <html>
            # <body>
            # <p> Hello {username},<p>
            # <p> You are successfully registered for MTAG Request page with the below details </p>
            # <table border ="1" style = "border-collapse:collapse">
            # <tr>
            # <th>Name<ith>
            # <td>{employee_name}</td>
            # </tr>
            # <tr>
            # <th>ID<ith>
            # <td>{employee_id}</td>
            # </tr>
            # <tr>
            # <th>Email<ith>
            # <td>{email}</td>
            # </tr>
            # <tr>
            # <th>Designation<ith>
            # <td>{designation}</td>
            # </tr>
            # <tr>
            # <th>Username<ith>
            # <td>{username}</td>
            # </tr>
            # <tr>
            # <th>Password<ith>
            # <td>{password}</td>
            # </tr>
            # </table>
            # <p>Thanks & Regards</p>
            # <p>MTAG Team</p>
            # </body>
            # </html>
            # """

            # mail.send(msg)
            flash("Successfully Registered",'success')
            return redirect(url_for('home'))
        except psycopg2.errors.UniqueViolation as e:
            conn.rollback()
            if 'master_user_employee_id_key' in str(e):
                flash('Employee ID already registered', 'error')
            elif 'master_user_employee_name_key' in str(e):
                flash('Employee Name already registered', 'error')
            elif 'master_user_email_key' in str(e):
                flash('Email already registerd', 'error')
            elif 'master_user_username' in str(e):
                flash('username already registered')
            else:
                flash('Registration Failed', 'error')
        finally:
            cur.close()
            conn.close()
    return render_template('registerform.html')



@app.route('/forgot_password',methods=['POST','GET'])
def forgot_password():
    if request.method == 'POST':
        email = session.get()



############################################### Login Page #############################################

@app.route("/" ,methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn=get_db_connection()
        cur = conn.cursor()
        
        create_table_if_not_exist_1_()
        create_table_if_not_exist_2_()
        
        cur.execute("SELECT password, designation, employee_id FROM master_user WHERE username = %s",(username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        if result and result[0] == password:
            flash('Login Successful', 'success')
            session['logged_in'] = True
            session['username'] = username
            session['designation'] = result[1].strip().lower()
            session['employee_id'] = result[2]
            session['email'] = result[0]
            # return redirect(url_for('admin'))
            if 'developer' in session['designation'] :
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('admin'))
        else:
            flash('Invalid username and password','danger')
    return render_template('login.html' )


@app.route('/logout')
def logout():
    session.pop('logged_in',None)
    session.pop('username', None)
    session.pop('designation',None)
    flash('You Successfully  logged out', 'success')
    return redirect(url_for('home'))

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=45)
    

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


######################################################### Admin Page ############################################

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    
    # if 'developer' not in session.get('designation', ''):
    #     flash('Access Denied: Only developers can access this page','danger')
    #     return redirect(url_for('home'))
    
    
    
    query = '''
        SELECT 
            COALESCE(status) AS status, 
            COUNT(s_no) AS num_requests
        FROM master_request_new 
        GROUP BY status
    '''
    df = pd.read_sql_query(query, engine)
    
    
    

    graph_data = {
        'labels': df['status'].tolist(),
        'data': df['num_requests'].tolist()
    }
    

    return render_template('admin.html', graph_data=graph_data, table_data=df )


########################### Defining a function to  create a Datastorage table whenever the host is changed ##################################################


# Function to create the table if it doesn't exist
# def create_table_if_not_exist_1_():
#     conn = get_db_connection()  # Obtain the database connection
#     cur = conn.cursor()  # Create a cursor object to interact with the database
    
#     # SQL statement to create the table if it doesn't exist
#     cur.execute("""
#                 CREATE TABLE IF NOT EXISTS master_request_new (
#                     s_no SERIAL PRIMARY KEY,
#                     department VARCHAR(100),
#                     project_name VARCHAR(100),
#                     request_description TEXT,
#                     username VARCHAR(100),
#                     time_saving_hours INTEGER,
#                     priority VARCHAR(20),
#                     raised_date TIMESTAMP WITHOUT TIME ZONE,
#                     start_date TIMESTAMP WITHOUT TIME ZONE,
#                     end_date TIMESTAMP WITHOUT TIME ZONE,
#                     developer_name VARCHAR(100),
#                     request_type VARCHAR(50),
#                     status VARCHAR(50)
#                 )
#             """)
    
#     # Set the initial value of s_no sequence to 1000
#     cur.execute("ALTER SEQUENCE master_request_new_s_no_seq RESTART WITH 1000")
    
#     conn.commit()  # Commit the transaction
#     cur.close()  # Close the cursor
#     conn.close()  # Close the database connection

def create_table_if_not_exist_1_():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Create the table if it does not exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS master_request_new(
                s_no SERIAL PRIMARY KEY,
                department VARCHAR(100),
                project_name VARCHAR(100),
                request_description TEXT,
                username VARCHAR(100),
                actual_time INTEGER NOT NULL CHECK (actual_time <> 0),
                units_of_measurement VARCHAR(500),
                time_saving_hours VARCHAR(100),
                priority VARCHAR(20),
                raised_date DATE,
                start_date DATE,
                end_date DATE,
                developer_name VARCHAR(100),
                request_type VARCHAR(50),
                status VARCHAR(50)
            )
        """)

        # Drop existing sequence if it exists and create a new one
        cur.execute("""DROP SEQUENCE IF EXISTS s_no_seq;""")
        cur.execute("""CREATE SEQUENCE s_no_seq START 1001;""")
        
        # Alter the table to use the new sequence for the s_no column
        cur.execute("""ALTER TABLE master_request_new ALTER COLUMN s_no SET DEFAULT nextval('s_no_seq');""")
        
        # Optionally, update the existing sequence to start at 1001
        cur.execute("""ALTER SEQUENCE s_no_seq RESTART WITH 1001;""")
        
        # Optionally, update existing rows to use the sequence
        cur.execute("""
            DO $$
            DECLARE
                row RECORD;
            BEGIN
                FOR row IN SELECT * FROM master_request_new ORDER BY s_no LOOP
                    UPDATE master_request_new
                    SET s_no = nextval('s_no_seq')
                    WHERE CURRENT OF row;
                END LOOP;
            END $$;
        """)

        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


###################################################  Request Page ####################################################

@app.route("/requestform",methods=['GET', 'POST'])
def requestform():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        # s_no = request.form['s_no']
        department = request.form['department']
        project_name = request.form['project_name']
        request_description = request.form['request_description']
        username = session.get('username')
        actual_time = request.form['actual_time']
        units_of_measurement = request.form['units_of_measurement']
        time_saving_hours = request.form['time_saving_hours']
        priority = request.form['priority']
        request_type = request.form['request_type']
        status = "YTS"
        current_date=datetime.now().date()
        
        # indian_tz = pytz.timezone('Asia/kolkata')
        # current_datetime_ist = current_datetime_utc.astimezone(indian_tz)
        
        
        

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("""INSERT INTO master_request_new (department,project_name,request_description,username, actual_time, units_of_measurement, time_saving_hours,priority,request_type,raised_date, status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING s_no """,
                        (department,project_name,request_description,username, actual_time, units_of_measurement, time_saving_hours,priority,request_type,current_date,status))
            s_no = cur.fetchone()[0]
            conn.commit()
            

            # cur.execute("SELECT email FROM master_user WHERE username = %s", (username,))
            # user_email = cur.fetchone()[0]
            

            # cc_email = "kiran.hs@india.magnasoft.com"

            # msg = Message('Request Submission Conformation',
            #               recipients=[user_email],cc=[cc_email])
            # msg.html = f"""
            # <html>
            # <body>
            # <p>Hello {username}</p>
            # <p> Your request is successfully submitted with below details</p>
            # <table border="1" style="border-collapse:collapse;">
            # <tr>
            # <th>Request ID</th>
            # <td>{s_no}</td>
            # </tr>
            # <tr>
            # <th>Department</th>
            # <td>{department}</td>
            # </tr>
            # <tr>
            # <th>Project Name</th>
            # <td>{project_name}</td>
            # </tr>
            # <tr>
            # <th>Request Description</th>
            # <td>{request_description}</td>
            # </tr>
            # <tr>
            # <th>Actual Time</th>
            # <td>{actual_time}</td>
            # </tr>
            # <tr>
            # <th>Units Of Measurement</th>
            # <td>{units_of_measurement}</td>
            # </tr>
            # <tr>
            # <th>Time Saving Hours</th>
            # <td>{time_saving_hours}</td>
            # </tr>
            # <tr>
            # <th>Priority</th>
            # <td>{priority}</td>
            # </tr>
            # <tr>
            # <th>Request Type</th>
            # <td>{request_type}</td>
            # </tr>
            # </table>
            # <p> Thanks & Regards </p>
            # <p> MTAG Request </p>
            # </body>
            # </html>
            # """
            # mail.send(msg)

            flash('Request submitted successfully!', 'success')
            return redirect(url_for('viewtable'))
        except Exception as e:
            flash('Error' + str(e), 'danger')
        finally:
            cur.close()
            conn.close()
    return render_template('request.html' )



##################################################### Assign Request Page #######################################################

@app.route("/table",methods=['GET','POST'] )
def table():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    
    if 'developer' not in session.get('designation', ''):
        flash('Access Denied: Only developers can access this page','danger')
        return redirect(url_for('home'))
    page = request.args.get('page',1,type=int)
    per_page = 15

    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM master_request_new')
    total = cur.fetchone()[0]
    cur.execute('SELECT s_no,department,project_name,request_description,username,actual_time,time_saving_hours,units_of_measurement,raised_date,start_date,end_date,developer_name,request_type,status  FROM master_request_new ORDER BY s_no DESC LIMIT %s OFFSET %s',(per_page,(page - 1) * per_page))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    total_pages = math.ceil(total / per_page)
    return render_template('table.html',rows=rows,colnames=colnames,page=page,per_page=per_page, total=total, total_pages=total_pages)


################################################################ View Request page ############################################################################


@app.route("/viewtable",methods=['GET','POST'] )
def viewtable():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    page = request.args.get('page',1,type=int)
    per_page = 15
    

    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM master_request_new')
    total = cur.fetchone()[0]
    cur.execute('SELECT s_no,department,project_name,request_description,username,actual_time, time_saving_hours,units_of_measurement,raised_date,start_date,end_date,developer_name,request_type,status  FROM master_request_new ORDER BY s_no DESC LIMIT %s OFFSET %s',(per_page,(page - 1) * per_page))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()

    total_pages = math.ceil(total / per_page)
    return render_template('view_table.html',rows=rows,colnames=colnames,page=page,per_page=per_page, total=total, total_pages=total_pages)



################################################### Update The Table ########################################

@app.route('/update', methods=['POST'])
def update():
    s_no = request.form['s_no']
    status = request.form['status']
    developer_name = session.get('username')

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        start_date = None
        end_date = None

        # Retrieve current start_date from the database
        cur.execute("SELECT start_date FROM master_request_new WHERE s_no = %s", (s_no,))
        row = cur.fetchone()
        if row:
            start_date = row[0]

        if status == 'WIP':
            start_date = datetime.now(pytz.utc)  # Current UTC time
            indian_tz = pytz.timezone('Asia/Kolkata')
            start_date = start_date.astimezone(indian_tz)  # Convert to IST
        elif status == 'Comp':
            end_date = datetime.now(pytz.utc)  # Current UTC time
            indian_tz = pytz.timezone('Asia/Kolkata')
            end_date = end_date.astimezone(indian_tz)

        cur.execute("""
            UPDATE master_request_new
            SET start_date = %s, end_date = %s, status = %s, developer_name = %s
            WHERE s_no = %s
        """, (start_date, end_date, status, developer_name, s_no))

        conn.commit()

    except Exception as e:
        return str(e)
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('table'))



########################################### Adding Filters to Assign Request Table #####################################

@app.route('/filter', methods=['GET','POST'])
def filter():
    
    filter_s_no = request.args.get('filter_s_no','')
    filter_department = request.args.get('filter_department','')
    filter_project_name = request.args.get('filter_project_name','')
    filter_developer_name = request.args.get('filter_developer_name' , '')
    filter_status=request.args.get('filter_status','')
    sort_by = request.args.get('sort_by', 's_no')
    sort_order = request.args.get('sort_order','DESC')

    conn=get_db_connection()
    cursor=conn.cursor()

    query = """SELECT s_no, department, project_name, request_description, username,actual_time, time_saving_hours,units_of_measurement, raised_date, start_date, end_date, developer_name, request_type, status FROM master_request_new WHERE 1=1 """
    params=[]

    if filter_s_no:
        query += 'AND s_no = %s'
        params.append(filter_s_no)

    if filter_department:
        query += 'AND department ILIKE %s'
        params.append(f"%{filter_department}%")
    
    if filter_project_name:
        query += 'AND project_name ILIKE %s'
        params.append(f"%{filter_project_name}%")

    # if filter_developer_name:
    #     query += 'AND developer_name ILIKE %s'
    #     params.append(f"%{filter_developer_name}%")
    if filter_developer_name:
        query += 'AND developer_name=%s'
        params.append(filter_developer_name)

    if filter_status:
        query += "AND status = %s"
        params.append(filter_status)

    query += f'ORDER BY {sort_by} {sort_order} '
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()
    return render_template('table.html' , rows=rows, colnames=colnames, page=None, per_page=None, total=None, total_pages=None,filter_s_no=filter_s_no,filter_department=filter_department,filter_project_name=filter_project_name,filter_developer_name=filter_developer_name,filter_status=filter_status)


########################################### Adding Filters to View Request Table #####################################


@app.route('/viewfilter', methods=['GET','POST'])
def viewfilter():
    filter_s_no = request.args.get('filter_s_no','')
    filter_department = request.args.get('filter_department','')
    filter_project_name = request.args.get('filter_project_name','')
    filter_developer_name = request.args.get('filter_developer_name' , '')
    filter_status=request.args.get('filter_status','')
    sort_by = request.args.get('sort_by', 's_no')
    sort_order = request.args.get('sort_order','DESC')

    conn=get_db_connection()
    cursor=conn.cursor()

    query = """SELECT s_no, department, project_name, request_description, username,actual_time, time_saving_hours,units_of_measurement, raised_date, start_date, end_date, developer_name, request_type, status FROM master_request_new WHERE 1=1 """
    params=[]

    if filter_s_no:
        query += 'AND s_no = %s'
        params.append(filter_s_no)

    if filter_department:
        query += 'AND department ILIKE %s'
        params.append(f"%{filter_department}%")
    
    if filter_project_name:
        query += 'AND project_name ILIKE %s'
        params.append(f"%{filter_project_name}%")

    if filter_developer_name:
        query += 'AND developer_name=%s'
        params.append(filter_developer_name)

    if filter_status:
        query += "AND status = %s"
        params.append(filter_status)

    query += f'ORDER BY {sort_by} {sort_order}'
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    colnames = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()
    return render_template('view_table.html' , rows=rows, colnames=colnames, page=None, per_page=None, total=None, total_pages=None,filter_s_no=filter_s_no,filter_department=filter_department,filter_project_name=filter_project_name,filter_developer_name=filter_developer_name,filter_status=filter_status)


############################################## Export Table To CSV ############################################################


@app.route('/export_csv', methods=['POST','GET'])
def export_csv():
    conn=get_db_connection()
    cursor=conn.cursor()

    query="""SELECT s_no, department, project_name, request_description, username, time_saving_hours, priority, raised_date, start_date, end_date, developer_name, request_type, status, actual_time, units_of_measurement FROM master_request_new"""
    cursor.execute(query)
    rows = cursor.fetchall()

    output = io.StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow([i[0] for i in cursor.description])
    csv_writer.writerows(rows)

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=static/data.csv"}
    )
    
############################################## Defining funtion to table whenever data is not there ############################################################
# 
#     
def create_table_if_not_exist_2_():
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS developer_status
                (s_no SERIAL PRIMARY KEY,
                developer_name VARCHAR(100),
                developer_id VARCHAR(20),
                project_name VARCHAR(100),
                task_activity VARCHAR(500),
                task_description TEXT,
                start_date TIMESTAMP WITH TIME ZONE,
                end_date TIMESTAMP WITH TIME ZONE,
                status VARCHAR(100),
                total_hours varchar(100))
        """)
    conn.commit()
    cur.close()
    conn.close()

############################################## Developer status page ############################################################    


@app.route('/developer_status', methods=['POST', 'GET'])
def developer_status():
    if 'developer' not in session.get('designation', ''):
        flash('Access Denied: Only developers can access this page', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        developer_name = session.get('username')
        developer_id = session.get('employee_id')
        project_name = request.form['project_name']
        task_activity = request.form['task_activity']
        task_description = request.form['task_description']
        status = "Working"
        
        # Set current time to IST
        indian_tz = pytz.timezone('Asia/Kolkata')
        current_datetime_ist = datetime.now(indian_tz).replace(second=0, microsecond=0)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            # Ensure the session timezone is set correctly
            cur.execute("SET TIMEZONE='Asia/Kolkata';")
            cur.execute("""SELECT COUNT(*) FROM developer_status WHERE developer_name = %s AND status = 'Working' """,
                        (developer_name,)

            )
            ongoing_tasks = cur.fetchone()[0]

            if ongoing_tasks > 0:
                flash("You already have a ongoing task. complete or hold the current task before adding new one", 'warning')
                return redirect(url_for('developer_status'))
            
            cur.execute(
                """INSERT INTO developer_status 
                   (developer_name, developer_id, project_name, task_activity, task_description, start_date, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (developer_name, developer_id, project_name, task_activity, task_description, current_datetime_ist, status)
            )
            conn.commit()
            
            flash('Request submitted successfully', 'success')
            return redirect(url_for('developer_status'))
        except Exception as e:
            flash('Error: ' + str(e), 'danger')
        finally:
            cur.close()
            conn.close()
    
    developer_name = session.get('username')
    today = datetime.now().date()
    # page = request.args.get('page', 1, type=int)
    # per_page = 15
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ensure the session timezone is set correctly
    cur.execute("SET TIMEZONE='Asia/Kolkata';")
    
    # cur.execute('SELECT COUNT(*) FROM developer_status')
    # total = cur.fetchone()[0]
    # cur.execute(
    #     '''SELECT * FROM developer_status 
    #     WHERE developer_name = %s  AND 
    #     ((DATE(start_date) = %s OR DATE(end_date) = %s) OR 
    #     status IN (%s, %s))
    #     ORDER BY s_no DESC LIMIT %s OFFSET %s''',
    #     (developer_name, today, today, 'Working','Hold', per_page, (page - 1) * per_page)
    # )
    cur.execute(
        '''SELECT * FROM developer_status 
        WHERE developer_name = %s  AND 
        ((DATE(start_date) = %s OR DATE(end_date) = %s) OR 
        status IN (%s, %s))
        ORDER BY s_no DESC''',
        (developer_name, today, today, 'Working','Hold')
    )
    
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    conn.commit()
    cur.close()
    conn.close()
    # total_pages = math.ceil(total / per_page)
    # return render_template('dev_status.html', rows=rows, colnames=colnames, page=page, per_page=per_page, total=total, total_pages=total_pages)
    return render_template('dev_status.html', rows=rows, colnames=colnames)




############################################## Developer status update ############################################################


@app.route('/developer_update', methods=['POST'])
def developer_update():
    s_no = request.form['s_no']
    status = request.form['status']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SET TIMEZONE='Asia/Kolkata';")

        if status == 'Comp' or status == 'Hold':

            cur.execute("SELECT status FROM developer_status WHERE s_no = %s",(s_no,))
            completed_tasks = cur.fetchone()[0]

            if completed_tasks != 'Working':
                flash("You can Completed or hold the tasks if the status is working ", 'warning')
                return redirect(url_for('developer_status'))
            
            # Update existing row with 'Comp' or 'Hold' status and calculate total hours
            cur.execute("SELECT start_date FROM developer_status WHERE s_no = %s", (s_no,))
            start_time = cur.fetchone()[0]
            # start_time_str = cur.fetchone()[0]
            # start_time = pd.to_datetime(start_time_str)
            
            
            # indian_tz = pytz.timezone('Asia/Kolkata')
            # end_date_utc = datetime.now(pytz.utc)
            # end_date_ist = end_date_utc.astimezone(indian_tz)
            indian_tz = pytz.timezone('Asia/Kolkata')
            end_datetime_ist = datetime.now(indian_tz).replace(second=0, microsecond=0)
            
            
            
            total_seconds = (end_datetime_ist - start_time).total_seconds()
            total_hours = total_seconds / 3600.0

            whole_hours = int(total_hours)
            remaining_minutes = (total_hours - whole_hours) * 60

            
            # total_hours_str = f"{whole_hours} hour {remaining_minutes:.0f} minutes"
            total_hours_str = f"{whole_hours}.{remaining_minutes:.0f} "
            
            cur.execute("""
                UPDATE developer_status
                SET end_date = %s, status = %s, total_hours = %s
                WHERE s_no = %s
            """, (end_datetime_ist, status, total_hours_str, s_no))
        
        elif status == 'Reassign':

            cur.execute("SELECT status FROM developer_status WHERE s_no = %s",(s_no,))
            Hold_tasks = cur.fetchone()[0]

            if Hold_tasks != 'Hold':
                flash("You can  reassign the task if the status is Hold ", 'warning')
                return redirect(url_for('developer_status'))
            # Retrieve current row data
            cur.execute("SELECT developer_name, developer_id, project_name, task_activity, task_description FROM developer_status WHERE s_no = %s", (s_no,))
            current_row = cur.fetchone()
            
            if current_row:
                # Insert new row with current date and 'Working' status
                current_date_time = datetime.now(pytz.timezone('Asia/Kolkata'))
                new_row_data = current_row + (current_date_time, 'Working',)
                
                cur.execute("""
                    INSERT INTO developer_status (developer_name, developer_id, project_name, task_activity, task_description, start_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, new_row_data)


                # cur.execute(""" UPDATE developer_status SET status = 'Comp' WHERE s_no = %s""",(s_no,) )
        
        conn.commit()

    except Exception as e:
        return str(e)
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('developer_status'))



############################################## Total team daily status page ############################################################

@app.route('/team_status',methods=['POST','GET'])
def team_status():

    if not session.get('logged_in'):
        return redirect(url_for('home'))


    if 'developer' not in session.get('designation', ''):
        flash('Access Denied: Only developers can access this page','danger')
        return redirect(url_for('home'))

    page = request.args.get('page',1,type=int)
    per_page = 60

    conn=get_db_connection()
    cur=conn.cursor()

    cur.execute("SET TIMEZONE='Asia/Kolkata';")

    cur.execute('SELECT COUNT(*) FROM developer_status')
    total = cur.fetchone()[0]
    conn.commit()

    cur.execute('SELECT SUM(CAST(total_hours AS FLOAT)) FROM developer_status')
    total_hours_all = cur.fetchone()[0] or 0 

    cur.execute('SELECT * FROM developer_status ORDER BY s_no DESC LIMIT %s OFFSET %s',(per_page,(page - 1) * per_page)) 
    rows = cur.fetchall()
    conn.commit()

    colnames = [desc[0] for desc in cur.description]
    total_minutes = 0
    for row in rows:
        if row[9] is not None:

            try:
                total_minutes += int(float(row[9]) * 60)
            except ValueError:
                continue

    
    total_hours= total_minutes // 60
    remaining_minutes = total_minutes % 60
    formatted_total_hours_page = f"{total_hours} hours {remaining_minutes} minutes"
    conn.commit()
    cur.close()
    conn.close()


    total_pages = math.ceil(total / per_page)

    formatted_total_hours_all = f"{int(total_hours_all)} hours {int((total_hours_all - int(total_hours_all))*60)} minutes"

    return render_template('team_status.html', rows=rows, colnames=colnames, page=page, per_page=per_page, total=total, total_pages=total_pages,formatted_total_hours_page=formatted_total_hours_page,formatted_total_hours_all=formatted_total_hours_all)


############################################## Total team daily status page filter ############################################################


@app.route('/team_filter', methods=['GET'])
def team_filter():
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')
    filter_developer_name = request.args.get('filter_developer_name', '')
    filter_status = request.args.get('filter_status', '')
    sort_by = request.args.get('sort_by', 's_no')
    sort_order = request.args.get('sort_order', 'DESC')

    conn = get_db_connection()
    cur = conn.cursor()

    query = """SELECT * FROM developer_status WHERE 1=1 """
    params = []
    

    if start_date_filter:
        query += "AND start_date >= %s "
        params.append(start_date_filter)

    if end_date_filter:
        query += "AND start_date <= %s "
        params.append(end_date_filter)

    if filter_developer_name:
        query += 'AND developer_id ILIKE %s '
        params.append(f"%{filter_developer_name}%")

    if filter_status:
        query += "AND status = %s "
        params.append(filter_status)

    query += f'ORDER BY {sort_by} {sort_order}'
    

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    total_minutes = 0
    for row in rows:
        if row[9] is not None:

            try:
                total_minutes += int(float(row[9]) * 60)
            except ValueError:
                continue

    
    total_hours= total_minutes // 60
    remaining_minutes = total_minutes % 60
    formatted_total_hours_all = f"{total_hours} hours {remaining_minutes} minutes"
    cur.close()
    conn.close()

    return render_template(
        'team_status.html',
        rows=rows,
        colnames=colnames,
        page=None,
        per_page=None,
        total=None,
        total_pages=None,
        start_date_filter=start_date_filter,
        end_date_filter=end_date_filter,
        filter_developer_name=filter_developer_name,
        filter_status=filter_status,
        formatted_total_hours_all=formatted_total_hours_all
    )

# @app.route('/team_filter', methods=['GET'])
# def team_filter():
#     page = request.args.get('page',1,type=int)
#     per_page = 30

    
#     start_date_filter = request.args.get('start_date_filter', '')
#     end_date_filter = request.args.get('end_date_filter','')
#     filter_developer_name = request.args.get('filter_developer_name' , '')
#     filter_status=request.args.get('filter_status','')
#     sort_by = request.args.get('sort_by', 's_no')
#     sort_order = request.args.get('sort_order','DESC')

#     conn=get_db_connection()
#     cur=conn.cursor()
#     cur.execute("SET TIMEZONE='Asia/Kolkata';")

#     query = """SELECT * FROM developer_status WHERE 1=1 """
#     params=[]

  

#     if start_date_filter:
#         query += "AND start_date >= %s"
#         params.append(start_date_filter)

#     if end_date_filter:
#         query += "AND start_date <= %s"
#         params.append(end_date_filter)

#     if filter_developer_name:
#         query += 'AND developer_id ILIKE %s'
#         params.append(f"%{filter_developer_name}%")

#     if filter_status:
#         query += "AND status = %s"
#         params.append(filter_status)

    

#     cur.execute(query, tuple(params))
#     total = cur.rowcount

#     query += f'ORDER BY {sort_by} {sort_order} LIMIT %s OFFSET %s'
#     params.extend([per_page, (page - 1) * per_page])

    
#     cur.execute(query, tuple(params))
#     rows = cur.fetchall()
#     colnames = [desc[0] for desc in cur.description]
#     cur.close()
#     conn.close()

#     total_pages = math.ceil(total / per_page)
    
#     return render_template('team_status.html', rows=rows, colnames=colnames, page=page, per_page=per_page, total=total, total_pages=total_pages)


@app.route('/admin_dev')
def developer_admin():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    
    if 'developer' not in session.get('designation', ''):
        flash('Access Denied: Only developers can access this page','danger')
        return redirect(url_for('home'))
    query = '''
    SELECT 
        COALESCE(status, 'Unknown') AS status, 
        COUNT(s_no) AS num_requests,
        SUM(CAST(total_hours AS NUMERIC)) AS total_hours
    FROM developer_status
    GROUP BY status'''

    

    # Execute the query and load into DataFrame
    df = pd.read_sql_query(query, engine)

    # Ensure total_hours is numeric and fill NaN with 0
    df['total_hours'] = pd.to_numeric(df['total_hours'], errors='coerce').fillna(0)

    # Convert total_hours to hours and minutes format
    df['total_hours_formatted'] = df['total_hours'].apply(lambda x: f"{int(x)}h {int((x % 1) * 60)}m")

    # Calculate the total hours across all statuses
    total_hours_sum = df['total_hours'].sum()

    # Calculate remaining tasks if needed (if there is any specific calculation required)
    # For now, we will not include any remaining task calculation in this example

    graph_data = {
        'labels': df['status'].tolist(),
        'data': df['num_requests'].tolist(),
        'total_hours': df['total_hours_formatted'].tolist(),
        'total_hours_sum': f"{int(total_hours_sum)}h {int((total_hours_sum % 1) * 60)}m"
    }
    
    return render_template('admin_dev.html', graph_data=graph_data, table_data=df)

@app.route('/developer_filter', methods=['GET'])
def developer_filter():
    start_date_filter = request.args.get('start_date_filter', '')
    end_date_filter = request.args.get('end_date_filter', '')
    filter_developer_name = request.args.get('filter_developer_name', '')
    filter_status = request.args.get('filter_status', '')

    conn = get_db_connection()
    cur = conn.cursor()

    query = "SELECT * FROM developer_status WHERE 1=1"
    params = []

    if start_date_filter:
        query += " AND start_date >= %s"
        params.append(start_date_filter)

    if end_date_filter:
        query += " AND start_date <= %s"
        params.append(end_date_filter)

    if filter_developer_name:
        query += " AND developer_id ILIKE %s"
        params.append(f"%{filter_developer_name}%")

    if filter_status:
        query += " AND status = %s"
        params.append(filter_status)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]

    df = pd.DataFrame(rows, columns=colnames)

    # Ensure total_hours is numeric and handle NaN values
    df['total_hours'] = pd.to_numeric(df['total_hours'], errors='coerce').fillna(0)

    # Convert total_hours to hours and minutes
    df['total_hours_formatted'] = df['total_hours'].apply(
        lambda x: f"{int(x)}h {int((x % 1) * 60)}m"
    )

    total_hours_sum = df['total_hours'].sum()

    # Prepare data for the graph
    graph_data = {
        'labels': df['status'].value_counts().index.tolist(),
        'data': df['status'].value_counts().tolist(),
        'total_hours': df['total_hours_formatted'].tolist(),
        'total_hours_sum': f"{int(total_hours_sum)}h {int((total_hours_sum % 1) * 60)}m"
    }

    return render_template('admin_dev.html', graph_data=graph_data, table_data=df.to_dict('records'))


# @app.route('/admin_dev')
# def developer_admin():
#     if not session.get('logged_in'):
#         return redirect(url_for('home'))
    
#     query = '''
#         SELECT 
#             COALESCE(status, 'Unknown') AS status, 
#             COUNT(s_no) AS num_requests
#         FROM developer_status
#         GROUP BY status
#     '''
#     df = pd.read_sql_query(query, engine)
    
#     graph_data = {
#         'labels': df['status'].tolist(),
#         'data': df['num_requests'].tolist()
#     }
    
#     return render_template('admin_dev.html', graph_data=graph_data, table_data=df)


# @app.route('/developer_filter', methods=['GET'])
# def developer_filter():
#     start_date_filter = request.args.get('start_date_filter', '')
#     end_date_filter = request.args.get('end_date_filter', '')
#     filter_developer_name = request.args.get('filter_developer_name', '')
#     filter_status = request.args.get('filter_status', '')

#     conn = get_db_connection()
#     cur = conn.cursor()

#     query = "SELECT * FROM developer_status WHERE 1=1"
#     params = []

#     if start_date_filter:
#         query += " AND start_date >= %s"
#         params.append(start_date_filter)

#     if end_date_filter:
#         query += " AND start_date <= %s"
#         params.append(end_date_filter)

#     if filter_developer_name:
#         query += " AND developer_id ILIKE %s"
#         params.append(f"%{filter_developer_name}%")

#     if filter_status:
#         query += " AND status = %s"
#         params.append(filter_status)

#     cur.execute(query, tuple(params))
#     rows = cur.fetchall()
#     colnames = [desc[0] for desc in cur.description]

#     df = pd.DataFrame(rows, columns=colnames)
#     conn.close()

#     graph_data = {
#         'labels': df['status'].value_counts().index.tolist(),
#         'data': df['status'].value_counts().tolist()
#     }

#     return render_template('admin_dev.html', graph_data=graph_data, table_data=df.to_dict('records'))


@app.route('/dev_export_csv', methods=['POST','GET'])
def dev_export_csv():
    conn=get_db_connection()
    cursor=conn.cursor()

    query="""SELECT * FROM developer_status"""
    cursor.execute(query)
    rows = cursor.fetchall()

    output = io.StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow([i[0] for i in cursor.description])
    csv_writer.writerows(rows)

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=static/data.csv"}
    )


                           



if __name__  == '__main__':
    app.run('0.0.0.0',debug=True)