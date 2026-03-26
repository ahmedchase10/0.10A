
# add this at the top of test_tools.py temporarily
import sys
import os

# go up one level from tools/ to backend/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# change working directory to backend/
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print(f"Current directory: {os.getcwd()}")
print(f"Files here: {os.listdir('.')}")

from backend.config import GOOGLE_CREDENTIALS_PATH
print(f"Credentials path: {GOOGLE_CREDENTIALS_PATH}")
print(f"File exists: {os.path.exists(GOOGLE_CREDENTIALS_PATH)}")
# test_tools.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tools.gmail_tools import draft_email, send_email
from backend.tools.classroom_tools import list_classrooms

# ── Test 1: List Classrooms ───────────────────────────────────────────────
print("=" * 50)
print("TEST 1: List Classrooms")
print("=" * 50)

result = list_classrooms.invoke({})
print(result)

# ── Test 2: Draft Email ───────────────────────────────────────────────────
print("\n" + "=" * 50)
print("TEST 2: Draft Email")
print("=" * 50)

result = draft_email.invoke({
    "to": "bouzer381@gmail.com",  # ← replace with your dev gmail
    "subject": "Test email from teacher agent",
    "body": "This is a test email drafted by the teacher agent."
})
print(result)

# ── Test 3: Send Email ────────────────────────────────────────────────────
print("\n" + "=" * 50)
print("TEST 3: Send Email")
print("=" * 50)

confirm = input("\nDo you want to actually send a test email? (yes/no): ")
if confirm.lower() == "yes":
    result = send_email.invoke({
        "to": "ahmedmidou.as@gmail.com",  # ← replace with your dev gmail
        "subject": "Test sent email from teacher agent",
        "body": "This is a test email sent by the teacher agent."
    })
    print(result)
else:
    print("Skipped sending email ✓")

print("\nAll tests done ✓")