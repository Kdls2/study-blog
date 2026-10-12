import os
import re
import sqlite3
import secrets
from functools import wraps
from urllib.parse import urlsplit
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
    g
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Security & App Configuration
def resolve_database_path():
    if "DATABASE_PATH" in os.environ and os.environ["DATABASE_PATH"]:
        return os.environ["DATABASE_PATH"]

    is_serverless = bool(
        os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
        or os.environ.get("NETLIFY")
        or os.environ.get("LAMBDA_TASK_ROOT")
    )

    if is_serverless:
        tmp_db = "/tmp/study_blog.db"
        if not os.path.exists(tmp_db):
            base_db = os.path.join(app.root_path, "study_blog.db")
            if os.path.exists(base_db):
                import shutil
                try:
                    shutil.copyfile(base_db, tmp_db)
                except Exception:
                    pass
            if not os.path.exists(tmp_db):
                from init_db import init_db
                try:
                    init_db(tmp_db)
                except Exception as e:
                    print(f"Warning: Failed to init db in /tmp: {e}")
        return tmp_db

    return os.path.join(app.root_path, "study_blog.db")


def resolve_secret_key():
    """Load SECRET_KEY from environment, or generate and persist a strong 32-byte key."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    key_file = os.path.join(app.root_path, ".secret_key")
    if os.path.exists(key_file):
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception:
            pass
    # Generate cryptographically secure random key
    new_key = secrets.token_hex(32)
    try:
        with open(key_file, "w", encoding="utf-8") as f:
            f.write(new_key)
    except Exception:
        pass
    return new_key


app.config.update(
    SECRET_KEY=resolve_secret_key(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,  # บังคับส่งคุกกี้ผ่าน HTTPS เท่านั้น
)

csrf = CSRFProtect(app)


# ---------------------------------------------------------
# Security Helpers (Open Redirect Prevention)
# ---------------------------------------------------------
def is_safe_url(target):
    """Check if target URL is a safe relative path within this application."""
    if not target:
        return False
    parsed = urlsplit(target)
    # Must have no scheme and no network location (domain)
    if parsed.scheme != "" or parsed.netloc != "":
        return False
    # Must start with single slash, not protocol-relative (//) and no backslash
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        return False
    return True


def safe_next(target, default="index"):
    """Redirect to safe target URL or fallback to default endpoint."""
    if is_safe_url(target):
        return target
    return url_for(default)


# ---------------------------------------------------------
# Database helpers
# ---------------------------------------------------------
def get_db():
    if "db" not in g:
        db_path = app.config.get("DATABASE") or resolve_database_path()
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.execute("PRAGMA foreign_keys = ON;")
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


# ---------------------------------------------------------
# Auth Decorators, Context & Security Middleware
# ---------------------------------------------------------
@app.before_request
def load_logged_in_user():
    """Load user identity and role directly from database on each request.
    Prevents privilege escalation from client-side cookie tampering."""
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        g.user = db.execute(
            "SELECT id, username, email, role FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if g.user is None:
            session.clear()


@app.after_request
def add_security_headers(response):
    """Attach defense-in-depth security headers to protect against Clickjacking,
    XSS, MIME-sniffing, and downgrade attacks."""
    # 5. Clickjacking & Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    # 6. HTTP Strict Transport Security (HSTS)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # 7. MIME type sniffing prevention
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Additional hardening
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # 8. Suppress server headers
    response.headers.pop("Server", None)
    response.headers.pop("X-Powered-By", None)
    response.headers.pop("X-Render-Origin-Server", None)
    return response


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not getattr(g, "user", None):
            flash("กรุณาเข้าสู่ระบบก่อนทำรายการ", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not getattr(g, "user", None):
            flash("กรุณาเข้าสู่ระบบก่อนทำรายการ", "warning")
            return redirect(url_for("login", next=request.path))
        if g.user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_current_user():
    if getattr(g, "user", None):
        return {
            "current_user": {
                "id": g.user["id"],
                "username": g.user["username"],
                "role": g.user["role"]
            }
        }
    return {"current_user": None}


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------
# Routes: Public & Auth
# ---------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    posts = db.execute(
        """
        SELECT p.id, p.title, p.content, p.created_at, p.updated_at, p.user_id,
               u.username AS author_name,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        """
    ).fetchall()
    return render_template("posts/list.html", posts=posts)


@app.route("/register", methods=["GET", "POST"])
def register():
    if getattr(g, "user", None):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not username:
            errors.append("กรุณากรอกชื่อผู้ใช้")
        elif len(username) < 3 or len(username) > 30:
            errors.append("ชื่อผู้ใช้ต้องมีความยาว 3 - 30 ตัวอักษร")

        if not email:
            errors.append("กรุณากรอกอีเมล")
        elif not EMAIL_REGEX.match(email):
            errors.append("รูปแบบอีเมลไม่ถูกต้อง")

        # 4. Strict Password Policy
        if not password:
            errors.append("กรุณากรอกรหัสผ่าน")
        elif len(password) < 8:
            errors.append("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
        elif len(password) > 128:
            errors.append("รหัสผ่านต้องมีความยาวไม่เกิน 128 ตัวอักษร")
        elif username and password.lower() == username.lower():
            errors.append("รหัสผ่านต้องไม่ตรงกับชื่อผู้ใช้")
        elif email and password.lower() == email.lower():
            errors.append("รหัสผ่านต้องไม่ตรงกับอีเมล")
        elif not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and re.search(r"\d", password)):
            errors.append("รหัสผ่านต้องประกอบด้วยตัวพิมพ์ใหญ่ ตัวพิมพ์เล็ก และตัวเลขอย่างน้อยอย่างละ 1 ตัว")

        if password != confirm_password:
            errors.append("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")

        if not errors:
            db = get_db()
            user_by_name = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if user_by_name:
                errors.append("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว")

            user_by_email = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if user_by_email:
                errors.append("อีเมลนี้ถูกใช้งานแล้ว")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", username=username, email=email)

        # Hash password and create user with default role 'user'
        password_hash = generate_password_hash(password)
        db = get_db()
        db.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, 'user')",
            (username, email, password_hash)
        )
        db.commit()

        flash("สมัครสมาชิกสำเร็จเรียบร้อย กรุณาเข้าสู่ระบบ", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if getattr(g, "user", None):
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            # 1. Store only user_id in session cookie (never store role or username client-side)
            session["user_id"] = user["id"]
            flash(f"ยินดีต้อนรับ {user['username']} เข้าสู่ระบบ", "success")

            # 3. Open Redirect Prevention
            return redirect(safe_next(request.args.get("next")))

        # Generic error message to prevent username enumeration
        flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "danger")

    return render_template("auth/login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("ออกจากระบบเรียบร้อยแล้ว", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------
# Routes: Posts & Comments
# ---------------------------------------------------------
@app.route("/my-posts")
@login_required
def my_posts():
    db = get_db()
    posts = db.execute(
        """
        SELECT p.id, p.title, p.content, p.created_at, p.updated_at,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count
        FROM posts p
        WHERE p.user_id = ?
        ORDER BY p.created_at DESC
        """,
        (g.user["id"],)
    ).fetchall()
    return render_template("posts/mine.html", posts=posts)


@app.route("/posts/new", methods=["GET", "POST"])
@login_required
def new_post():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        errors = []
        if not title:
            errors.append("กรุณากรอกหัวข้อโพสต์")
        elif len(title) > 100:
            errors.append("หัวข้อโพสต์ต้องมีความยาวไม่เกิน 100 ตัวอักษร")

        if not content:
            errors.append("กรุณากรอกเนื้อหาโพสต์")
        elif len(content) > 5000:
            errors.append("เนื้อหาโพสต์ต้องมีความยาวไม่เกิน 5,000 ตัวอักษร")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("posts/form.html", title=title, content=content, is_edit=False)

        db = get_db()
        cursor = db.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (?, ?, ?)",
            (g.user["id"], title, content)
        )
        db.commit()
        new_post_id = cursor.lastrowid
        flash("สร้างโพสต์เรียบร้อยแล้ว", "success")
        return redirect(url_for("post_detail", post_id=new_post_id))

    return render_template("posts/form.html", is_edit=False)


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    db = get_db()
    post = db.execute(
        """
        SELECT p.id, p.title, p.content, p.created_at, p.updated_at, p.user_id,
               u.username AS author_name, u.role AS author_role
        FROM posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.id = ?
        """,
        (post_id,)
    ).fetchone()

    if post is None:
        abort(404)

    comments = db.execute(
        """
        SELECT c.id, c.content, c.created_at, c.user_id,
               u.username AS author_name, u.role AS author_role
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.post_id = ?
        ORDER BY c.created_at ASC
        """,
        (post_id,)
    ).fetchall()

    return render_template("posts/detail.html", post=post, comments=comments)


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)

    # Requirement 3 & Least Privilege: Only the owner can edit the post!
    if post["user_id"] != g.user["id"]:
        abort(403)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()

        errors = []
        if not title:
            errors.append("กรุณากรอกหัวข้อโพสต์")
        elif len(title) > 100:
            errors.append("หัวข้อโพสต์ต้องมีความยาวไม่เกิน 100 ตัวอักษร")

        if not content:
            errors.append("กรุณากรอกเนื้อหาโพสต์")
        elif len(content) > 5000:
            errors.append("เนื้อหาโพสต์ต้องมีความยาวไม่เกิน 5,000 ตัวอักษร")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("posts/form.html", post=post, title=title, content=content, is_edit=True)

        db.execute(
            """
            UPDATE posts
            SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (title, content, post_id, g.user["id"])
        )
        db.commit()
        flash("แก้ไขโพสต์เรียบร้อยแล้ว", "success")
        return redirect(url_for("post_detail", post_id=post_id))

    return render_template("posts/form.html", post=post, title=post["title"], content=post["content"], is_edit=True)


