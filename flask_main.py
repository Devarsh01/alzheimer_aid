import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///alzheimers_caregiver.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24).hex())
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_name = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/tasks', methods=['GET', 'POST'])
def tasks():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    if request.method == 'POST':
        task_name = request.form['task_name']
        new_task = Task(user_id=user_id, task_name=task_name)
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for('tasks'))

    user_tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('tasks.html', tasks=user_tasks)


@app.route('/task/delete/<int:task_id>')
def delete_task(task_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully.', 'info')

    return redirect(url_for('tasks'))


@app.route('/task/complete/<int:task_id>')
def complete_task(task_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    task = Task.query.get(task_id)
    if task and task.user_id == session['user_id']:
        task.completed = True
        db.session.commit()
        flash('Task marked as completed!', 'success')

    return redirect(url_for('tasks'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
