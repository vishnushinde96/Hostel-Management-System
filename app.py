import io
import os
import re
from datetime import date
from flask import session, make_response
import pandas as pd
from config import Config
from extensions import db, login_manager, migrate
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from models import Fee, Room, Student, User
from pdf_generator import generate_fee_receipt
from routes import main_bp
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from whatsapp_service import send_whatsapp_receipt


def verify_database_connection(app):
    with app.app_context():
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    verify_database_connection(app)

    # --- डेटाबेस टेबल्स आणि डिफॉल्ट Admin युझर ऑटो-क्रिएशन ---
    with app.app_context():
        db.create_all()

        existing_admin = User.query.filter_by(email="admin@gmail.com").first()
        if not existing_admin:
            hashed_password = generate_password_hash("admin123")
            admin_user = User(
                email="admin@gmail.com",
                password=hashed_password,
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created successfully!")

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(main_bp)

    # ब्राउझरला प्रत्येक पेजसाठी कॅश बंद करण्याचे आदेश
    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = (
            "no-cache, no-store, must-revalidate, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.context_processor
    def inject_globals():
        from datetime import datetime

        return {"current_year": datetime.now().year}

    @app.route("/")
    def index():
        return render_template("index.html")

    # --- Login Route (Fixed Password Hashing Check) ---
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = User.query.filter_by(email=email).first()

            # हॅश केलेला पासवर्ड किंवा प्लेन टेक्स्ट पासवर्ड दोन्ही सपोर्ट करेल
            if user and (
                check_password_hash(user.password, password)
                or user.password == password
            ):
                login_user(user)
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password", "danger")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        session.clear()

        response = make_response(redirect(url_for("index")))
        response.delete_cookie("session")
        response.headers["Cache-Control"] = (
            "no-cache, no-store, must-revalidate, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # --- Dashboard Route ---
    @app.route("/dashboard")
    @login_required
    def dashboard():
        total_students = Student.query.count()
        total_admins = User.query.count()
        total_rooms = Room.query.count()

        all_rooms = Room.query.all()
        available_rooms_count = 0
        for room in all_rooms:
            student_count = Student.query.filter_by(room_no=room.room_number).count()
            if student_count < 4:
                available_rooms_count += 1

        recent_students = Student.query.order_by(Student.id.desc()).limit(5).all()

        return render_template(
            "dashboard.html",
            total_students=total_students,
            total_admins=total_admins,
            total_rooms=total_rooms,
            available_rooms_count=available_rooms_count,
            recent_students=recent_students,
        )

    # --- Add Student Route ---
    @app.route("/add_student", methods=["GET", "POST"])
    @login_required
    def add_student():
        if request.method == "POST":
            room_no = request.form.get("room_no")
            name = request.form.get("name", "").strip()
            class_name = request.form.get("class_name")
            mobile_no = request.form.get("mobile_no", "").strip()
            aadhaar_no = request.form.get("aadhaar_no", "").strip()
            gender = request.form.get("gender")
            address = request.form.get("address")

            # 1. Name Validation
            if not re.match(r"^[a-zA-A-zA-Z\s]+$", name):
                flash(
                    "Name should contain letters only! Numbers are not allowed.",
                    "danger",
                )
                return redirect(url_for("add_student"))

            # 2. Mobile Number Validation
            if not re.match(r"^\d{10}$", mobile_no):
                flash("Mobile number must be exactly 10 digits!", "danger")
                return redirect(url_for("add_student"))

            existing_mobile = Student.query.filter_by(mobile_no=mobile_no).first()
            if existing_mobile:
                flash(
                    "This Mobile Number is already registered with another student!",
                    "danger",
                )
                return redirect(url_for("add_student"))

            # 3. Aadhaar Number Validation
            if not re.match(r"^\d{12}$", aadhaar_no):
                flash("Aadhaar number must be exactly 12 digits!", "danger")
                return redirect(url_for("add_student"))

            existing_aadhaar = Student.query.filter_by(aadhaar_no=aadhaar_no).first()
            if existing_aadhaar:
                flash(
                    "This Aadhaar Number is already registered with another student!",
                    "danger",
                )
                return redirect(url_for("add_student"))

            current_student_count = Student.query.filter_by(room_no=room_no).count()
            if current_student_count >= 4:
                flash(
                    "This room is already full (Max 4 students allowed)!",
                    "danger",
                )
                return redirect(url_for("add_student"))

            new_student = Student(
                room_no=room_no,
                name=name,
                class_name=class_name,
                mobile_no=mobile_no,
                aadhaar_no=aadhaar_no,
                gender=gender,
                address=address,
                date_added=date.today(),
            )
            db.session.add(new_student)
            db.session.commit()

            new_fee = Fee(
                student_id=new_student.id,
                duration="1 Month (01-01-2026 to 01-02-2026)",
                amount=1000.0,
                status="Pending",
            )
            db.session.add(new_fee)
            db.session.commit()

            flash("Student added successfully!", "success")
            return redirect(url_for("student_records"))

        all_rooms = Room.query.all()
        available_rooms = []
        for room in all_rooms:
            count = Student.query.filter_by(room_no=room.room_number).count()
            if count < 4:
                available_rooms.append(room)

        return render_template("add_student.html", rooms=available_rooms)

    # --- View All Students Route ---
    @app.route("/student_records")
    @login_required
    def student_records():
        students = Student.query.all()
        return render_template("student_records.html", students=students)

    # --- Update/Edit Student Route ---
    @app.route("/edit_student/<int:id>", methods=["GET", "POST"])
    @login_required
    def edit_student(id):
        student = Student.query.get_or_404(id)

        if request.method == "POST":
            room_no = request.form.get("room_no")
            name = request.form.get("name", "").strip()
            class_name = request.form.get("class_name")
            mobile_no = request.form.get("mobile_no", "").strip()
            aadhaar_no = request.form.get("aadhaar_no", "").strip()
            gender = request.form.get("gender")
            address = request.form.get("address")

            if not re.match(r"^[a-zA-A-zA-Z\s]+$", name):
                flash(
                    "Name should contain letters only! Numbers are not allowed.",
                    "danger",
                )
                return redirect(url_for("edit_student", id=id))

            if not re.match(r"^\d{10}$", mobile_no):
                flash("Mobile number must be exactly 10 digits!", "danger")
                return redirect(url_for("edit_student", id=id))

            existing_mobile = Student.query.filter(
                Student.mobile_no == mobile_no, Student.id != id
            ).first()
            if existing_mobile:
                flash(
                    "This Mobile Number is already registered with another student!",
                    "danger",
                )
                return redirect(url_for("edit_student", id=id))

            if not re.match(r"^\d{12}$", aadhaar_no):
                flash("Aadhaar number must be exactly 12 digits!", "danger")
                return redirect(url_for("edit_student", id=id))

            existing_aadhaar = Student.query.filter(
                Student.aadhaar_no == aadhaar_no, Student.id != id
            ).first()
            if existing_aadhaar:
                flash(
                    "This Aadhaar Number is already registered with another student!",
                    "danger",
                )
                return redirect(url_for("edit_student", id=id))

            if str(student.room_no) != str(room_no):
                current_student_count = Student.query.filter_by(room_no=room_no).count()
                if current_student_count >= 4:
                    flash(
                        "This room is already full (Max 4 students allowed)!",
                        "danger",
                    )
                    return redirect(url_for("edit_student", id=id))

            student.room_no = room_no
            student.name = name
            student.class_name = class_name
            student.mobile_no = mobile_no
            student.aadhaar_no = aadhaar_no
            student.gender = gender
            student.address = address

            db.session.commit()
            flash("Student updated successfully!", "success")
            return redirect(url_for("student_records"))

        all_rooms = Room.query.all()
        available_rooms = []
        for room in all_rooms:
            count = Student.query.filter_by(room_no=room.room_number).count()
            if count < 4 or str(room.room_number) == str(student.room_no):
                available_rooms.append(room)

        return render_template(
            "edit_student.html", student=student, rooms=available_rooms
        )

    # --- Delete Student Route ---
    @app.route("/delete_student/<int:id>", methods=["POST"])
    @login_required
    def delete_student(id):
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        flash("Student record deleted successfully!", "success")
        return redirect(url_for("student_records"))

    # --- Add Admin Route ---
    @app.route("/add_admin", methods=["GET", "POST"])
    @login_required
    def add_admin():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("This Email ID is already registered!", "danger")
                return redirect(url_for("add_admin"))

            # नवीन admin पासवर्डसुद्धा हॅश करून सेव्ह करा
            new_admin = User(email=email, password=generate_password_hash(password))

            db.session.add(new_admin)
            db.session.commit()

            flash("Admin added successfully!", "success")
            return redirect(url_for("all_admins"))

        return render_template("add_admin.html")

    # --- View All Admins Route ---
    @app.route("/all_admins")
    @login_required
    def all_admins():
        admins = User.query.all()
        return render_template("all_admins.html", admins=admins)

    # --- Delete Admin Route ---
    @app.route("/delete_admin/<int:id>", methods=["POST"])
    @login_required
    def delete_admin(id):
        if current_user.id == id:
            flash("You cannot delete your own account!", "danger")
            return redirect(url_for("all_admins"))

        admin = User.query.get_or_404(id)
        db.session.delete(admin)
        db.session.commit()
        flash("Admin deleted successfully!", "success")
        return redirect(url_for("all_admins"))

    # --- Rooms Routes ---
    @app.route("/rooms")
    @login_required
    def rooms():
        all_rooms = Room.query.all()
        return render_template("rooms.html", rooms=all_rooms)

    @app.route("/add_room", methods=["GET", "POST"])
    @login_required
    def add_room():
        if request.method == "POST":
            room_number = request.form.get("room_number")

            existing_room = Room.query.filter_by(room_number=room_number).first()
            if existing_room:
                flash("Room number already exists!", "danger")
                return redirect(url_for("add_room"))

            new_room = Room(room_number=room_number)
            db.session.add(new_room)
            db.session.commit()
            flash("Room added successfully!", "success")
            return redirect(url_for("rooms"))

        return render_template("add_room.html")

    # --- Delete Room Route ---
    @app.route("/delete_room/<int:id>", methods=["POST"])
    @login_required
    def delete_room(id):
        room = Room.query.get_or_404(id)
        students_in_room = Student.query.filter_by(room_no=room.room_number).count()

        if students_in_room > 0:
            flash(
                f"Room {room.room_number} cannot be deleted because"
                f" {students_in_room} student(s) are currently assigned to it!",
                "danger",
            )
            return redirect(url_for("rooms"))

        try:
            db.session.delete(room)
            db.session.commit()
            flash(f"Room {room.room_number} deleted successfully!", "success")
        except Exception:
            db.session.rollback()
            flash("Something went wrong while deleting the room.", "danger")

        return redirect(url_for("rooms"))

    # --- View Fees Route ---
    @app.route("/fees")
    @login_required
    def fees():
        all_students = Student.query.all()

        for student in all_students:
            fee_record = Fee.query.filter_by(student_id=student.id).first()
            if not fee_record:
                new_fee = Fee(
                    student_id=student.id,
                    duration="1 Month (01-01-2026 to 01-02-2026)",
                    amount=1000.0,
                    status="Pending",
                )
                db.session.add(new_fee)

        db.session.commit()
        all_fees = Fee.query.all()
        return render_template("fees.html", fees=all_fees)

    # --- Update Fees Route ---
    @app.route("/update_fees", methods=["GET", "POST"])
    @login_required
    def update_fees():
        show_popup = False
        fee = None
        mobile_no = request.args.get("mobile_no")

        if request.method == "POST":
            fee_id = request.form.get("fee_id")
            fee = Fee.query.get_or_404(fee_id)

            fee.duration = request.form.get("duration")
            fee.amount = float(request.form.get("amount", 1000))
            fee.status = request.form.get("status")

            db.session.commit()

            try:
                generate_fee_receipt(fee, fee.student)
            except Exception as e:
                print("PDF Generation Error:", e)

            try:
                pdf_url = url_for(
                    "static",
                    filename=f"receipts/receipt_{fee.id}.pdf",
                    _external=True,
                )
                send_whatsapp_receipt(
                    student_mobile=fee.student.mobile_no,
                    pdf_url=pdf_url,
                    student_name=fee.student.name,
                    amount=fee.amount,
                    status=fee.status,
                )
            except Exception as e:
                print("WhatsApp Error:", e)

            show_popup = True
            return render_template(
                "update_fees.html",
                fee=fee,
                searched_mobile=fee.student.mobile_no,
                show_popup=show_popup,
            )

        if mobile_no:
            student = Student.query.filter_by(mobile_no=mobile_no.strip()).first()
            if student:
                fee = Fee.query.filter_by(student_id=student.id).first()
                if not fee:
                    flash("Student found, but no Fee record exists!", "danger")
            else:
                flash("No student found with this Mobile Number!", "danger")

        return render_template(
            "update_fees.html",
            fee=fee,
            searched_mobile=mobile_no,
            show_popup=show_popup,
        )

    # --- Download PDF Receipt Route ---
    @app.route("/download_receipt/<int:fee_id>")
    @login_required
    def download_receipt(fee_id):
        fee = Fee.query.get_or_404(fee_id)
        pdf_path = generate_fee_receipt(fee, fee.student)

        if not os.path.exists(pdf_path):
            flash("Receipt file could not be generated!", "danger")
            return redirect(url_for("update_fees", mobile_no=fee.student.mobile_no))

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"Receipt_{fee.student.name}.pdf",
        )

    # --- Download Excel Route ---
    @app.route("/download_excel")
    @login_required
    def download_excel():
        students = Student.query.all()

        data = []
        for s in students:
            fee_duration = s.fee.duration if s.fee else "N/A"
            fee_amount = s.fee.amount if s.fee else 0.0
            fee_status = s.fee.status if s.fee else "N/A"

            data.append(
                {
                    "Room No": s.room_no,
                    "Name": s.name,
                    "Gender": s.gender,
                    "Class": s.class_name,
                    "Mobile No": s.mobile_no,
                    "Aadhaar No": s.aadhaar_no,
                    "Address": s.address,
                    "Date Added": getattr(s, "date_added", "N/A"),
                    "Duration": fee_duration,
                    "Amount": fee_amount,
                    "Status": fee_status,
                }
            )

        df = pd.DataFrame(data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Students")
        output.seek(0)

        return send_file(
            output,
            mimetype=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            download_name="Students_List.xlsx",
            as_attachment=True,
        )

    return app


if __name__ == "__main__":
    app = create_app()

    app.run(
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "True").lower() == "true",
    )
