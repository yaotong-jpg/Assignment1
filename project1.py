import sqlite3
import getpass
import sys
from datetime import datetime, timedelta
from admin import admin_menu
from Instructor import instructor_menu

#Database
DB_PATH = sys.argv[1]

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def mask_credit_card(card_no):
    #update3.5: without using re
    digits = card_no.replace(" ", "")
    if len(digits) >= 4:
        return '**** **** **** ' + digits[-4:]
    return card_no

def validate_card(card_no, cvv, expiry):
    digits = card_no.replace(" ", "")
    if not digits.isdigit() or len(digits) != 16:
        return False, "card number length must be 16 digits"
    if not cvv.isdigit() or len(cvv) != 3:
        return False, "CVV must be 3 digits"
    try:
        exp_date = datetime.strptime(expiry, "%Y-%m-%d")
        if exp_date <= datetime.now():
            return False, "credit card has expired."
    except ValueError:
        return False, "please type in the format YYYY/MM/DD"
    return True, expiry

def paginate(results, page, page_size=5):
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = results[start:end]
    has_prev = page > 1
    has_next = end < total
    return page_data, has_prev, has_next

#Menu for pagination: TO BE IMPROVED
def display_pagination_menu(has_prev, has_next):
    print("\n---Navigation---")
    if has_prev:
        print("P: Previous Page")
    if has_next:
        print("N: Next Page")
    print("Q: Back to Menu")
    

#login/register stuff
def login(conn):
    uid = input("Enter User ID: ").strip()
    pwd = getpass.getpass("Enter Password: ").strip()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT uid, name, role FROM users WHERE uid = ? AND pwd = ?", (uid, pwd))
    user = cursor.fetchone()
    if user:
        print(f"Login successful. Welcome {user['name']} (Role: {user['role']})")
        return {'uid': user['uid'], 'name': user['name'], 'role': user['role']}
    else:
        print("Fail: Invalid User ID or password.")
        return None
    
