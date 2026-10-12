import os
import re
import sqlite3
import unittest
from app import app, get_db
from init_db import init_db

TEST_DB = "test_study_blog.db"

class StudyBlogTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["DATABASE"] = os.path.join(app.root_path, TEST_DB)
        app.config["WTF_CSRF_ENABLED"] = True  # Keep CSRF enabled for security testing!
        
        # Fresh test database
        if os.path.exists(app.config["DATABASE"]):
            os.remove(app.config["DATABASE"])
        init_db(app.config["DATABASE"])
        
        self.client = app.test_client()

    def tearDown(self):
        if os.path.exists(app.config["DATABASE"]):
            try:
                os.remove(app.config["DATABASE"])
            except PermissionError:
                pass

    def get_csrf_token(self, response_data):
        """Extract CSRF token from HTML form"""
        html = response_data.decode("utf-8")
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html)
        if not match:
            # Try alternate order value before name
            match = re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html)
        return match.group(1) if match else None

    # -------------------------------------------------------------
    # 11.1 การยืนยันตัวตน (Authentication)
    # -------------------------------------------------------------
    def test_01_register_valid(self):
        """#1 สมัครด้วยข้อมูลถูกต้อง -> สำเร็จ ไปหน้า Login"""
        res = self.client.get("/register")
        token = self.get_csrf_token(res.data)
        
        res = self.client.post("/register", data={
            "csrf_token": token,
            "username": "userA",
            "email": "usera@example.com",
            "password": "Password123",
            "confirm_password": "Password123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("สมัครสมาชิกสำเร็จเรียบร้อย".encode("utf-8"), res.data)

    def test_02_register_duplicate_username(self):
        """#2 สมัครด้วย username ที่มีอยู่แล้ว -> ขึ้น error ไม่สร้างซ้ำ"""
        res = self.client.get("/register")
        token = self.get_csrf_token(res.data)
        # 'admin' already created in init_db
        res = self.client.post("/register", data={
            "csrf_token": token,
            "username": "admin",
            "email": "otheradmin@example.com",
            "password": "Password123",
            "confirm_password": "Password123"
        }, follow_redirects=True)
        self.assertIn("ชื่อผู้ใช้นี้ถูกใช้งานแล้ว".encode("utf-8"), res.data)

    def test_03_register_short_password(self):
        """#3 สมัครด้วยรหัสผ่านสั้นกว่า 8 ตัว -> ขึ้น error"""
        res = self.client.get("/register")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/register", data={
            "csrf_token": token,
            "username": "userShort",
            "email": "usershort@example.com",
            "password": "123",
            "confirm_password": "123"
        }, follow_redirects=True)
        self.assertIn("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร".encode("utf-8"), res.data)

    def test_04_password_hashed_in_db(self):
        """#4 เปิดดูคอลัมน์ password_hash -> ไม่ใช่รหัสผ่านจริง"""
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        pw_hash = row[0]
        self.assertNotEqual(pw_hash, "Admin@12345")
        self.assertTrue(pw_hash.startswith("scrypt:") or pw_hash.startswith("pbkdf2:"))

    def test_05_login_wrong_password(self):
        """#5 ล็อกอินด้วยรหัสผ่านผิด -> ขึ้นข้อความกลาง ๆ ไม่ล็อกอิน"""
        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/login", data={
            "csrf_token": token,
            "username": "admin",
            "password": "WrongPassword!"
        }, follow_redirects=True)
        self.assertIn("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง".encode("utf-8"), res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    def test_06_login_and_logout(self):
        """#6 ล็อกอินถูกต้อง แล้วกดออกจากระบบ -> กลับสู่สถานะผู้เยี่ยมชม"""
        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/login", data={
            "csrf_token": token,
            "username": "admin",
            "password": "Admin@12345"
        }, follow_redirects=True)
        self.assertIn("ยินดีต้อนรับ".encode("utf-8"), res.data)
        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get("user_id"))
            self.assertNotIn("role", sess)
            
        # Logout
        token = self.get_csrf_token(res.data)
        res = self.client.post("/logout", data={"csrf_token": token}, follow_redirects=True)
        self.assertIn("ออกจากระบบเรียบร้อยแล้ว".encode("utf-8"), res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    # -------------------------------------------------------------
    # Helper to register and login users
    # -------------------------------------------------------------
    def logout(self):
        with self.client.session_transaction() as sess:
            sess.clear()

    def create_and_login_user(self, username, password="Password123", role="user"):
        self.logout()
        res = self.client.get("/register")
        token = self.get_csrf_token(res.data)
        self.client.post("/register", data={
            "csrf_token": token,
            "username": username,
            "email": f"{username}@test.com",
            "password": password,
            "confirm_password": password
        })
        if role == "admin":
            conn = sqlite3.connect(app.config["DATABASE"])
            conn.execute("UPDATE users SET role = 'admin' WHERE username = ?", (username,))
            conn.commit()
            conn.close()

        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        self.client.post("/login", data={
            "csrf_token": token,
            "username": username,
            "password": password
        })

    # -------------------------------------------------------------
    # 11.2 สิทธิ์และเจ้าของข้อมูล (Permissions & Ownership)
    # -------------------------------------------------------------
    def test_07_guest_access_new_post(self):
        """#7 ผู้เยี่ยมชมเปิด /posts/new -> ถูกพาไปหน้า Login"""
        res = self.client.get("/posts/new", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn("/login", res.headers.get("Location"))

    def test_08_user_crud_own_post(self):
        """#8 userA สร้างโพสต์ แล้วแก้ไข/ลบของตัวเอง -> ทำได้"""
        self.create_and_login_user("userA")
        
        # Create post
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "Post by UserA",
            "content": "Original Content"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Post by UserA".encode("utf-8"), res.data)
        
        # Get post ID
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE title = 'Post by UserA'")
        post_id = cursor.fetchone()[0]
        conn.close()
        
        # Edit own post
        res = self.client.get(f"/posts/{post_id}/edit")
        token = self.get_csrf_token(res.data)
        res = self.client.post(f"/posts/{post_id}/edit", data={
            "csrf_token": token,
            "title": "Post by UserA Updated",
            "content": "Updated Content"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Post by UserA Updated".encode("utf-8"), res.data)
        
        # Delete own post
        token = self.get_csrf_token(res.data)
        res = self.client.post(f"/posts/{post_id}/delete", data={
            "csrf_token": token
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("ลบโพสต์เรียบร้อยแล้ว".encode("utf-8"), res.data)

    def test_09_userb_cannot_edit_usera_post(self):
        """#9 userB พิมพ์ URL /posts/<id ของ A>/edit -> 403 Forbidden"""
        self.create_and_login_user("userA")
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "A's Post",
            "content": "Secret Content"
        })
        
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE title = \"A's Post\"")
        post_id = cursor.fetchone()[0]
        conn.close()
        
        # Switch to userB
        self.client.get("/logout")
        self.create_and_login_user("userB")
        
        res = self.client.get(f"/posts/{post_id}/edit")
        self.assertEqual(res.status_code, 403)
        self.assertIn("403 Forbidden".encode("utf-8"), res.data)

    def test_10_userb_cannot_delete_usera_post(self):
        """#10 userB ส่ง POST /posts/<id ของ A>/delete -> 403 Forbidden ข้อมูลไม่ถูกลบ"""
        self.create_and_login_user("userA")
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "A's Post To Keep",
            "content": "Cannot delete this"
        })
        
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE title = \"A's Post To Keep\"")
        post_id = cursor.fetchone()[0]
        conn.close()
        
        # Switch to userB
        self.client.get("/logout")
        self.create_and_login_user("userB")
        
        res = self.client.get(f"/posts/{post_id}")
        token = self.get_csrf_token(res.data)
        res = self.client.post(f"/posts/{post_id}/delete", data={"csrf_token": token})
        self.assertEqual(res.status_code, 403)
        
        # Verify still in DB
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_11_user_cannot_access_admin(self):
        """#11 userA เปิด /admin -> 403 Forbidden"""
        self.create_and_login_user("userA")
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 403)
        self.assertIn("403 Forbidden".encode("utf-8"), res.data)

    def test_12_admin_can_delete_user_post(self):
        """#12 admin ลบโพสต์ของ userA -> ทำได้"""
        self.create_and_login_user("userA")
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "Inappropriate Post",
            "content": "Spam"
        })
        
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE title = 'Inappropriate Post'")
        post_id = cursor.fetchone()[0]
        conn.close()
        
        # Login as admin
        self.logout()
        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        self.client.post("/login", data={
            "csrf_token": token,
            "username": "admin",
            "password": "Admin@12345"
        })
        
        res = self.client.get(f"/posts/{post_id}")
        token = self.get_csrf_token(res.data)
        res = self.client.post(f"/posts/{post_id}/delete", data={"csrf_token": token}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn("ลบโพสต์เรียบร้อยแล้ว".encode("utf-8"), res.data)
        
        # Verify deleted in DB
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        self.assertIsNone(cursor.fetchone())
        conn.close()

    def test_13_admin_cannot_demote_or_delete_self(self):
        """#13 admin พยายามลดสิทธิ์/ลบบัญชีตัวเอง -> ถูกปฏิเสธ"""
        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        self.client.post("/login", data={
            "csrf_token": token,
            "username": "admin",
            "password": "Admin@12345"
        })
        
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_id = cursor.fetchone()[0]
        conn.close()
        
        # Attempt to change self role
        res = self.client.get("/admin/users")
        token = self.get_csrf_token(res.data)
        res = self.client.post(f"/admin/users/{admin_id}/role", data={
            "csrf_token": token,
            "role": "user"
        }, follow_redirects=True)
        self.assertIn("ไม่สามารถแก้ไขบทบาทของตัวเองได้".encode("utf-8"), res.data)
        
        # Attempt to delete self
        token = self.get_csrf_token(res.data)
        res = self.client.post(f"/admin/users/{admin_id}/delete", data={
            "csrf_token": token
        }, follow_redirects=True)
        self.assertIn("ไม่สามารถลบบัญชีของตัวเองได้".encode("utf-8"), res.data)

    # -------------------------------------------------------------
    # 11.3 ฟอร์มและความปลอดภัย (Forms & Security)
    # -------------------------------------------------------------
    def test_14_empty_post_validation(self):
        """#14 ส่งฟอร์มโพสต์โดยปล่อยช่องว่าง -> ขึ้น error ไม่บันทึก"""
        self.create_and_login_user("userA")
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "",
            "content": ""
        }, follow_redirects=True)
        self.assertIn("กรุณากรอกหัวข้อโพสต์".encode("utf-8"), res.data)

    def test_15_xss_protection(self):
        """#15 พิมพ์ <script>alert(1)</script> ในโพสต์ -> แสดงเป็นข้อความธรรมดา ไม่รันสคริปต์"""
        self.create_and_login_user("userA")
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "XSS Test",
            "content": "<script>alert(1)</script>"
        }, follow_redirects=True)
        
        # In HTML response, it should be escaped: &lt;script&gt;alert(1)&lt;/script&gt;
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", res.data)
        self.assertNotIn(b"<script>alert(1)</script>", res.data)

    def test_16_sql_injection_safe(self):
        """#16 พิมพ์ ' OR '1'='1 ในช่อง username ตอนล็อกอิน -> ล็อกอินไม่ได้"""
        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/login", data={
            "csrf_token": token,
            "username": "' OR '1'='1",
            "password": "any"
        }, follow_redirects=True)
        self.assertIn("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง".encode("utf-8"), res.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    def test_17_csrf_protection_blocks_post(self):
        """#17 ส่ง POST โดยไม่มี CSRF token -> ถูกปฏิเสธ (400)"""
        self.create_and_login_user("userA")
        # Submit POST without csrf_token
        res = self.client.post("/posts/new", data={
            "title": "No CSRF",
            "content": "Should Fail"
        })
        self.assertEqual(res.status_code, 400)

    def test_18_mass_assignment_safe(self):
        """#18 เพิ่มช่อง role=admin ในฟอร์มสมัคร -> ยังได้บทบาท user"""
        res = self.client.get("/register")
        token = self.get_csrf_token(res.data)
        self.client.post("/register", data={
            "csrf_token": token,
            "username": "hackerUser",
            "email": "hacker@test.com",
            "password": "Password123",
            "confirm_password": "Password123",
            "role": "admin"  # Mass assignment attempt
        })
        
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = 'hackerUser'")
        role = cursor.fetchone()[0]
        conn.close()
        self.assertEqual(role, "user")

    def test_19_prg_pattern_comment(self):
        """#19 เขียนความคิดเห็นแล้ว redirect (PRG)"""
        self.create_and_login_user("userA")
        res = self.client.get("/posts/new")
        token = self.get_csrf_token(res.data)
        self.client.post("/posts/new", data={
            "csrf_token": token,
            "title": "Discussion Post",
            "content": "What do you think?"
        })
        
        conn = sqlite3.connect(app.config["DATABASE"])
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE title = 'Discussion Post'")
        post_id = cursor.fetchone()[0]
        conn.close()
        
        res = self.client.get(f"/posts/{post_id}")
        token = self.get_csrf_token(res.data)
        
        # Post comment -> should redirect (302) to post_detail
        res = self.client.post(f"/posts/{post_id}/comments", data={
            "csrf_token": token,
            "content": "Great article!"
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), f"/posts/{post_id}")
        
        # Following redirect shows the comment
        res = self.client.get(f"/posts/{post_id}")
        self.assertIn("Great article!".encode("utf-8"), res.data)

    # -------------------------------------------------------------
    # 11.4 การทดสอบความปลอดภัยเพิ่มเติม (Burp Suite Hardening Tests)
    # -------------------------------------------------------------
    def test_20_security_headers_present(self):
        """#20 ตรวจสอบ Response Headers ต้องมี CSP, XFO, HSTS, nosniff ครบถ้วน"""
        res = self.client.get("/")
        self.assertIn("Content-Security-Policy", res.headers)
        self.assertEqual(res.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertIn("max-age=31536000", res.headers.get("Strict-Transport-Security", ""))
        self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertNotIn("Server", res.headers)
        self.assertNotIn("X-Render-Origin-Server", res.headers)

    def test_21_open_redirect_prevention(self):
        """#21 Open Redirect: ?next=//evil.com หรือ https://evil.com ถูกส่งกลับ index"""
        res = self.client.get("/login")
        token = self.get_csrf_token(res.data)
        res = self.client.post("/login?next=//evil.com", data={
            "csrf_token": token,
            "username": "admin",
            "password": "Admin@12345"
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.headers.get("Location"), "/")

    def test_22_password_policy_enforcement(self):
        """#22 Password Policy: ปฏิเสธ password=username และรหัสที่ขาด complexity"""
        res = self.client.get("/register")
        token = self.get_csrf_token(res.data)
        # 1. Password equals username
        res = self.client.post("/register", data={
            "csrf_token": token,
            "username": "userWeak",
            "email": "weak@test.com",
            "password": "userWeak",
            "confirm_password": "userWeak"
        }, follow_redirects=True)
        self.assertIn("รหัสผ่านต้องไม่ตรงกับชื่อผู้ใช้".encode("utf-8"), res.data)

        # 2. Password missing uppercase or digits
        token = self.get_csrf_token(res.data)
        res = self.client.post("/register", data={
            "csrf_token": token,
            "username": "userWeak2",
            "email": "weak2@test.com",
            "password": "onlylowercase",
            "confirm_password": "onlylowercase"
        }, follow_redirects=True)
        self.assertIn("รหัสผ่านต้องประกอบด้วยตัวพิมพ์ใหญ่".encode("utf-8"), res.data)

    def test_23_client_role_tampering_ignored(self):
        """#23 Client-Side Cookie Tampering: ปลอมแปลง role ใน session ไม่มีผล (ตรวจจาก DB เสมอ)"""
        self.create_and_login_user("userRegular")
        # Attacker injects 'role: admin' into client-side session
        with self.client.session_transaction() as sess:
            sess["role"] = "admin"

        # Access /admin -> must still return 403 because DB role is 'user'
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 403)

if __name__ == "__main__":
    unittest.main()
