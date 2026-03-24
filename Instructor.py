import sys
def instructor_menu(conn, user):
    while True:
        #print available courses
        print("\n---Currently Available Courses---")
        cursor = conn.cursor()
        cursor.execute("""SELECT c.cid, c.title, c.price, c.pass_grade, c.max_students
                            FROM enrollments e JOIN users u ON e.uid = u.uid
                            JOIN courses c ON e.cid = c.cid
                            WHERE u.uid = ? AND CURRENT_TIMESTAMP BETWEEN e.start_ts AND e.end_ts""", (user['uid'],))
        courses = cursor.fetchall()
        for idx, c in enumerate(courses, 1):
            print(f"{idx}. CID: {c[0]}, Title: {c[1]}, Price: {c[2]}, Pass Grade: {c[3]}, Maximum Students: {c[4]}")
        print("\n---Instructor Menu---")
        print("1. Update Courses")
        print("2. Course Statistics")
        print("3. Override Enrollment")
        print("4. Logout")
        print("5. Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            update_courses(conn, user)
        elif choice == '2':
            view_course_stats(conn, user)
        elif choice == '3':
            override_enroll(conn, user)
        elif choice == '4':
            print("Logged out successful")
            break
        elif choice == '5':
            print("Goodbye!")
            sys.exit()
        else:
            print("Fail: Invalid option")

def update_courses(conn, user):
    #menu for updating courses
    cursor = conn.cursor()
    cid = input("Select CID (required): ")
    if(not cid.isnumeric()):  #if cid is left empty or not a number
        print("Invalid CID")
        return

    #finds if course exists
    cursor.execute("""SELECT COUNT(*) FROM courses
                        WHERE cid = ?;""", (cid,))
    is_course = cursor.fetchall()[0][0]
    if not is_course:
        print("Course ID does not exist")
        return

    #finds if instructor teaches this course
    cursor.execute("""SELECT COUNT(*) FROM enrollments
                        WHERE cid = ? AND uid = ?
                        AND CURRENT_TIMESTAMP BETWEEN start_ts AND end_ts""", (cid, user['uid']))
    teaches_course = cursor.fetchall()[0][0]
    if not teaches_course:
        print("You do not teach this course")
        return

    cursor.execute("""SELECT cid, price, pass_grade, max_students
                    FROM courses
                    WHERE cid = ?;
                    """, (cid,))
    course = cursor.fetchall()[0]
    print(f"cid: {cid}, price: {course[1]}, pass_grade: {course[2]}, max_students: {course[3]}")
    print("Select New Values (leave blank for no change): ")
    price = input("New Price: ").strip()
    pass_grade = input("New Pass Grade: ").strip()
    max_students = input("New Maximum Students: ").strip()
    query = "UPDATE courses "
    params = []
    #if parameter is included, append to params, otherwise append name of attribute (no change)
    if price or pass_grade or max_students:
        query += "SET "
        if price:
            params.append(price)
            query += "price = ?"
            if pass_grade or max_students:
                query += ", "
        if pass_grade:
            params.append(pass_grade)
            query += "pass_grade = ?"
            if max_students: query += ", "
        if max_students:
            params.append(max_students)
            query += "max_students = ?"
        query += " WHERE cid = ?"
        params.append(cid)
    else: query = "UPDATE courses SET price = price"
    cursor.execute(query, params)
    if pass_grade: 
        update_certs(conn, cid, int(pass_grade))
    else:
        update_certs(conn, cid, -1)
    conn.commit()



def update_certs(conn, cid, pass_grade):
    #makes sure certificates are up to date
    cursor = conn.cursor()
    if pass_grade == -1:
        cursor.execute(f"SELECT * FROM courses WHERE cid = {cid};")
        course = cursor.fetchall()[0]
        print(f"cid: {course[0]}, price: {course[1]}, pass_grade: {course[2]}, max_students: {course[3]}, certificates_added: 0, certificates_removed: 0")
        return
    cursor.execute("""SELECT e.uid
                    FROM enrollments e
                    WHERE e.cid = ?
                    AND e.role = 'Student' AND e.start_ts <= CURRENT_TIMESTAMP AND e.end_ts >= CURRENT_TIMESTAMP;""", (cid,)) 
    #get all students in course
    students = cursor.fetchall()
    certificates_added = 0;
    certificates_removed = 0;
    for s in students:
        uid = s[0]
        cursor.execute("""SELECT(
                            SELECT COUNT(DISTINCT cmp.mid || '-' || cmp.lid)
                            FROM completion cmp
                            WHERE cmp.uid = ? AND cmp.cid = ?
                        ) = (
                            SELECT COUNT(*)
                            FROM lessons l
                            WHERE l.cid = ?
                        ) AS all_completed;""", (uid, cid, cid))
        has_completed = cursor.fetchall()[0][0]
        #finds if student has certificate in this course
        cursor.execute("""SELECT COUNT(*) FROM certificates WHERE uid = ? and cid = ?;""", (uid, cid))
        has_certificate = cursor.fetchall()[0][0]
        if not has_completed:
            continue; #if not completed all lessons, no certificate given (or taken away as they couldn't have gotten one if they didn't complete everything)
        #find final grade
        cursor.execute("""SELECT 
                            SUM(g.grade * m.weight) / SUM(m.weight) AS final_grade
                            FROM grades g
                            JOIN modules m ON g.cid = m.cid AND g.mid = m.mid
                            WHERE g.uid = ? AND g.cid = ?
                                AND g.received_ts = (
                                  SELECT MAX(received_ts) 
                                    FROM grades g2
                                    WHERE g2.uid = g.uid AND g2.cid = g.cid AND g2.mid = g.mid
                        );""", (uid, cid))
        final_grade = cursor.fetchall()[0][0]
        if final_grade >= pass_grade and not has_certificate:
            cursor.execute("""INSERT INTO certificates (cid, uid, received_ts, final_grade)
                            VALUES (?, ?, CURRENT_TIMESTAMP, ?);""", (cid, uid, final_grade))
            certificates_added += 1
        elif final_grade < pass_grade and has_certificate:
            cursor.execute("""DELETE FROM certificates
                                WHERE cid = ? AND uid = ?;""", (cid, uid))
            certificates_removed += 1
    cursor.execute(f"SELECT * FROM courses WHERE cid = {cid};")
    course = cursor.fetchall()[0]
    print(f"cid: {course[0]}, price: {course[4]}, pass_grade: {course[5]}, max_students: {course[6]}, certificates_added: {certificates_added}, certificates_removed: {certificates_removed}")
    conn.commit()


def override_enroll(conn, user):
    uid = input("User ID of Student to Be Enrolled: ").strip()
    cid = input("Course ID of Course to Be Enrolled In: ").strip()
    cursor = conn.cursor()

    if(not uid.isnumeric() or not cid.isnumeric()):
        print("Invalid UID or CID")

    #finds if id is of a student
    cursor.execute("""SELECT COUNT(*) FROM users
                        WHERE uid = ? AND role = 'Student';""", (uid,))
    is_student = cursor.fetchall()[0][0]
    if not is_student:
        print("User ID does not exist or is not a student")
        return

    #finds if cid is valid
    cursor.execute("""SELECT COUNT(*) FROM courses
                        WHERE cid = ?;""", (cid,))
    is_course = cursor.fetchall()[0][0]
    if not is_course:
        print("Course ID does not exist")
        return

    #finds if instructor teaches this course
    cursor.execute("""SELECT COUNT(*) FROM enrollments
                        WHERE cid = ? AND uid = ?
                        AND CURRENT_TIMESTAMP BETWEEN start_ts AND end_ts""", (cid, user['uid']))
    teaches_course = cursor.fetchall()[0][0]
    if not teaches_course:
        print("You do not teach this course")
        return

    #finds if student is already enrolled
    cursor.execute("""SELECT COUNT(*) FROM enrollments
                        WHERE uid = ? AND cid = ? AND start_ts <= CURRENT_TIMESTAMP
                        AND end_ts >= CURRENT_TIMESTAMP;""", (uid, cid))
    is_enrolled = cursor.fetchall()[0][0]
    if is_enrolled:
        print("Already Enrolled")
        return
    #enroll student
    cursor.execute("""INSERT INTO enrollments (cid, uid, start_ts, end_ts, role)
                        VALUES (?, ?, CURRENT_TIMESTAMP, '9999-12-31 23:59:59', 'Student');""", (cid, uid))
    #insert payment
    cursor.execute("""INSERT INTO payments (uid, cid, ts, credit_card_no, expiry_date)
                        VALUES (?, ?, CURRENT_TIMESTAMP, '0000000000000000', '9999-12');""", (uid, cid))
    #summary
    cursor.execute("""SELECT e.cid, c.title AS course_title, e.uid, u.name AS student_name, e.start_ts
                        FROM enrollments e
                        JOIN courses c ON e.cid = c.cid
                        JOIN users u ON e.uid = u.uid
                        WHERE e.cid = ? AND e.uid = ?
                            AND e.role = 'Student'
                            AND e.start_ts <= CURRENT_TIMESTAMP
                            AND e.end_ts >= CURRENT_TIMESTAMP;""", (cid, uid))
    summary = cursor.fetchall()[0]
    print(f"cid: {summary[0]}, course_title: {summary[1]}, uid: {summary[2]}, student_name: {summary[3]}, start_ts: {summary[4]}")
    conn.commit();

def view_course_stats(conn, usr):
    cursor = conn.cursor()
    cursor.execute("""SELECT 
                c.cid,
                c.title,
                COUNT(e.uid) AS active_enrollment, --"Active_enrollment = number of active student enrollments"
                ROUND( --"completion_rate = percentage of actively enrolled students who have completed all lessons in the course"
                    100.0 * SUM(
                        CASE WHEN (
                            SELECT COUNT(DISTINCT cmp.mid || '-' || cmp.lid)
                            FROM completion cmp
                            WHERE cmp.uid = e.uid AND cmp.cid = c.cid
                        ) = (
                            SELECT COUNT(*)
                            FROM lessons l
                            WHERE l.cid = c.cid
                        ) THEN 1 ELSE 0 END 
                    ) / NULLIF(COUNT(e.uid), 0), 2
                ) AS completion_rate,
                ROUND(AVG(fg.final_grade), 2) AS average_final_grade
            FROM courses c
            JOIN enrollments e ON c.cid = e.cid 
                AND e.role = 'Student'
                AND e.start_ts <= CURRENT_TIMESTAMP
                AND e.end_ts >= CURRENT_TIMESTAMP
            LEFT JOIN (
                SELECT g.uid, g.cid,
                       SUM(g.grade * m.weight) / SUM(m.weight) AS final_grade
                FROM grades g
                JOIN modules m ON g.cid = m.cid AND g.mid = m.mid
                WHERE g.received_ts = (
                    SELECT MAX(g2.received_ts) FROM grades g2
                    WHERE g2.uid = g.uid AND g2.cid = g.cid AND g2.mid = g.mid
                )
                GROUP BY g.uid, g.cid
            ) fg ON fg.uid = e.uid AND fg.cid = c.cid
            WHERE EXISTS (
                SELECT 1 FROM enrollments 
                WHERE cid = c.cid 
                AND uid = ? 
                AND role = 'Instructor'
                AND start_ts <= CURRENT_TIMESTAMP
                AND end_ts >= CURRENT_TIMESTAMP

            )
            GROUP BY c.cid, c.title;""", (usr['uid'],))
    courses = cursor.fetchall()
    print("\n---Course Statistics---")
    for c in courses:
        print(f"cid: {c[0]}, title: {c[1]}, active_enrollment: {c[2]}, completion_rate: {c[3]}, average_final_grade: {c[4]}")
