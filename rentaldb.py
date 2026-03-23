import sqlite3

conn = sqlite3.connect("bike_rental.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

cursor.execute("""
CREATE TABLE Customers (
    CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    MembershipType TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE Staff (
    StaffID INTEGER PRIMARY KEY AUTOINCREMENT,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE,
    Role TEXT NOT NULL CHECK(Role IN ('Manager', 'Clerk', 'Mechanic'))
)
""")

cursor.execute("""
CREATE TABLE Bikes (
    BikeID INTEGER PRIMARY KEY AUTOINCREMENT,
    Model TEXT NOT NULL,
    BatteryLevel INTEGER CHECK(BatteryLevel BETWEEN 0 AND 100),
    Status TEXT NOT NULL CHECK(Status IN ('Available', 'Rented', 'Repair'))
)
""")

cursor.execute("""
CREATE TABLE Rentals (
    RentalID INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerID INTEGER NOT NULL,
    BikeID INTEGER NOT NULL,
    RentalDate TEXT NOT NULL,
    ReturnDate TEXT NOT NULL,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (BikeID) REFERENCES Bikes(BikeID)
)
""")

# samples

cursor.execute("""
INSERT INTO Bikes (Model, BatteryLevel, Status)
VALUES ('Whiteo Bike', 85, 'Available')
""")

cursor.execute("""
INSERT INTO Bikes (Model, BatteryLevel, Status)
VALUES ('Burger Bike', 90, 'Available')
""")

cursor.execute("""
INSERT INTO Customers (CustomerID, FirstName, LastName, Email, MembershipType)
VALUES (1, 'Evan', 'Burger', 'evan@burger.com', 'Standard')
""")

conn.commit()
conn.close()