def register(conn):
    name = input("Enter Name: ").strip()
    email = input("Enter Email: ").strip()
    pwd = getpass.getpass("Enter Password: ").strip()

    cursor = conn.cursor()
    cursor.execute(
        "SELECT uid FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        print("Fail: this email is registered")
        return None
    
    cursor.execute(
        "INSERT INTO users (name, email, role, pwd) VALUES (?, ?, 'Student', ?)", (name, email, pwd))
    conn.commit()
    uid = cursor.lastrowid
    print(f"Registration successful. Your User ID is: {uid}")
    return {'uid': uid, 'name': name, 'role': 'Student'}


#student stuff
def student_menu(conn, user):
    while True:
        print("\n---STUDENT MENU---")
        print("1. Search for Courses")
        print("2. View Enrolled Courses")
        print("3. View Payment History")
        print("4. Logout")
        print("5. Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            search_courses(conn, user)
        elif choice == '2':
            view_enrolled_courses(conn, user)
        elif choice == '3':
            view_payments(conn, user)
        elif choice == '4':
            print("Logged out successful")
            break
        elif choice == '5':
            print("Goodbye!")
            sys.exit()
        else:
            print("Fail: Invalid option")

def search_courses(conn, user):
    keyword = ""
    category = ""
    min_price = ""
    max_price = ""

    #update3.8: now if no result, it will go back to searching menu
    while True:
        #update3.6: menu for course searching
        while True:
            print("\n---Search Courses---")
            print(f"1. Set Keyword (Title/Desc): {keyword}")
            print(f"2. Add Category filter: {category}")
            print(f"3. Add Price filter: Min={min_price}, Max={max_price}")
            print("4. Search")
            print("0. Cancel and Return")

            choice = input("Select an option (0-4): ").strip()

            if choice == '1':
                keyword = input("Keyword (Title/Desc): ").strip()
            elif choice == '2':
                category = input("Category filter: ").strip()
            elif choice == '3':
                t_min = input("Min Price (Enter to skip): ").strip()
                t_max = input("Max Price (Enter to skip): ").strip()
                #update3.6: Add some checking for input
                try:
                    if t_min: float(t_min)
                    if t_max: float(t_max)
                    if t_min and t_max and float(t_min) > float(t_max):
                        print("Fail: Min Price cannot be greater than Max Price.")
                    else:
                        min_price = t_min
                        max_price = t_max
                except ValueError:
                    print("Fail: Price must be a number.")
            elif choice == '4':
                break
            elif choice == '0':
                return
            else:
                print("Fail: Invalid choice. Please try again.")

        query = """
            SELECT c.cid, c.title, c.description, c.category, c.price, c.pass_grade, c.max_students,
            (SELECT COUNT(*) FROM enrollments e
            WHERE e.cid = c.cid AND e.role = 'Student'
            AND datetime('now') BETWEEN e.start_ts 
            AND e.end_ts) AS current_enrollment
            FROM courses c
            WHERE 1=1
        """

        params = []
        #update3.6: better keyword searching algorithm
        if keyword:
            kw_1 = keyword.replace(" ", "").lower()
            kw_2 = f"%{'%'.join(kw_1)}%"
            query += " AND (REPLACE(LOWER(c.title), ' ', '') LIKE ? OR REPLACE(LOWER(c.description), ' ', '') LIKE ?)"
            params.extend([kw_2, kw_2])
        if category:
            #update3.5: can match course name regardless of capitalization
            cat_1 = category.replace(" ", "").lower()
            cat_2 = f"%{'%'.join(cat_1)}%"
            query += " AND REPLACE(LOWER(c.category), ' ', '') LIKE ?"
            params.append(cat_2)
        #update3.6: repair the logic for number comparing query
        if min_price:
            query += " AND CAST(c.price AS REAL) >= ?"
            params.append(float(min_price))
        if max_price:
            query += " AND CAST(c.price AS REAL) <= ?"
            params.append(float(max_price))

        cursor = conn.cursor()
        cursor.execute(query, params)
        courses = cursor.fetchall()

        if not courses:
            print("Fail: No matching course found")
            continue
    
        page = 1
        while True:
            page_courses, has_prev, has_next = paginate(courses, page)
            print(f"\n---Search Results (Page {page})---")
            for idx, c in enumerate(page_courses, 1):
                print(f"{idx}. cid: {c['cid']}, title: {c['title']}, description: {c['description']}, category: {c['category']}, price: {c['price']}, pass_grade: {c['pass_grade']}, max_students: {c['max_students']}, current_enrollment: {c['current_enrollment']}")
        
            display_pagination_menu(has_prev, has_next)
            cmd = input("Enter CID to view details, or P/N/Q: ").strip().upper()
            if cmd == 'Q':
                break
            elif cmd == 'P':
                if has_prev:
                    page -= 1
                else:
                    print("\nNotice: Already on the first page. Cannot go back.")
            elif cmd == 'N':
                if has_next:
                    page += 1
                else:
                    print("\nNotice: Already on the last page. Cannot go forward.")
            else:
                selected_course = next((c for c in page_courses if str(c['cid']) == cmd), None)
                if selected_course:
                    show_course_details(conn, user, selected_course['cid'])
                    cursor.execute(query, params)
                    courses = cursor.fetchall()
                else:
                    print("\nFail:cid not found on current page")

def show_course_details(conn, user, cid):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, (SELECT COUNT(*) FROM enrollments e WHERE e.cid = c.cid AND e.role = 'Student'
                     AND datetime('now') BETWEEN e.start_ts AND e.end_ts) AS current_enrollment
        FROM courses c WHERE c.cid = ?
    """, (cid,))
    course = cursor.fetchone()
    
    print("\n---COURSE DETAILS---")
    for key in course.keys():
        print(f"{key.capitalize()}: {course[key]}")

    cursor.execute("""
        SELECT * FROM enrollments WHERE cid = ? AND uid = ? AND role = 'Student'
        AND datetime('now') BETWEEN start_ts AND end_ts
    """, (cid, user['uid']))

    if cursor.fetchone():
        print("Fail: You are already enrolled in this course.")
        return
    
    if course['current_enrollment'] >= course['max_students']:
        print("Fail: Course is full.")
        return
    
    if input("Enroll in this course? (y/n): ").strip().lower() == 'y':
        enroll_course(conn, user, course)

def enroll_course(conn, user, course):
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    #A student may not have more than one active enrollment in the same course.
    cursor.execute("""
        SELECT 1 FROM enrollments 
        WHERE uid = ? AND cid = ? AND role = 'Student'
          AND ? BETWEEN start_ts AND end_ts
    """, (user['uid'], course['cid'], now_str))
    if cursor.fetchone():
        print("Fail: you have already enrolled in this course.")
        return
    
    #Before enrolling, the system must check if the course is full as determined by `max_students`.
    cursor.execute("""
        SELECT COUNT(*) FROM enrollments 
        WHERE cid = ? AND role = 'Student'
          AND ? BETWEEN start_ts AND end_ts
    """, (course['cid'], now_str))
    current_enrolled = cursor.fetchone()[0]
    if current_enrolled >= course['max_students']:
        print("Fail: this course is full.")
        return
    
    #update3.6: false input won't cause going back to course searching page now.
    print("\n---Payment Detail---")
    
    #card number length must be 16 digits (numeric) –user is allowed to enter spaces.
    while True:
        raw_card_no = input("Card Number (16 digits): ").strip()
        card_no = raw_card_no.replace(" ", "")
        if card_no.isdigit() and len(card_no) == 16:
            break
        print("Fail: card number length must be 16 digits. Please try again.")
    
    #CVV must be 3 digits (numeric) — do not store CVV (not in schema)
    while True:
        cvv = input("CVV (3 digits): ").strip()
        if cvv.isdigit() and len(cvv) == 3:
            break
        print("Fail: CVV must be 3 digits. Please try again.")
    
    #expiry date must not have expired (must be a future date)
    while True:
        expiry_str = input("Expiry Date(YYYY-MM-DD): ").strip()
        try:
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            if expiry_date <= datetime.now():
                print("Fail: credit card has expired. Please enter a valid future date.")
            else:
                break
        except ValueError:
            print("Fail: please type in the format YYYY-MM-DD")
    
    try:
        now = datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M:%S')

        end_ts_str = (now + timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            INSERT INTO payments (uid, cid, ts, credit_card_no, expiry_date) 
            VALUES (?, ?, ?, ?, ?)
        """, (user['uid'], course['cid'], now_str, card_no, expiry_str))

        cursor.execute("""
            INSERT INTO enrollments (cid, uid, start_ts, end_ts, role) 
            VALUES (?, ?, ?, ?, 'Student')
        """, (course['cid'], user['uid'], now_str, end_ts_str))
        
        conn.commit()

        masked_card = f"**** **** **** {card_no[-4:]}"
        
        print("\nRegistration Successfull")
        print(f"cid: {course['cid']}")
        print(f"title: {course['title']}")
        print(f"price: {course['price']}")
        print(f"payments.ts: {now_str}")
        print(f"masked card number: {masked_card}")

    except Exception as e:
        conn.rollback()
        print(f"Fail to enroll: {e}")

def view_enrolled_courses(conn, user):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.cid, c.title, c.category, e.start_ts, c.pass_grade
        FROM enrollments e JOIN courses c ON e.cid = c.cid
        WHERE e.uid = ? AND e.role = 'Student' AND datetime('now') BETWEEN e.start_ts AND e.end_ts
    """, (user['uid'],))
    courses = cursor.fetchall()
    if not courses:
        print("Fail: no active enrollments.")
        return
    
    #update3.5: when the first and last pages are reached, page turning is not allowed, and a notification is displayed
    page = 1
    while True:
        page_courses, has_prev, has_next = paginate(courses, page)
        print(f"\n---Enrolled Courses (Page {page})---")
        for idx, c in enumerate(page_courses, 1):
            print(f"{idx}. cid: {c['cid']}, title: {c['title']}, category: {c['category']}, start: {c['start_ts']}, pass grade: {c['pass_grade']}")

        display_pagination_menu(has_prev, has_next)
        cmd = input("Enter cid to view course menu, or P/N/Q: ").strip().upper()
        if cmd == 'Q': 
            break
        elif cmd == 'P': 
            if has_prev:
                page -= 1
            else:
                print("\nNotice: Already on the first page")
        elif cmd == 'N': 
            if has_next:
                page += 1
            else:
                print("\nNotice: Already on the last page")
        else:
            selected_course = next((c for c in page_courses if str(c['cid']) == cmd), None)
            if selected_course:
                enrolled_course_menu(conn, user, selected_course['cid'])
            else:
                print("\nFail: cid not found on current page")

def enrolled_course_menu(conn, user, cid):
    while True:
        print(f"\n---Course {cid} Options---")
        print("1. See all modules")
        print("2. See grades")
        print("3. See certificate")
        print("4. Back")
        choice = input("Choice: ").strip()
        if choice == '1': view_modules(conn, user, cid)
        elif choice == '2': view_grades(conn, user, cid)
        elif choice == '3': view_certificate(conn, user, cid)
        elif choice == '4': break

def view_modules(conn, user, cid):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT mid, name, weight, summary FROM modules WHERE cid = ?", (cid,))
    modules = cursor.fetchall()
    if not modules:
        print("Fail: no modules found.")
        return
    
    page = 1
    while True:
        page_modules, has_prev, has_next = paginate(modules, page)
        print(f"\n---Modules (Page {page})---")
        for idx, m in enumerate(page_modules, 1):
            print(f"{idx}. mid: {m['mid']}, name: {m['name']}, weight: {m['weight']}, summary: {m['summary']}")

        display_pagination_menu(has_prev, has_next)
        cmd = input("Enter mid to view lessons, or P/N/Q: ").strip().upper()
        if cmd == 'Q': 
            break
        elif cmd == 'P':
            if has_prev: page -= 1
            else: print("\nNotice: Already on the first page")
        elif cmd == 'N':
            if has_next: page += 1
            else: print("\nNotice: Already on the last page")
        else:
            selected_module = next((m for m in page_modules if str(m['mid']) == cmd), None)
            if selected_module:
                view_lessons(conn, user, cid, selected_module['mid'])
            else:
                print("\nFail: mid not found on current page")

def view_lessons(conn, user, cid, mid):
    cursor = conn.cursor()
    #update3.8: it wil update the complement after student choose y now.
    query = """
        SELECT l.lid, l.title, l.duration,
               CASE WHEN EXISTS (SELECT 1 FROM completion cp WHERE cp.uid=? AND cp.cid=l.cid AND cp.mid=l.mid AND cp.lid=l.lid) 
               THEN 'Completed' ELSE 'Not Completed' END AS status
        FROM lessons l WHERE l.cid = ? AND l.mid = ?
    """
    params = (user['uid'], cid, mid)
    cursor.execute(query, params)
    lessons = cursor.fetchall()
    
    page = 1
    while True:
        page_lessons, has_prev, has_next = paginate(lessons, page)
        print(f"\n---Lessons (Page {page})---")
        for idx, le in enumerate(page_lessons, 1):
            print(f"{idx}. lid: {le['lid']}, title: {le['title']}, duration: {le['duration']}, status: {le['status']}")
        
        display_pagination_menu(has_prev, has_next)
        cmd = input("Enter lid to view detail, or P/N/Q: ").strip().upper()
        if cmd == 'Q': 
            break
        elif cmd == 'P':
            if has_prev: page -= 1
            else: print("\nNotice: Already on the first page")
        elif cmd == 'N':
            if has_next: page += 1
            else: print("\nNotice: Already on the last page")
        else:
            selected_lesson = next((le for le in page_lessons if str(le['lid']) == cmd), None)
            if selected_lesson:
                show_lesson_detail(conn, user, cid, mid, selected_lesson['lid'])
                cursor.execute(query, params)
                lessons = cursor.fetchall()
            else:
                print("\nFail: lid not found on current page.")


def show_lesson_detail(conn, user, cid, mid, lid):
    cursor = conn.cursor()
    
    #update3.5: use LEFT JOIN instead of CASE WHEN
    cursor.execute("""
        SELECT l.cid, l.mid, l.lid, l.title, l.duration, l.content, cp.uid AS completed_uid
        FROM lessons l
        LEFT JOIN completion cp ON l.cid = cp.cid AND l.mid = cp.mid AND l.lid = cp.lid AND cp.uid = ?
        WHERE l.cid = ? AND l.mid = ? AND l.lid = ?
    """, (user['uid'], cid, mid, lid))
    
    lesson = cursor.fetchone()
    if not lesson:
        print("Fail: Lesson not found")
        return
    
    status = 'Completed' if lesson['completed_uid'] else 'Not Completed'

    #update3.5: print exactly as requirements
    print("\n---Lesson Detail---")
    print(f"cid: {lesson['cid']}")
    print(f"mid: {lesson['mid']}")
    print(f"lid: {lesson['lid']}")
    print(f"title: {lesson['title']}")
    print(f"duration: {lesson['duration']}")
    print(f"content: {lesson['content']}")
    print(f"status: {status}")

    if status == 'Not Completed':
        ans = input("\nMark as complete?(y/n): ").strip().lower()
        if ans == 'y':
            try:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    INSERT INTO completion (uid, cid, mid, lid, ts) 
                    VALUES (?, ?, ?, ?, ?)
                """, (user['uid'], cid, mid, lid, now))

                conn.commit()
                print("Status updated to Completed.")
                return True
            except Exception as e:
                conn.rollback()
                print(f"Fail: Cannot update status: {e}")
    else:
        #If the lesson is already completed, do not insert another row; show a message
        print("\nFail: This lesson is already completed.")

    return False

