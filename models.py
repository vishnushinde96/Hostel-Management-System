from datetime import date
from extensions import db
from flask_login import UserMixin


class User(db.Model, UserMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    room_no = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    mobile_no = db.Column(db.String(15), nullable=False)
    aadhaar_no = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    date_added = db.Column(db.Date, default=date.today)

    # 🔴 इथे cascade="all, delete-orphan" जोडले आहे
    fee = db.relationship(
        "Fee",
        backref="student",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Room(db.Model):
    __tablename__ = "room"

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), unique=True, nullable=False)


class Fee(db.Model):
    __tablename__ = "fees"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    duration = db.Column(db.String(100), default="1 Month (01-01-2026 to 01-02-2026)")
    amount = db.Column(db.Float, default=1000.0)
    status = db.Column(db.String(20), default="Pending")
