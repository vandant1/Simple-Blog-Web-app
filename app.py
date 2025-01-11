from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
@app.route('/')
def index():
    posts = BlogPost.query.order_by(BlogPost.date_posted.desc()).all()  # Fetch all posts in descending order
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()  # Commit to save the new user
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    return render_template('login.html', action="Register")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Login failed, check your credentials.", "danger")
    return render_template('login.html', action="Login")

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        flash("Please log in to create a post.", "warning")
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post = BlogPost(title=title, content=content, author_id=session['user_id'])
        db.session.add(post)
        db.session.commit()  # Commit to save the new post
        flash("Post created successfully!", "success")
        return redirect(url_for('index'))
    return render_template('form.html', action="Create New Post")

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if 'user_id' not in session or post.author_id != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()  # Commit to save the edited post
        flash("Post updated successfully!", "success")
        return redirect(url_for('view_post', post_id=post.id))
    return render_template('form.html', post=post, action="Edit Post")

@app.route('/delete/<int:post_id>')
def delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if 'user_id' not in session or post.author_id != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()  # Commit to delete the post
    flash("Post deleted successfully!", "success")
    return redirect(url_for('index'))

# Initialize the database and create tables if they don’t exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