@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)

    # Owner or Admin can delete
    if post["user_id"] != g.user["id"] and g.user["role"] != "admin":
        abort(403)

    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    flash("ลบโพสต์เรียบร้อยแล้ว", "info")

    next_page = request.form.get("next")
    if is_safe_url(next_page):
        return redirect(next_page)

    if g.user["role"] == "admin" and request.referrer and "admin" in request.referrer:
        return redirect(url_for("admin_posts"))
    return redirect(url_for("index"))


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def add_comment(post_id):
    db = get_db()
    post = db.execute("SELECT id FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)

    content = request.form.get("content", "").strip()
    if not content:
        flash("กรุณากรอกข้อความความคิดเห็น", "danger")
    elif len(content) > 500:
        flash("ความคิดเห็นต้องมีความยาวไม่เกิน 500 ตัวอักษร", "danger")
    else:
        db.execute(
            "INSERT INTO comments (post_id, user_id, content) VALUES (?, ?, ?)",
            (post_id, g.user["id"], content)
        )
        db.commit()
        flash("แสดงความคิดเห็นเรียบร้อยแล้ว", "success")

    # PRG pattern
    return redirect(url_for("post_detail", post_id=post_id))


@app.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    db = get_db()
    comment = db.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if comment is None:
        abort(404)

    # Owner or Admin can delete
    if comment["user_id"] != g.user["id"] and g.user["role"] != "admin":
        abort(403)

    post_id = comment["post_id"]
    db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    db.commit()
    flash("ลบความคิดเห็นเรียบร้อยแล้ว", "info")
    return redirect(url_for("post_detail", post_id=post_id))


# ---------------------------------------------------------
# Routes: Admin Panel
# ---------------------------------------------------------
@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    post_count = db.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    comment_count = db.execute("SELECT COUNT(*) FROM comments").fetchone()[0]

    recent_users = db.execute(
        "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 5"
    ).fetchall()

    recent_posts = db.execute(
        """
        SELECT p.id, p.title, p.created_at, u.username AS author_name
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        LIMIT 5
        """
    ).fetchall()

    return render_template(
        "admin/dashboard.html",
        user_count=user_count,
        post_count=post_count,
        comment_count=comment_count,
        recent_users=recent_users,
        recent_posts=recent_posts
    )


@app.route("/admin/users")
@admin_required
def admin_users():
    db = get_db()
    users = db.execute(
        """
        SELECT u.id, u.username, u.email, u.role, u.created_at,
               (SELECT COUNT(*) FROM posts p WHERE p.user_id = u.id) AS post_count,
               (SELECT COUNT(*) FROM comments c WHERE c.user_id = u.id) AS comment_count
        FROM users u
        ORDER BY u.created_at DESC
        """
    ).fetchall()
    return render_template("admin/users.html", users=users)


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_change_role(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        abort(404)

    # Admin cannot change their own role!
    if user["id"] == g.user["id"]:
        flash("ไม่สามารถแก้ไขบทบาทของตัวเองได้ เพื่อป้องกันระบบขาด Admin", "danger")
        return redirect(url_for("admin_users"))

    new_role = request.form.get("role", "").strip()
    if new_role not in ["user", "admin"]:
        flash("บทบาทที่เลือกไม่ถูกต้อง", "danger")
        return redirect(url_for("admin_users"))

    db.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    db.commit()
    flash(f"เปลี่ยนบทบาทของ '{user['username']}' เป็น '{new_role}' เรียบร้อยแล้ว", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        abort(404)

    # Admin cannot delete their own account!
    if user["id"] == g.user["id"]:
        flash("ไม่สามารถลบบัญชีของตัวเองได้", "danger")
        return redirect(url_for("admin_users"))

    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash(f"ลบบัญชีผู้ใช้ '{user['username']}' เรียบร้อยแล้ว", "info")
    return redirect(url_for("admin_users"))


@app.route("/admin/posts")
@admin_required
def admin_posts():
    db = get_db()
    posts = db.execute(
        """
        SELECT p.id, p.title, p.created_at, p.updated_at, p.user_id,
               u.username AS author_name,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count
        FROM posts p
        JOIN users u ON p.user_id = u.id
        ORDER BY p.created_at DESC
        """
    ).fetchall()
    return render_template("admin/posts.html", posts=posts)


# ---------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(400)
def bad_request(e):
    # Commonly triggered by CSRF token missing or expired
    return render_template(
        "errors/404.html",
        custom_title="400 Bad Request / CSRF Token ไม่ถูกต้อง",
        custom_message="คำขอไม่ถูกต้อง หรือ CSRF Token หมดอายุ กรุณาลองใหม่อีกครั้ง"
    ), 400


# ---------------------------------------------------------
# WSGI Middleware to Strip Server Disclosure Headers
# ---------------------------------------------------------
class StripServerHeaderMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        def custom_start_response(status, response_headers, exc_info=None):
            filtered = [
                (k, v) for k, v in response_headers
                if k.lower() not in ("server", "x-render-origin-server", "x-powered-by")
            ]
            return start_response(status, filtered, exc_info)
        return self.wsgi_app(environ, custom_start_response)


app.wsgi_app = StripServerHeaderMiddleware(app.wsgi_app)

if __name__ == "__main__":
    app.run(debug=False)
