"""
Check database for students and therapy reports
"""

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

engine = create_engine(DATABASE_URL)

print("🔍 Checking Database...")
print("=" * 70)

try:
    with engine.connect() as conn:
        # Check students
        result = conn.execute(text("SELECT id, student_id, name FROM students LIMIT 10"))
        students = result.fetchall()
        
        print(f"\n👥 STUDENTS IN DATABASE: {len(students)}")
        print("-" * 70)
        if students:
            for student in students:
                print(f"  ID: {student[0]} | Student ID: {student[1]} | Name: {student[2]}")
        else:
            print("  ❌ No students found!")
            print("  You need to add students through the frontend first.")
        
        # Check therapy reports
        result = conn.execute(text("SELECT COUNT(*) FROM therapy_reports"))
        report_count = result.fetchone()[0]
        
        print(f"\n📋 THERAPY REPORTS IN DATABASE: {report_count}")
        print("-" * 70)
        
        if report_count > 0:
            result = conn.execute(text("""
                SELECT s.student_id, s.name, COUNT(tr.id) as report_count
                FROM students s
                LEFT JOIN therapy_reports tr ON s.id = tr.student_id
                GROUP BY s.id, s.student_id, s.name
                HAVING COUNT(tr.id) > 0
                ORDER BY report_count DESC
                LIMIT 10
            """))
            student_reports = result.fetchall()
            
            print("Students with therapy reports:")
            for sr in student_reports:
                print(f"  • {sr[0]} ({sr[1]}): {sr[2]} reports")
                
            if student_reports:
                print(f"\n✅ You can test with student ID: {student_reports[0][0]}")
                print(f"\nRun this command to test:")
                print(f"  python test_ai_with_student.py {student_reports[0][0]}")
        else:
            print("  ❌ No therapy reports found!")
            print("  Add therapy reports through the frontend first.")
            
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure:")
    print("  1. PostgreSQL is running")
    print("  2. Database credentials in .env are correct")
    print("  3. Database has been migrated (alembic upgrade head)")

print("\n" + "=" * 70)
