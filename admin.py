import sys
from datetime import datetime

def admin_menu(conn, user):
    while True:
        print("\n---ADMIN MENU---")
        print("1. Platform Statistics")
        print("2. Logout")
        print("3. Exit")
        choice = input("Select an option: ").strip()
        if choice == '1':
            platform_statistics(conn)
        elif choice == '2':
            print("Logged out successfully.")
            break
        elif choice == '3':
            print("Goodbye!")
            sys.exit()
        else:
            print("Fail: Invalid option.")

def paginate(results, page, page_size=5):
    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = results[start:end]
    has_prev = page > 1
    has_next = end < total
    return page_data, has_prev, has_next


def platform_statistics(conn):
    while True:
        print("\n---PLATFORM STATISTICS---")
        print("1. Top 5 Courses by Enrollment")
        print("2. Payment Counts per Course")
        print("3. Back")
        choice = input("Select an option: ").strip()
        if choice == '1':
            view_top5_courses(conn)
        elif choice == '2':
            view_payment_counts(conn)
        elif choice == '3':
            break
        else:
            print("Fail: Invalid option.")


def view_top5_courses(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.cid,
            c.title,
            COUNT(e.uid) AS active_enrollment
        FROM courses c
        LEFT JOIN enrollments e
            ON c.cid = e.cid
            AND e.role = 'Student'
            AND e.start_ts <= CURRENT_TIMESTAMP
            AND e.end_ts   >= CURRENT_TIMESTAMP
        GROUP BY c.cid, c.title
        HAVING active_enrollment >= (
            SELECT MIN(active_enrollment) FROM (
                SELECT COUNT(e2.uid) AS active_enrollment
                FROM courses c2
                LEFT JOIN enrollments e2
                    ON c2.cid = e2.cid
                    AND e2.role = 'Student'
                    AND e2.start_ts <= CURRENT_TIMESTAMP
                    AND e2.end_ts   >= CURRENT_TIMESTAMP
                GROUP BY c2.cid
                ORDER BY active_enrollment DESC
                LIMIT 5
            )
        )
        ORDER BY active_enrollment DESC
    """)
    rows = cursor.fetchall()

    print("\n---Top 5 Courses by Active Enrollment---")
    if not rows:
        print("Fail: No course data found.")
    else:
        for r in rows:
            print(f"cid: {r['cid']}, title: {r['title']}, active_enrollment: {r['active_enrollment']}")

def view_payment_counts(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.cid,
            c.title,
            COUNT(p.ts) AS payment_count
        FROM courses c
        LEFT JOIN payments p ON c.cid = p.cid
        GROUP BY c.cid, c.title
        ORDER BY payment_count DESC
    """)
    rows = cursor.fetchall()

    page = 1
    while True:
        page_rows, has_prev, has_next = paginate(rows, page)

        print(f"\n---Payment Counts per Course (Page {page})---")
        if not page_rows:
            print("Fail: No course data found.")
        else:
            for r in page_rows:
                print(f"cid: {r['cid']}, title: {r['title']}, payment_count: {r['payment_count']}")

        print("\n---Navigation---")
        if has_prev:
            print("P: Previous Page")
        if has_next:
            print("N: Next Page")
        print("Q: Back to Menu")

        cmd = input("Choice: ").strip().upper()
        if cmd == 'Q':
            break
        elif cmd == 'P':
            if has_prev:
                page -= 1
            else:
                print("Notice: Already on the first page.")
        elif cmd == 'N':
            if has_next:
                page += 1
            else:
                print("Notice: Already on the last page.")
        else:
            print("Fail: Invalid option. Please enter P, N, or Q.")