def view_grades(conn, user, cid):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.mid, m.name, m.weight, g.grade, g.received_ts
        FROM modules m LEFT JOIN grades g ON g.cid = m.cid AND g.mid = m.mid AND g.uid = ?
            AND g.received_ts = (
                -- only join to the most recently received grade for this module
                SELECT MAX(g2.received_ts) FROM grades g2
                WHERE g2.uid = ? AND g2.cid = m.cid AND g2.mid = m.mid
            )
        WHERE m.cid = ?
    """, (user['uid'], user['uid'], cid))
    rows = cursor.fetchall()
    
    print("\n---Module Grades---")
    total_weight = 0
    weighted_sum = 0
    has_grades = False
    for r in rows:
        if r['grade'] is not None:
            grade_str = str(r['grade'])
        else:
            grade_str = "N/A"

        if r['received_ts'] is not None:
            ts_str = r['received_ts']
        else:
            ts_str = "N/A"

        print(f"mid: {r['mid']}, module_name: {r['name']}, weight: {r['weight']}, grade: {grade_str}, received_ts: {ts_str}")

        if r['grade'] is not None:
            total_weight = total_weight + r['weight']
            weighted_sum = weighted_sum + (r['grade'] * r['weight'])
            has_grades = True

    final_grade = weighted_sum / total_weight if has_grades and total_weight > 0 else "N/A"
    print(f"\nfinal_grade = {final_grade}")

def view_certificate(conn, user, cid):
    cursor = conn.cursor()
    #update3.5: don't need ORDER BY
    cursor.execute("""
        SELECT c.cid, co.title AS course_title, c.received_ts, c.final_grade
        FROM certificates c 
        JOIN courses co ON c.cid = co.cid
        WHERE c.cid = ? AND c.uid = ?
    """, (cid, user['uid']))
    cert = cursor.fetchone()
    
    if cert:
        print("\n---Certificate Earned---")
        print(f"cid: {cert['cid']}")
        print(f"course_title: {cert['course_title']}")
        print(f"received_ts: {cert['received_ts']}")
        print(f"final_grade: {cert['final_grade']}")
    else:
        print("\nFail: No certificate found")

def view_payments(conn, user):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.ts, p.cid, c.title AS course_title, p.credit_card_no, p.expiry_date
        FROM payments p 
        JOIN courses c ON p.cid = c.cid
        WHERE p.uid = ? 
        ORDER BY p.ts DESC
    """, (user['uid'],))
    
    payments = cursor.fetchall()
    if not payments:
        print("\nFail: No payment history found")
        return
    
    page = 1
    while True:
        page_pays, has_prev, has_next = paginate(payments, page)
        print(f"\n---Payment History (Page {page})---")
        
        for idx, p in enumerate(page_pays, 1):
            print(f"\n[{idx}]")
            print(f"ts: {p['ts']}")
            print(f"cid: {p['cid']}")
            print(f"course_title: {p['course_title']}")
            print(f"masked_card number: {mask_credit_card(p['credit_card_no'])}")
            print(f"expiry_date: {p['expiry_date']}")
        
        display_pagination_menu(has_prev, has_next)
        
        #update3.5: complete the page turning
        cmd = input("Choice (N for Next, P for Prev, Q to quit): ").strip().upper()
        
        if cmd == 'Q': 
            break
        elif cmd == 'P':
            if has_prev:
                page -= 1
            else:
                print("\nNotice: Already on the first page. Cannot go back.")
        elif cmd == 'N':
            if has_next:
                page += 1
            else:
                print("\nNotice: Already on the last page. Cannot go forward.")
        else:
            print("\nFail: Invalid choice. Please enter N,P,or Q")

#main function with menu
def main():
    conn = get_db_connection()
    while True:
        print("\n---LEARNING MANAGEMENT SYSTEM---")
        print("1. Login")
        print("2. Register (Student)")
        print("3. Exit")
        choice = input("Choice: ").strip()
        if choice == '1':
            user = login(conn)
            if user:
                if user['role'] == 'Student': student_menu(conn, user)
                elif user['role'] == 'Admin': admin_menu(conn, user)
                elif user['role'] == 'Instructor': instructor_menu(conn, user)
                else: print(f"{user['role']} menus not implemented in this demo.")
        elif choice == '2':
            user = register(conn)
            if user: student_menu(conn, user)
        elif choice == '3':
            break
    conn.close()

if __name__ == "__main__":
    main()

