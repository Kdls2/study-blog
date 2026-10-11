# Study Blog — โปรเจกต์เว็บแอปพื้นฐานเพื่อการศึกษา

โปรเจกต์ตัวอย่างสำหรับฝึกพัฒนาเว็บแอปพลิเคชันที่มีระบบสมาชิก, การแบ่งสิทธิ์ผู้ใช้, การจัดการข้อมูลที่มีเจ้าของ และหน้าผู้ดูแลระบบ
เอกสารนี้อธิบาย **สิ่งที่ต้องทำ, แนวคิดเบื้องหลัง และวิธีตรวจสอบว่าทำถูกต้อง** โดยเน้นความรู้ระดับพื้นฐาน

> ⚠️ โปรเจกต์นี้ใช้เพื่อ **การเรียนรู้** เท่านั้น ก่อนนำไปใช้งานจริงต้องเสริมความปลอดภัยเพิ่มเติม (ดูหัวข้อ [ข้อจำกัดและสิ่งที่ควรต่อยอด](#12-ข้อจำกัดและสิ่งที่ควรต่อยอด))

---

## สารบัญ

1. [ภาพรวมและเป้าหมาย](#1-ภาพรวมและเป้าหมาย)
2. [ข้อกำหนดของโปรเจกต์ (Requirements)](#2-ข้อกำหนดของโปรเจกต์-requirements)
3. [เทคโนโลยีที่แนะนำ](#3-เทคโนโลยีที่แนะนำ)
4. [โครงสร้างโปรเจกต์](#4-โครงสร้างโปรเจกต์)
5. [การออกแบบฐานข้อมูล](#5-การออกแบบฐานข้อมูล)
6. [รายละเอียดแต่ละฟีเจอร์](#6-รายละเอียดแต่ละฟีเจอร์)
7. [ตารางสิทธิ์ (Permission Matrix)](#7-ตารางสิทธิ์-permission-matrix)
8. [รายการ Routes](#8-รายการ-routes)
9. [พื้นฐานด้านความปลอดภัยที่ต้องรู้](#9-พื้นฐานด้านความปลอดภัยที่ต้องรู้)
10. [วิธีติดตั้งและรันโปรเจกต์](#10-วิธีติดตั้งและรันโปรเจกต์)
11. [แนวทางทดสอบ](#11-แนวทางทดสอบ)
12. [ข้อจำกัดและสิ่งที่ควรต่อยอด](#12-ข้อจำกัดและสิ่งที่ควรต่อยอด)
13. [คำศัพท์ที่ควรรู้](#13-คำศัพท์ที่ควรรู้)

---

## 1. ภาพรวมและเป้าหมาย

**Study Blog** คือเว็บบล็อกขนาดเล็ก ที่ผู้ใช้สามารถสมัครสมาชิก เขียนโพสต์ และแสดงความคิดเห็นได้
มีผู้ดูแลระบบ (admin) คอยจัดการผู้ใช้และตรวจสอบเนื้อหา

### สิ่งที่จะได้เรียนรู้

| หัวข้อ | สิ่งที่ได้ฝึก |
|---|---|
| Authentication | สมัครสมาชิก, เข้าสู่ระบบ, ออกจากระบบ, จัดการ session |
| Password Security | การทำ password hashing + salt |
| Authorization | การแบ่งบทบาท (role) และตรวจสิทธิ์ที่ฝั่งเซิร์ฟเวอร์ |
| CRUD | สร้าง/อ่าน/แก้ไข/ลบ ข้อมูล พร้อมระบบเจ้าของข้อมูล (ownership) |
| Form & Database | รับข้อมูลจากฟอร์ม ตรวจสอบ บันทึกลง DB และแสดงผลกลับ |
| Admin Panel | หน้าจัดการระบบที่เข้าได้เฉพาะ admin |
| Web Security พื้นฐาน | SQL Injection, XSS, CSRF, IDOR |

### ขอบเขต (Scope)

- ✅ ทำ: ฟีเจอร์ตามข้อกำหนด 5 ข้อ, UI ง่าย ๆ, ฐานข้อมูลไฟล์เดียว
- ❌ ไม่ทำ (เพื่อให้เรียบง่าย): อัปโหลดรูป, ยืนยันอีเมล, ลืมรหัสผ่าน, OAuth/Social login, REST API, deploy จริง

---

## 2. ข้อกำหนดของโปรเจกต์ (Requirements)

| # | ข้อกำหนด | วิธีทำในโปรเจกต์นี้ |
|---|---|---|
| 1 | สมัครสมาชิกและเข้าสู่ระบบ พร้อมเก็บรหัสผ่านด้วย password hashing ที่เหมาะสม | หน้า Register / Login, เก็บ `password_hash` (ไม่เก็บรหัสผ่านจริง) |
| 2 | ผู้ใช้อย่างน้อย 2 บทบาท ที่มีสิทธิ์ต่างกันชัดเจน | บทบาท `user` และ `admin` |
| 3 | CRUD อย่างน้อย 1 ชุด ที่ข้อมูลมี "เจ้าของ" (ผู้ใช้ A แก้/ลบข้อมูลของผู้ใช้ B ไม่ได้) | จัดการ **โพสต์ (posts)** — เจ้าของคือผู้เขียน |
| 4 | ฟอร์มรับข้อมูลอย่างน้อย 2 ฟอร์ม ที่บันทึกลงฐานข้อมูลและแสดงผลกลับ | ฟอร์ม **เขียน/แก้ไขโพสต์** และฟอร์ม **แสดงความคิดเห็น** |
| 5 | หน้าผู้ดูแลระบบอย่างน้อย 1 หน้า | หน้า **Admin Dashboard** (จัดการผู้ใช้ + ดูโพสต์ทั้งหมด) |

> 💡 ฟอร์มสมัครสมาชิกและเข้าสู่ระบบก็เป็นฟอร์มเช่นกัน แต่เพื่อความชัดเจน ให้ถือว่า "2 ฟอร์มของข้อ 4" คือฟอร์มโพสต์และฟอร์มความคิดเห็น

---

## 3. เทคโนโลยีที่แนะนำ

ตัวอย่างในเอกสารนี้ใช้ชุดเครื่องมือที่ติดตั้งง่ายและเหมาะกับผู้เริ่มต้น:

| ส่วน | เครื่องมือ | เหตุผล |
|---|---|---|
| ภาษา / Framework | Python 3.10+ และ **Flask** | โค้ดอ่านง่าย โครงสร้างเล็ก |
| ฐานข้อมูล | **SQLite** | ไม่ต้องติดตั้งเซิร์ฟเวอร์ เป็นไฟล์เดียว |
| Template | **Jinja2** (มากับ Flask) | escape ข้อมูลให้อัตโนมัติ ช่วยกัน XSS |
| Password Hashing | `werkzeug.security` | มี salt ในตัว ใช้งานง่าย |
| CSRF Protection | **Flask-WTF** (`CSRFProtect`) | ใส่ token ในฟอร์ม |
| หน้าตา (UI) | HTML + CSS ธรรมดา หรือ Bootstrap | ไม่ซับซ้อน |

### ใช้ภาษา/Framework อื่นได้ไหม?

ได้ แนวคิดเหมือนกันทั้งหมด เพียงเปลี่ยนเครื่องมือ:

| แนวคิด | Python (Flask) | Node.js (Express) | PHP |
|---|---|---|---|
| Password hashing | `werkzeug.security` | `bcrypt` / `argon2` | `password_hash()` |
| Session | `flask.session` | `express-session` | `$_SESSION` |
| Query ปลอดภัย | placeholder `?` | placeholder `?` / `$1` | PDO prepared statements |
| CSRF | Flask-WTF | `csurf` หรือ token เอง | token เอง / Laravel |
| Template escape | Jinja2 (อัตโนมัติ) | EJS `<%= %>` | `htmlspecialchars()` |

---

## 4. โครงสร้างโปรเจกต์

```
study-blog/
├── app.py                 # จุดเริ่มต้นของแอป + routes
├── init_db.py             # สร้างตารางและ admin เริ่มต้น
├── schema.sql             # คำสั่งสร้างตาราง
├── requirements.txt       # รายการไลบรารี
├── study_blog.db          # ไฟล์ฐานข้อมูล (สร้างอัตโนมัติ ห้าม commit)
├── .gitignore
├── templates/
│   ├── base.html          # layout หลัก (navbar, flash message)
│   ├── auth/
│   │   ├── register.html
│   │   └── login.html
│   ├── posts/
│   │   ├── list.html      # รายการโพสต์ทั้งหมด
│   │   ├── detail.html    # โพสต์ + ความคิดเห็น + ฟอร์มคอมเมนต์
│   │   ├── form.html      # ฟอร์มสร้าง/แก้ไขโพสต์
│   │   └── mine.html      # โพสต์ของฉัน
│   ├── admin/
│   │   ├── dashboard.html # สรุปจำนวนผู้ใช้/โพสต์
│   │   ├── users.html     # จัดการผู้ใช้
│   │   └── posts.html     # ดู/ลบโพสต์ทั้งหมด
│   └── errors/
│       ├── 403.html
│       └── 404.html
└── static/
    └── css/style.css
```

**.gitignore** ที่ควรมี:

```
venv/
__pycache__/
*.db
.env
```

---

## 5. การออกแบบฐานข้อมูล

### ER Diagram (แบบย่อ)

```
users 1 ───── N posts 1 ───── N comments
  │                                 ▲
  └─────────────────────────────────┘
          (ผู้ใช้ 1 คนเขียนได้หลายความคิดเห็น)
```

### ตาราง `users`

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| `id` | INTEGER PK | auto increment |
| `username` | TEXT UNIQUE NOT NULL | ห้ามซ้ำ |
| `email` | TEXT UNIQUE NOT NULL | ห้ามซ้ำ |
| `password_hash` | TEXT NOT NULL | **ห้ามเก็บรหัสผ่านจริง** |
| `role` | TEXT NOT NULL DEFAULT `'user'` | `'user'` หรือ `'admin'` |
| `created_at` | TEXT | เวลาที่สมัคร |

### ตาราง `posts`

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | INTEGER FK → `users.id` | **เจ้าของโพสต์** |
| `title` | TEXT NOT NULL | |
| `content` | TEXT NOT NULL | |
| `created_at` | TEXT | |
| `updated_at` | TEXT | |

### ตาราง `comments`

| คอลัมน์ | ชนิด | หมายเหตุ |
|---|---|---|
| `id` | INTEGER PK | |
| `post_id` | INTEGER FK → `posts.id` | ลบโพสต์แล้วลบคอมเมนต์ตาม (`ON DELETE CASCADE`) |
| `user_id` | INTEGER FK → `users.id` | **เจ้าของความคิดเห็น** |
| `content` | TEXT NOT NULL | |
| `created_at` | TEXT | |

### ตัวอย่าง `schema.sql`

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

> 💡 SQLite ต้องสั่ง `PRAGMA foreign_keys = ON;` **ทุกครั้งที่เชื่อมต่อ** จึงจะบังคับใช้ foreign key และ `ON DELETE CASCADE`

---

## 6. รายละเอียดแต่ละฟีเจอร์

### 6.1 สมัครสมาชิกและเข้าสู่ระบบ (Requirement 1)

**ฟอร์มสมัครสมาชิก** — ช่อง: `username`, `email`, `password`, `confirm_password`

ขั้นตอนฝั่งเซิร์ฟเวอร์:

1. ตรวจว่าทุกช่องไม่ว่าง และรูปแบบ email ถูกต้อง
2. ตรวจรหัสผ่านอย่างน้อย 8 ตัวอักษร และ `password == confirm_password`
3. ตรวจว่า `username` / `email` ยังไม่ถูกใช้
4. **Hash** รหัสผ่านก่อนบันทึก
5. บันทึกผู้ใช้ใหม่ด้วย `role = 'user'` (กำหนดเองจากฝั่งเซิร์ฟเวอร์ ไม่รับจากฟอร์ม)
6. redirect ไปหน้า Login พร้อมข้อความแจ้งสำเร็จ

**ฟอร์มเข้าสู่ระบบ** — ช่อง: `username`, `password`

1. ค้นหาผู้ใช้จาก `username`
2. ตรวจรหัสผ่านด้วย `check_password_hash`
3. ถ้าถูกต้อง → เก็บ `user_id` และ `role` ใน session แล้ว redirect
4. ถ้าผิด → แสดงข้อความ **กลาง ๆ** เช่น "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง" (อย่าบอกว่าผิดที่ช่องไหน เพราะช่วยให้ผู้โจมตีเดา username ได้)

**ออกจากระบบ** — ล้าง session (`session.clear()`) ผ่านคำขอแบบ `POST`

#### ตัวอย่างโค้ด: Password Hashing

```python
from werkzeug.security import generate_password_hash, check_password_hash

# ตอนสมัคร: แปลงรหัสผ่านเป็น hash (มี salt สุ่มรวมอยู่ในผลลัพธ์แล้ว)
password_hash = generate_password_hash(password)
db.execute(
    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
    (username, email, password_hash),
)

# ตอนล็อกอิน: เทียบรหัสผ่านที่กรอกกับ hash ที่เก็บไว้
user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
if user and check_password_hash(user["password_hash"], password):
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
```

#### ทำไมต้อง Hash?

| วิธี | ปลอดภัยไหม | เหตุผล |
|---|---|---|
| เก็บรหัสผ่านตรง ๆ (plaintext) | ❌ | DB รั่ว = รหัสผ่านทุกคนรั่ว |
| เข้ารหัสแบบถอดกลับได้ (encryption) | ❌ | ถ้ากุญแจรั่วก็ถอดได้ทั้งหมด |
| MD5 / SHA-1 / SHA-256 ล้วน ๆ | ❌ | เร็วเกินไป ถูกเดาด้วย rainbow table / brute force ได้ง่าย |
| **bcrypt / scrypt / Argon2 / PBKDF2** | ✅ | ออกแบบให้ช้าโดยตั้งใจ และมี salt ป้องกันการเดาแบบกลุ่ม |

**Salt** คือค่าสุ่มที่ผสมเข้าไปกับรหัสผ่านก่อน hash ทำให้รหัสผ่านเดียวกันของคนสองคนได้ hash ไม่เหมือนกัน

### 6.2 บทบาทผู้ใช้ (Requirement 2)

| บทบาท | ได้มาอย่างไร | ทำอะไรได้ |
|---|---|---|
| **user** | สมัครผ่านหน้า Register | เขียน/แก้ไข/ลบโพสต์ **ของตัวเอง**, คอมเมนต์, ลบคอมเมนต์ของตัวเอง |
| **admin** | สร้างด้วย `init_db.py` หรือถูก admin คนอื่นเลื่อนขั้น | ทุกอย่างที่ user ทำได้ + เข้าหน้า Admin, จัดการผู้ใช้, ลบโพสต์/คอมเมนต์ของใครก็ได้ |

หลักสำคัญ: **ตรวจสิทธิ์ที่ฝั่งเซิร์ฟเวอร์เสมอ** การซ่อนปุ่มในหน้าเว็บไม่ได้ป้องกันอะไร เพราะใคร ๆ ก็สามารถพิมพ์ URL หรือส่ง request เองได้

#### ตัวอย่างโค้ด: Decorator ตรวจสิทธิ์

```python
from functools import wraps
from flask import session, redirect, url_for, abort

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            abort(403)  # Forbidden: ล็อกอินแล้วแต่ไม่มีสิทธิ์
        return view(*args, **kwargs)
    return wrapped
```

> 📌 ความต่างของรหัสสถานะ: **401** = ยังไม่ได้ล็อกอิน, **403** = ล็อกอินแล้วแต่ไม่มีสิทธิ์, **404** = ไม่พบข้อมูล

### 6.3 CRUD ที่มีเจ้าของ — โพสต์ (Requirement 3)

| การกระทำ | ใครทำได้ |
|---|---|
| **Create** — สร้างโพสต์ | ผู้ใช้ที่ล็อกอินแล้ว (ระบบกำหนด `user_id` จาก session) |
| **Read** — ดูโพสต์ | ทุกคน (รวมผู้เยี่ยมชมที่ไม่ได้ล็อกอิน) |
| **Update** — แก้ไขโพสต์ | **เฉพาะเจ้าของ** |
| **Delete** — ลบโพสต์ | **เจ้าของ** หรือ **admin** (เพื่อการดูแลเนื้อหา) |

#### หัวใจของ Ownership: ตรวจเจ้าของทุกครั้ง

```python
@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)

    # ★ ตรวจว่าผู้ใช้ปัจจุบันคือเจ้าของโพสต์ ไม่ใช่แค่ล็อกอินอยู่
    if post["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "POST":
        # ... validate แล้ว UPDATE ...
        pass
    return render_template("posts/form.html", post=post)
```

**ข้อควรระวัง (IDOR — Insecure Direct Object Reference):** ถ้าไม่ตรวจเจ้าของ ผู้ใช้ A เพียงแค่เปลี่ยน URL จาก `/posts/5/edit` เป็น `/posts/6/edit` ก็แก้โพสต์ของ B ได้ ซึ่งเป็นช่องโหว่ที่พบบ่อยมาก

**ทางเลือกที่ปลอดภัยอีกแบบ:** ใส่เงื่อนไขเจ้าของลงใน SQL ตรง ๆ

```python
db.execute(
    "UPDATE posts SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP "
    "WHERE id = ? AND user_id = ?",
    (title, content, post_id, session["user_id"]),
)
```

### 6.4 ฟอร์มรับข้อมูลและแสดงผลกลับ (Requirement 4)

| ฟอร์ม | ช่องข้อมูล | บันทึกที่ตาราง | แสดงผลที่ |
|---|---|---|---|
| **ฟอร์มโพสต์** (สร้าง/แก้ไข) | `title`, `content` | `posts` | หน้ารายการโพสต์ และหน้ารายละเอียด |
| **ฟอร์มความคิดเห็น** | `content` | `comments` | ใต้โพสต์ในหน้ารายละเอียด |

**เงื่อนไขการตรวจสอบข้อมูล (Validation):**

| ช่อง | กฎ |
|---|---|
| `title` | ห้ามว่าง, ยาวไม่เกิน 100 ตัวอักษร |
| `content` (โพสต์) | ห้ามว่าง, ยาวไม่เกิน 5,000 ตัวอักษร |
| `content` (คอมเมนต์) | ห้ามว่าง, ยาวไม่เกิน 500 ตัวอักษร |

**รูปแบบ Post/Redirect/Get (PRG):** หลังบันทึกฟอร์มสำเร็จให้ `redirect` ไปหน้าอื่นเสมอ ไม่ render หน้าเดิมตรง ๆ เพื่อกันไม่ให้การกดรีเฟรชส่งข้อมูลซ้ำ

**การแสดงข้อมูลที่ผู้ใช้กรอก:** ใช้ `{{ post.title }}` ใน Jinja2 ซึ่ง escape อัตโนมัติ **ห้ามใช้** `|safe` กับข้อมูลที่ผู้ใช้พิมพ์

### 6.5 หน้าผู้ดูแลระบบ (Requirement 5)

เข้าได้เฉพาะ `role = 'admin'` (ป้องกันด้วย `@admin_required`)

| หน้า | URL | ฟังก์ชัน |
|---|---|---|
| Dashboard | `/admin` | แสดงจำนวนผู้ใช้, โพสต์, คอมเมนต์ |
| จัดการผู้ใช้ | `/admin/users` | ดูรายชื่อผู้ใช้, เปลี่ยนบทบาท `user ↔ admin`, ลบผู้ใช้ |
| จัดการโพสต์ | `/admin/posts` | ดูโพสต์ทั้งหมด, ลบโพสต์ที่ไม่เหมาะสม |

**กฎความปลอดภัยของหน้า Admin:**

- admin **ลบหรือลดสิทธิ์ตัวเองไม่ได้** (ป้องกันระบบไม่มี admin เหลือ)
- การลบ/เปลี่ยนบทบาทต้องส่งผ่าน `POST` พร้อม CSRF token เท่านั้น
- ก่อนลบให้มี `confirm()` หรือหน้ายืนยัน

---

## 7. ตารางสิทธิ์ (Permission Matrix)

| การกระทำ | ผู้เยี่ยมชม | user | admin |
|---|:---:|:---:|:---:|
| ดูรายการ/รายละเอียดโพสต์ | ✅ | ✅ | ✅ |
| สมัครสมาชิก / เข้าสู่ระบบ | ✅ | — | — |
| สร้างโพสต์ | ❌ | ✅ | ✅ |
| แก้ไขโพสต์ของ **ตัวเอง** | ❌ | ✅ | ✅ |
| แก้ไขโพสต์ของ **คนอื่น** | ❌ | ❌ | ❌ |
| ลบโพสต์ของ **ตัวเอง** | ❌ | ✅ | ✅ |
| ลบโพสต์ของ **คนอื่น** | ❌ | ❌ | ✅ |
| เขียนความคิดเห็น | ❌ | ✅ | ✅ |
| ลบความคิดเห็นของ **ตัวเอง** | ❌ | ✅ | ✅ |
| ลบความคิดเห็นของ **คนอื่น** | ❌ | ❌ | ✅ |
| เข้าหน้า Admin | ❌ | ❌ | ✅ |
| เปลี่ยนบทบาท / ลบผู้ใช้ | ❌ | ❌ | ✅ |

> admin แก้เนื้อหาของคนอื่นไม่ได้ ทำได้เพียงลบ (เพื่อควบคุมเนื้อหา) — เป็นการออกแบบที่ยึดหลัก **Least Privilege** (ให้สิทธิ์เท่าที่จำเป็น)

---

## 8. รายการ Routes

### สาธารณะ / การยืนยันตัวตน

| Method | URL | คำอธิบาย | ต้องล็อกอิน |
|---|---|---|:---:|
| GET | `/` | หน้ารายการโพสต์ทั้งหมด | ไม่ |
| GET | `/posts/<id>` | รายละเอียดโพสต์ + ความคิดเห็น | ไม่ |
| GET, POST | `/register` | สมัครสมาชิก | ไม่ |
| GET, POST | `/login` | เข้าสู่ระบบ | ไม่ |
| POST | `/logout` | ออกจากระบบ | ใช่ |

### โพสต์และความคิดเห็น

| Method | URL | คำอธิบาย | สิทธิ์ |
|---|---|---|---|
| GET | `/my-posts` | โพสต์ของฉัน | user+ |
| GET, POST | `/posts/new` | สร้างโพสต์ | user+ |
| GET, POST | `/posts/<id>/edit` | แก้ไขโพสต์ | **เจ้าของ** |
| POST | `/posts/<id>/delete` | ลบโพสต์ | เจ้าของ / admin |
| POST | `/posts/<id>/comments` | เพิ่มความคิดเห็น | user+ |
| POST | `/comments/<id>/delete` | ลบความคิดเห็น | เจ้าของ / admin |

### ผู้ดูแลระบบ

| Method | URL | คำอธิบาย | สิทธิ์ |
|---|---|---|---|
| GET | `/admin` | Dashboard | admin |
| GET | `/admin/users` | รายชื่อผู้ใช้ | admin |
| POST | `/admin/users/<id>/role` | เปลี่ยนบทบาท | admin |
| POST | `/admin/users/<id>/delete` | ลบผู้ใช้ | admin |
| GET | `/admin/posts` | โพสต์ทั้งหมด | admin |

> การ **ลบ/แก้ไข/เปลี่ยนแปลงข้อมูล** ต้องใช้ `POST` เสมอ ห้ามใช้ `GET` เพราะลิงก์ธรรมดาอาจถูกเรียกโดยไม่ตั้งใจ (เช่น จาก crawler หรือรูปภาพที่ฝังลิงก์)

---

## 9. พื้นฐานด้านความปลอดภัยที่ต้องรู้

### 9.1 SQL Injection

**ปัญหา:** นำข้อมูลที่ผู้ใช้พิมพ์ไปต่อเป็นสตริงใน SQL

```python
# ❌ อันตราย
db.execute(f"SELECT * FROM users WHERE username = '{username}'")
# ถ้า username = ' OR '1'='1  จะล็อกอินได้โดยไม่ต้องมีรหัสผ่าน

# ✅ ปลอดภัย: ใช้ parameterized query (placeholder)
db.execute("SELECT * FROM users WHERE username = ?", (username,))
```

### 9.2 XSS (Cross-Site Scripting)

**ปัญหา:** ผู้ใช้ฝัง `<script>...</script>` ในโพสต์ แล้วสคริปต์ทำงานในเบราว์เซอร์ของคนอื่น
**วิธีกัน:** escape ข้อมูลทุกครั้งที่แสดงผล (Jinja2 ทำให้อัตโนมัติ) และไม่ใช้ `|safe` กับข้อมูลผู้ใช้

### 9.3 CSRF (Cross-Site Request Forgery)

**ปัญหา:** เว็บอันตรายหลอกให้เบราว์เซอร์ที่ล็อกอินอยู่ ส่งคำขอไปยังเว็บเราโดยที่ผู้ใช้ไม่รู้ตัว (เช่น สั่งลบโพสต์)
**วิธีกัน:** ใส่ CSRF token ในทุกฟอร์มที่เป็น `POST`

```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

```html
<form method="post">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

### 9.4 Session และ Cookie

```python
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],   # ค่าสุ่มยาว ๆ ห้ามฝังในโค้ด / ห้าม commit
    SESSION_COOKIE_HTTPONLY=True,          # JavaScript อ่าน cookie ไม่ได้
    SESSION_COOKIE_SAMESITE="Lax",         # ลดความเสี่ยง CSRF
    # SESSION_COOKIE_SECURE=True,          # เปิดเมื่อใช้ HTTPS
)
```

หลังล็อกอินสำเร็จให้ `session.clear()` ก่อนเขียนค่าใหม่ เพื่อกัน Session Fixation

### 9.5 Mass Assignment

**ปัญหา:** รับค่าจากฟอร์มทั้งหมดไปบันทึกตรง ๆ ผู้โจมตีเพิ่มช่อง `role=admin` ใน request แล้วกลายเป็น admin
**วิธีกัน:** ดึงเฉพาะช่องที่อนุญาตเอง (`username`, `email`, `password`) และกำหนด `role` จากฝั่งเซิร์ฟเวอร์เท่านั้น

### 9.6 สรุปเช็กลิสต์ความปลอดภัย

- [ ] รหัสผ่านถูก hash ด้วยอัลกอริทึมที่เหมาะสม ไม่มี plaintext ในฐานข้อมูลหรือ log
- [ ] ทุก SQL ใช้ placeholder ไม่มีการต่อสตริง
- [ ] ทุกหน้าที่ต้องล็อกอินมี `@login_required`
- [ ] ทุก route ของ admin มี `@admin_required`
- [ ] การแก้/ลบข้อมูลตรวจ **เจ้าของ** ทุกครั้งที่ฝั่งเซิร์ฟเวอร์
- [ ] ฟอร์ม `POST` ทุกอันมี CSRF token
- [ ] ไม่ใช้ `|safe` กับข้อมูลที่ผู้ใช้กรอก
- [ ] `SECRET_KEY` ไม่ได้ฝังในโค้ดและไม่ถูก commit
- [ ] ปิดโหมด debug เมื่อไม่ได้พัฒนา
- [ ] ข้อความ error ตอนล็อกอินเป็นข้อความกลาง ๆ

---

## 10. วิธีติดตั้งและรันโปรเจกต์

### สิ่งที่ต้องมี

- Python 3.10 ขึ้นไป
- Git (ถ้าต้องการ clone โปรเจกต์)

### ขั้นตอน

```bash
# 1) เข้าโฟลเดอร์โปรเจกต์
cd study-blog

# 2) สร้าง virtual environment
python -m venv venv

# 3) เปิดใช้งาน virtual environment
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 4) ติดตั้งไลบรารี
pip install -r requirements.txt

# 5) ตั้งค่า SECRET_KEY (สร้างค่าสุ่มด้วยคำสั่งด้านล่าง)
python -c "import secrets; print(secrets.token_hex(32))"
export SECRET_KEY="ค่าที่ได้จากคำสั่งด้านบน"      # Windows: set SECRET_KEY=...

# 6) สร้างตารางและบัญชี admin เริ่มต้น
python init_db.py

# 7) รันเซิร์ฟเวอร์
flask --app app run --debug
```

เปิดเบราว์เซอร์ที่ <http://127.0.0.1:5000>

### ตัวอย่าง `requirements.txt`

```
Flask
Flask-WTF
```

### บัญชี admin เริ่มต้น

`init_db.py` จะสร้าง admin ให้ 1 บัญชี (ตัวอย่าง `admin` / รหัสผ่านที่กำหนดเอง) — **ให้เปลี่ยนรหัสผ่านทันทีหลังรันครั้งแรก** และห้ามใช้รหัสผ่านเริ่มต้นนี้นอกเครื่องพัฒนา

---

## 11. แนวทางทดสอบ

ทดสอบด้วยมือ (Manual Testing) ตามตารางด้านล่าง ควรมีบัญชีทดสอบอย่างน้อย `userA`, `userB` และ `admin`

### 11.1 การยืนยันตัวตน

| # | ขั้นตอน | ผลที่คาดหวัง |
|---|---|---|
| 1 | สมัครด้วยข้อมูลถูกต้อง | สมัครสำเร็จ ไปหน้า Login |
| 2 | สมัครด้วย username ที่มีอยู่แล้ว | ขึ้น error ไม่สร้างบัญชีซ้ำ |
| 3 | สมัครด้วยรหัสผ่านสั้นกว่า 8 ตัว | ขึ้น error |
| 4 | เปิดไฟล์ `.db` ดูคอลัมน์ `password_hash` | เห็นเป็นข้อความ hash ที่อ่านไม่ออก ไม่ใช่รหัสผ่านจริง |
| 5 | ล็อกอินด้วยรหัสผ่านผิด | ขึ้นข้อความกลาง ๆ ไม่ล็อกอิน |
| 6 | ล็อกอินถูกต้อง แล้วกดออกจากระบบ | กลับสู่สถานะผู้เยี่ยมชม |

### 11.2 สิทธิ์และเจ้าของข้อมูล

| # | ขั้นตอน | ผลที่คาดหวัง |
|---|---|---|
| 7 | ผู้เยี่ยมชมเปิด `/posts/new` | ถูกพาไปหน้า Login |
| 8 | `userA` สร้างโพสต์ แล้วแก้ไข/ลบของตัวเอง | ทำได้ |
| 9 | `userB` พิมพ์ URL `/posts/<id ของ A>/edit` | **403 Forbidden** |
| 10 | `userB` ส่ง `POST /posts/<id ของ A>/delete` (ลองด้วย curl/Postman) | **403 Forbidden** ข้อมูลไม่ถูกลบ |
| 11 | `userA` เปิด `/admin` | **403 Forbidden** |
| 12 | `admin` ลบโพสต์ของ `userA` | ทำได้ |
| 13 | `admin` พยายามลดสิทธิ์/ลบบัญชีตัวเอง | ถูกปฏิเสธ |

### 11.3 ฟอร์มและความปลอดภัย

| # | ขั้นตอน | ผลที่คาดหวัง |
|---|---|---|
| 14 | ส่งฟอร์มโพสต์โดยปล่อยช่องว่าง | ขึ้น error ไม่บันทึก |
| 15 | พิมพ์ `<script>alert(1)</script>` ในโพสต์ | แสดงเป็นข้อความธรรมดา ไม่รันสคริปต์ |
| 16 | พิมพ์ `' OR '1'='1` ในช่อง username ตอนล็อกอิน | ล็อกอินไม่ได้ |
| 17 | ส่ง POST โดยไม่มี CSRF token | ถูกปฏิเสธ (400) |
| 18 | เพิ่มช่อง `role=admin` ในฟอร์มสมัครด้วย DevTools | ยังได้บทบาท `user` |
| 19 | เขียนความคิดเห็นแล้วรีเฟรชหน้า | ความคิดเห็นยังอยู่ ไม่ถูกส่งซ้ำ |

---

## 12. ข้อจำกัดและสิ่งที่ควรต่อยอด

### ข้อจำกัดของโปรเจกต์ระดับพื้นฐาน

- ไม่มี **rate limiting** — ผู้โจมตีลองเดารหัสผ่านซ้ำ ๆ ได้ (brute force)
- ไม่ยืนยันอีเมล และไม่มีระบบรีเซ็ตรหัสผ่าน
- `role` ถูกเก็บใน session — หากเปลี่ยนบทบาทผู้ใช้ จะมีผลเมื่อล็อกอินใหม่ (ระบบจริงควรเช็กจาก DB ทุกคำขอ)
- ใช้ SQLite และ development server — ไม่เหมาะกับงานจริงที่มีผู้ใช้จำนวนมาก
- ยังไม่ใช้ HTTPS

### แนวทางต่อยอด (เรียงจากง่ายไปยาก)

1. เพิ่มระบบ **ค้นหา** และ **แบ่งหน้า (pagination)** ของโพสต์
2. เพิ่ม **หมวดหมู่ / แท็ก** (ความสัมพันธ์แบบ many-to-many)
3. เพิ่ม **การจำกัดจำนวนครั้งที่ล็อกอินผิด** (Flask-Limiter)
4. เพิ่ม **audit log** บันทึกการกระทำของ admin
5. เขียน **automated test** ด้วย `pytest`
6. แยกโค้ดเป็น **Blueprints** ให้เป็นระเบียบ
7. ย้ายไป **PostgreSQL / MySQL** และ deploy ด้วย gunicorn + HTTPS

---

## 13. คำศัพท์ที่ควรรู้

| คำศัพท์ | ความหมาย |
|---|---|
| **Authentication (AuthN)** | การพิสูจน์ว่า "คุณคือใคร" (เช่น ล็อกอิน) |
| **Authorization (AuthZ)** | การตรวจว่า "คุณทำสิ่งนี้ได้ไหม" (เช่น สิทธิ์ admin) |
| **Hash** | ฟังก์ชันแปลงข้อมูลเป็นค่าคงที่แบบทางเดียว ย้อนกลับไม่ได้ |
| **Salt** | ค่าสุ่มที่ผสมกับรหัสผ่านก่อน hash |
| **Session** | ข้อมูลสถานะผู้ใช้ที่เซิร์ฟเวอร์จำไว้ระหว่างหลายคำขอ |
| **Cookie** | ข้อมูลเล็ก ๆ ที่เบราว์เซอร์เก็บและส่งกลับไปกับทุกคำขอ |
| **CRUD** | Create, Read, Update, Delete |
| **Ownership** | ความเป็นเจ้าของข้อมูล ใช้ตัดสินว่าใครแก้/ลบได้ |
| **RBAC** | Role-Based Access Control — คุมสิทธิ์ตามบทบาท |
| **IDOR** | ช่องโหว่ที่เข้าถึงข้อมูลคนอื่นได้ด้วยการเปลี่ยน ID ใน URL |
| **SQL Injection** | แทรกคำสั่ง SQL ผ่านข้อมูลที่ผู้ใช้กรอก |
| **XSS** | แทรกสคริปต์อันตรายให้ทำงานในเบราว์เซอร์ของผู้อื่น |
| **CSRF** | หลอกให้เบราว์เซอร์ของเหยื่อส่งคำขอโดยไม่รู้ตัว |
| **Foreign Key** | คอลัมน์ที่อ้างอิงไปยัง primary key ของอีกตาราง |
| **Least Privilege** | ให้สิทธิ์เท่าที่จำเป็นต่อการทำงานเท่านั้น |
| **PRG** | Post/Redirect/Get — redirect หลังส่งฟอร์มเพื่อกันส่งซ้ำ |

---

## แหล่งเรียนรู้เพิ่มเติม

- [Flask Documentation](https://flask.palletsprojects.com/) — โดยเฉพาะบท Tutorial (Blog) ซึ่งเป็นโครงสร้างใกล้เคียงกับโปรเจกต์นี้
- [OWASP Top 10](https://owasp.org/www-project-top-ten/) — รายการช่องโหว่เว็บที่พบบ่อยที่สุด
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) — แนวทางการเก็บรหัสผ่าน
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

*เอกสารนี้จัดทำเพื่อการศึกษา — ปรับเปลี่ยนหัวข้อ ฟีเจอร์ หรือเทคโนโลยีได้ตามโจทย์ของรายวิชา*
