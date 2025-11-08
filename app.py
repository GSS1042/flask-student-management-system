from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "dev-secret"

# SQLite DB (file will be created next to app.py)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    roll = db.Column(db.String(50), nullable=False, unique=True)
    course = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), nullable=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "roll": self.roll, "course": self.course, "email": self.email}

# remove @app.before_first_request decorator usage and call create_tables() at runtime
def create_tables():
    # Ensure create_all runs with an application context
    with app.app_context():
        db.create_all()

@app.route("/")
def home():
    q = request.args.get('q', '').strip()
    if q:
        qlow = f"%{q.lower()}%"
        students = Student.query.filter(
            db.or_(
                db.func.lower(Student.name).like(qlow),
                db.func.lower(Student.roll).like(qlow),
                db.func.lower(Student.course).like(qlow),
                db.func.lower(Student.email).like(qlow),
            )
        ).all()
    else:
        students = Student.query.all()
    # convert to list of dicts for templates that expect dict-style access
    students_list = [s.to_dict() for s in students]
    return render_template("index.html", students=students_list, q=q, active='home')

@app.route("/about")
def about():
    return render_template("about.html", active='about')

@app.route("/contact", methods=["GET", "POST"])
def contact():
    # keep simple in-memory contact handling
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('All contact fields are required.', 'danger')
            return render_template("contact.html", active='contact')
        flash('Thank you for your message — we will get back to you shortly.', 'success')
        return redirect(url_for('contact'))
    return render_template("contact.html", active='contact')

@app.route('/students/new', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll = request.form.get('roll', '').strip()
        course = request.form.get('course', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not roll:
            flash('Name and roll are required.', 'danger')
            return render_template('add_student.html', active='add', form=request.form)

        # check unique roll
        if Student.query.filter_by(roll=roll).first():
            flash('A student with this roll already exists.', 'danger')
            return render_template('add_student.html', active='add', form=request.form)

        s = Student(name=name, roll=roll, course=course, email=email)
        db.session.add(s)
        db.session.commit()
        flash('Student added.', 'success')
        return redirect(url_for('home'))

    return render_template('add_student.html', active='add')

@app.route('/students/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll = request.form.get('roll', '').strip()
        course = request.form.get('course', '').strip()
        email = request.form.get('email', '').strip()

        if not name or not roll:
            flash('Name and roll are required.', 'danger')
            return render_template('edit_student.html', active='home', student=student.to_dict())

        # check roll uniqueness (allow same as current)
        other = Student.query.filter_by(roll=roll).first()
        if other and other.id != student.id:
            flash('Another student already uses this roll.', 'danger')
            return render_template('edit_student.html', active='home', student=student.to_dict())

        student.name = name
        student.roll = roll
        student.course = course
        student.email = email
        db.session.commit()
        flash('Student updated.', 'success')
        return redirect(url_for('home'))

    return render_template('edit_student.html', active='home', student=student.to_dict())

@app.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    try:
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error deleting student. Please try again.', 'danger')
    return redirect(url_for('home'))

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
