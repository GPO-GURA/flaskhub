from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_required, login_user, current_user, logout_user
import sqlite3
from datetime import datetime
from flask_bcrypt import Bcrypt

app= Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'thisIsSecret'
login_manager = LoginManager(app)
login_manager.login_view="login"

@app.route('/')
def home():
    return render_template('home.html')

def is_admin():
    # return current_user.is_authenticated and current_user.email == "admin@mail.com"
    return current_user.is_authenticated

@app.route('/login')
def login():
    return render_template('login.html')
    
class User(UserMixin):
    def __init__(self,id,email,password):
        self.id = id
        self.email = email
        self.password = password
        self.authenticated = False
        def is_active(self):
            return self.is_active()
        def is_anonymous(self):
            return False
        def is_authenticated(self):
            return self.authenticated
        def is_active(self):
            return True
        def get_id(self):
            return self.id

@app.route("/login", methods=["POST"])
def login_post():
    if current_user.is_authenticated:
        print("authenticated kid")
        return redirect(url_for('home'))
    con=sqlite3.connect("login.db")
    curs = con.cursor()
    email = request.form["email"]
    curs.execute("SELECT * FROM login where email = (?)", [email])
    row=curs.fetchone()
    if row==None:
        flash('please try logging in again')
        return render_template('login.html')
    user = list(row)
    liUser = User(int(user[0]),user[3],user[4])
    password = request.form['password']
    
    print(f"Stored password hash: {row[2]}")
    print(f"Hash length: {len(row[2]) if row[2] else 0}")
    
    match = bcrypt.check_password_hash(liUser.password,password)
    if match and email==liUser.email:
        login_user(liUser,remember=request.form.get('remember'))
        redirect(url_for('home'))
    else:
        flash('Please try logging in again')
        return render_template ('login.html')
    return redirect(url_for('home'))

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('login.db')
    curs=conn.cursor()
    curs.execute("SELECT * from login where user_id = (?)", [user_id])
    liUser = curs.fetchone()
    if liUser is None:
        return None
    else:
        return User(int(liUser[0]),liUser[1],liUser[2])
    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/register', methods=['POST'])
def register_post():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    email = request.form['email']
    fname = request.form['fname']
    sname = request.form['sname']
    password = request.form['password']

    hashedPassword = bcrypt.generate_password_hash(password)

    login_conn = sqlite3.connect("login.db")
    login_cursor = login_conn.cursor()

    login_cursor.execute("SELECT * FROM login WHERE email = ?", (email,))
    existing_user = login_cursor.fetchone()

    if existing_user:
        login_conn.close()
        flash('Email already registered.')
        return render_template('register.html')

    login_cursor.execute(
        "INSERT INTO login (firstName, secondName, email, password) VALUES (?, ?, ?, ?)",
        (fname, sname, email, hashedPassword)
    )
    login_conn.commit()
    login_conn.close()

    bike_conn = sqlite3.connect("bike_rental.db")
    bike_cursor = bike_conn.cursor()

    bike_cursor.execute("""
        INSERT INTO Staff (FirstName, LastName, Email, Role)
        VALUES (?, ?, ?, ?)
    """, (
        fname,
        sname,
        email,
        "Manager"
    ))

    bike_conn.commit()
    bike_conn.close()

    flash("Registration successful! Please log in.")
    return redirect(url_for('login'))


@app.route("/rental")
@login_required
def rental():

    conn = sqlite3.connect("bike_rental.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT BikeID, Model, BatteryLevel 
        FROM Bikes 
        WHERE Status = 'Available'
    """)
    bikes = cursor.fetchall()

    conn.close()

    today = datetime.today().strftime("%Y-%m-%d")

    return render_template("rental.html", bikes=bikes, today=today)


@app.route("/rental", methods=["POST"])
@login_required
def rental_post():

    start_date = request.form["start_date"]
    return_date = request.form["return_date"]
    bike_id = request.form["bike_id"]
    customer_email = request.form["customer_email"]

    if not start_date or not return_date:
        flash("Please select both dates.")
        return redirect(url_for("rental"))

    today = datetime.today().date()
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    return_date_obj = datetime.strptime(return_date, "%Y-%m-%d").date()

    if start_date_obj < today:
        flash("You cannot rent a bike in the past.")
        return redirect(url_for("rental"))

    if return_date_obj < today:
        flash("Return date cannot be in the past.")
        return redirect(url_for("rental"))

    if return_date_obj < start_date_obj:
        flash("Return date must be after start date.")
        return redirect(url_for("rental"))

    conn = sqlite3.connect("bike_rental.db")
    cursor = conn.cursor()

    cursor.execute("SELECT Status FROM Bikes WHERE BikeID = ?", (bike_id,))
    bike = cursor.fetchone()

    if bike is None:
        flash("Bike does not exist.")
        conn.close()
        return redirect(url_for("rental"))

    if bike[0] != "Available":
        flash("Bike is not available.")
        conn.close()
        return redirect(url_for("rental"))

    cursor.execute("""
        SELECT * FROM Rentals
        WHERE BikeID = ?
        AND (
            RentalDate <= ? AND ReturnDate >= ?
        )
    """, (bike_id, return_date, start_date))

    conflict = cursor.fetchone()

    if conflict:
        flash("Bike is already booked for those dates.")
        conn.close()
        return redirect(url_for("rental"))

    cursor.execute("SELECT CustomerID FROM Customers WHERE Email = ?", (customer_email,))
    customer = cursor.fetchone()

    customer_id = customer[0]

    if customer is None:
        flash("Customer record not found.")
        conn.close()
        return redirect(url_for("rental"))

    cursor.execute("""
        INSERT INTO Rentals (CustomerID, BikeID, RentalDate, ReturnDate)
        VALUES (?, ?, ?, ?)
    """, (customer_id, bike_id, start_date, return_date))

    cursor.execute("""
        UPDATE Bikes
        SET Status = 'Rented'
        WHERE BikeID = ?
    """, (bike_id,))

    conn.commit()
    conn.close()

    flash("Bike rented successfully!")
    return redirect(url_for("home"))

app.debug=True
app.run()