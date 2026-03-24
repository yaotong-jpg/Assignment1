-- CMPUT291 W2026 Mini Project I

-- Drop tables if they exist
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS certificates;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS completion;
DROP TABLE IF EXISTS lessons;
DROP TABLE IF EXISTS modules;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS users;

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL CHECK(role IN ('Student', 'Instructor', 'Admin')),
    pwd TEXT NOT NULL
);

-- ============================================================================
-- COURSES TABLE
-- ============================================================================
CREATE TABLE courses (
    cid INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price REAL NOT NULL CHECK(price >= 0),
    pass_grade REAL NOT NULL CHECK(pass_grade >= 0 AND pass_grade <= 100),
    max_students INTEGER NOT NULL CHECK(max_students > 0)
);

-- ============================================================================
-- ENROLLMENTS TABLE
-- ============================================================================
-- Stores enrollment records for students and instructors in courses
-- A student can have multiple enrollments in the same course over time
-- Active enrollment: current timestamp is between start_ts and end_ts AND role = 'Student'
-- PRIMARY KEY: (cid, uid, start_ts) allows multiple enrollments but ensures uniqueness per enrollment
CREATE TABLE enrollments (
    cid INTEGER NOT NULL,
    uid INTEGER NOT NULL,
    start_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_ts TIMESTAMP NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Student', 'Instructor')),
    PRIMARY KEY (cid, uid, start_ts),
    FOREIGN KEY (cid) REFERENCES courses(cid) ON DELETE CASCADE,
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
);

-- ============================================================================
-- MODULES TABLE
-- ============================================================================
CREATE TABLE modules (
    cid INTEGER NOT NULL,
    mid INTEGER NOT NULL,
    name TEXT NOT NULL,
    summary TEXT,
    weight REAL NOT NULL CHECK(weight >= 0),
    PRIMARY KEY (cid, mid),
    FOREIGN KEY (cid) REFERENCES courses(cid) ON DELETE CASCADE
);

-- ============================================================================
-- LESSONS TABLE
-- ============================================================================
CREATE TABLE lessons (
    cid INTEGER NOT NULL,
    mid INTEGER NOT NULL,
    lid INTEGER NOT NULL,
    title TEXT NOT NULL,
    duration INTEGER NOT NULL CHECK(duration >= 0),
    content TEXT,
    PRIMARY KEY (cid, mid, lid),
    FOREIGN KEY (cid, mid) REFERENCES modules(cid, mid) ON DELETE CASCADE
);

-- ============================================================================
-- COMPLETION TABLE
-- ============================================================================
-- Tracks lesson completion by students
-- A student can complete the same lesson multiple times across different enrollments
-- PRIMARY KEY: (uid, cid, mid, lid, ts) allows tracking completion per enrollment period
CREATE TABLE completion (
    uid INTEGER NOT NULL,
    cid INTEGER NOT NULL,
    mid INTEGER NOT NULL,
    lid INTEGER NOT NULL,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (uid, cid, mid, lid, ts),
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (cid, mid, lid) REFERENCES lessons(cid, mid, lid) ON DELETE CASCADE
);

-- ============================================================================
-- GRADES TABLE
-- ============================================================================
-- Stores module grades for students
-- A student can receive multiple grades for the same module across different enrollments
-- PRIMARY KEY: (uid, cid, mid, received_ts) allows multiple grades per module over time
CREATE TABLE grades (
    uid INTEGER NOT NULL,
    cid INTEGER NOT NULL,
    mid INTEGER NOT NULL,
    received_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    grade REAL NOT NULL CHECK(grade >= 0 AND grade <= 100),
    PRIMARY KEY (uid, cid, mid, received_ts),
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (cid, mid) REFERENCES modules(cid, mid) ON DELETE CASCADE
);

-- ============================================================================
-- CERTIFICATES TABLE
-- ============================================================================
-- Stores certificates earned by students for courses
-- A student can earn multiple certificates for the same course across different enrollments
-- PRIMARY KEY: (cid, uid, received_ts) allows multiple certificates over time
CREATE TABLE certificates (
    cid INTEGER NOT NULL,
    uid INTEGER NOT NULL,
    received_ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    final_grade REAL NOT NULL CHECK(final_grade >= 0 AND final_grade <= 100),
    PRIMARY KEY (cid, uid, received_ts),
    FOREIGN KEY (cid) REFERENCES courses(cid) ON DELETE CASCADE,
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE
);

-- ============================================================================
-- PAYMENTS TABLE
-- ============================================================================
-- Stores payment records for course enrollments
-- A student can make multiple payments for the same course (multiple enrollments)
-- PRIMARY KEY: (uid, cid, ts) ensures unique payment records
CREATE TABLE payments (
    uid INTEGER NOT NULL,
    cid INTEGER NOT NULL,
    ts TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    credit_card_no TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    PRIMARY KEY (uid, cid, ts),
    FOREIGN KEY (uid) REFERENCES users(uid) ON DELETE CASCADE,
    FOREIGN KEY (cid) REFERENCES courses(cid) ON DELETE CASCADE
);

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

PRAGMA foreign_keys = ON;

DELETE FROM payments;
DELETE FROM certificates;
DELETE FROM grades;
DELETE FROM completion;
DELETE FROM lessons;
DELETE FROM modules;
DELETE FROM enrollments;
DELETE FROM courses;
DELETE FROM users;

-- USERS
-- Space and punctuation are allowed in the name field.
-- Different email postfix
INSERT INTO users(name,email,role,pwd) VALUES
  ('Alice','alice@ualberta.ca','Student','alicepw'),
  ('Bob','bob@gmail.com','Student','bobpw'),
  ('Prof. Smith','prof.smith@gmail.com','Instructor','smithpw'),
  ('Albert Gyamfi','albert@ualberta.ca','Instructor','albertpw'),
  ('Admin One','admin@gmail.com','Admin','adminpw');

-- COURSES
-- Different course prices such as zero, int, float...
INSERT INTO courses(title,description,category,price,pass_grade,max_students) VALUES
  ('Intro to Databases','SQL basics, joins, aggregation, constraints.','DB',0.00,60,2),
  ('Data Structures','Lists, trees, hashing, complexity.','Systems',40,55,80),
  ('Web Dev Foundations','HTTP, REST, templating, security basics.','Web',29.99,60,120),
  ('Machine Learning 101','Regression, classification, model selection.','AI',99.99,65,60),
  ('Operating Systems','Processes, threads, virtual memory.','Systems', 80,60,70),
  ('Computer Networks','TCP/IP, routing, congestion control.','Systems',23,60,90),
  ('Software Testing','Unit/integration testing, CI, coverage.','Web',44,55,100),
  ('Data Visualization','Charts, dashboards, storytelling.','AI',20,50,100),
  ('Security Basics','Threats, crypto basics, auth.','Systems',59.50,60,40),
  ('Advanced SQL','Window functions, query plans, indexing.','DB',8.34,70,30),
  ('NLP Primer','Tokenization, embeddings, transformers.','AI',109.65,65,35),
  ('Mobile App Dev','Android basics, storage, networking.','Web',59,60,50),
  ('Advanced Database Systems','Advanced SQL, query plans, indexing.','DB',8.34,70,30),
  ('Data Mining','Clustering, association rules, decision trees.','AI',109.65,65,35),
  ('Data Analytics','Data visualization, storytelling, dashboarding.','AI',109.65,65,35),
  ('Security in Databases','Threats, crypto basics, auth.','Systems',59.50,60,40);

-- ENROLLMENTS
INSERT INTO enrollments(cid,uid,start_ts,end_ts,role) VALUES
  (1,1,datetime('now','-40 days'),datetime('now','-40 days','+1 year'),'Student'),
  (2,1,datetime('now','-35 days'),datetime('now','-35 days','+1 year'),'Student'),
  (3,1,datetime('now','-30 days'),datetime('now','-30 days','+1 year'),'Student'),
  (4,1,datetime('now','-25 days'),datetime('now','-25 days','+1 year'),'Student'),
  (5,1,datetime('now','-20 days'),datetime('now','-20 days','+1 year'),'Student'),
  (6,1,datetime('now','-15 days'),datetime('now','-15 days','+1 year'),'Student'),
  (7,1,datetime('now','-10 days'),datetime('now','-10 days','+1 year'),'Student'),
  (8,1,datetime('now','-5 days'),datetime('now','-5 days','+1 year'),'Student'),
  (1,2,datetime('now','-28 days'),datetime('now','-28 days','+1 year'),'Student'),
  (2,2,datetime('now','-24 days'),datetime('now','-24 days','+1 year'),'Student'),
  (3,2,datetime('now','-22 days'),datetime('now','-22 days','+1 year'),'Student'),
  (4,2,datetime('now','-18 days'),datetime('now','-18 days','+1 year'),'Student'),
  (9,2,datetime('now','-12 days'),datetime('now','-12 days','+1 year'),'Student'),
  (10,2,datetime('now','-8 days'),datetime('now','-8 days','+1 year'),'Student'),
  (11,2,datetime('now','-420 days'),datetime('now','-420 days','+1 year'),'Student'),
  (1,3,datetime('now','-60 days'),datetime('now','-60 days','+1 year'),'Instructor'),
  (2,3,datetime('now','-58 days'),datetime('now','-58 days','+1 year'),'Instructor'),
  (3,3,datetime('now','-56 days'),datetime('now','-56 days','+1 year'),'Instructor'),
  (4,3,datetime('now','-54 days'),datetime('now','-54 days','+1 year'),'Instructor'),
  (5,3,datetime('now','-52 days'),datetime('now','-52 days','+1 year'),'Instructor'),
  (6,3,datetime('now','-50 days'),datetime('now','-50 days','+1 year'),'Instructor'),
  (7,4,datetime('now','-48 days'),datetime('now','-48 days','+1 year'),'Instructor'),
  (8,4,datetime('now','-46 days'),datetime('now','-46 days','+1 year'),'Instructor'),
  (9,4,datetime('now','-44 days'),datetime('now','-44 days','+1 year'),'Instructor'),
  (10,4,datetime('now','-42 days'),datetime('now','-42 days','+1 year'),'Instructor'),
  (11,4,datetime('now','-40 days'),datetime('now','-40 days','+1 year'),'Instructor'),
  (12,4,datetime('now','-38 days'),datetime('now','-38 days','+1 year'),'Instructor');

-- MODULES
INSERT INTO modules(cid,mid,name,summary,weight) VALUES
  (1,1,'Relational Model','Keys, constraints, relational algebra',30),
  (1,2,'SQL','Filtering, joins, grouping',50),
  (1,3,'Views & Triggers','Views, triggers, integrity',20),
  (2,1,'Basics','Core concepts for course 2.',50),
  (2,2,'Practice','Hands-on exercises for course 2.',50),
  (3,1,'Basics','Core concepts for course 3.',50),
  (3,2,'Practice','Hands-on exercises for course 3.',50),
  (4,1,'Basics','Core concepts for course 4.',50),
  (4,2,'Practice','Hands-on exercises for course 4.',50),
  (5,1,'Basics','Core concepts for course 5.',50),
  (5,2,'Practice','Hands-on exercises for course 5.',50),
  (6,1,'Basics','Core concepts for course 6.',50),
  (6,2,'Practice','Hands-on exercises for course 6.',50),
  (7,1,'Basics','Core concepts for course 7.',50),
  (7,2,'Practice','Hands-on exercises for course 7.',50),
  (8,1,'Basics','Core concepts for course 8.',50),
  (8,2,'Practice','Hands-on exercises for course 8.',50),
  (9,1,'Basics','Core concepts for course 9.',50),
  (9,2,'Practice','Hands-on exercises for course 9.',50),
  (10,1,'Basics','Core concepts for course 10.',50),
  (10,2,'Practice','Hands-on exercises for course 10.',50),
  (11,1,'Basics','Core concepts for course 11.',50),
  (11,2,'Practice','Hands-on exercises for course 11.',50),
  (12,1,'Basics','Core concepts for course 12.',50),
  (12,2,'Practice','Hands-on exercises for course 12.',50);

-- LESSONS
INSERT INTO lessons(cid,mid,lid,title,duration,content) VALUES
  (1,1,1,'Lesson 1: Relational Concepts1',11,'Content for C1 M1 L1.'),
  (1,1,2,'Lesson 2: Relational Concepts2',12,'Content for C1 M1 L2.'),
  (1,1,3,'Lesson 3: Relational Concepts3',13,'Content for C1 M1 L3.'),
  (1,1,4,'Lesson 4: Relational Concepts4',14,'Content for C1 M1 L4.'),
  (1,2,1,'C1 M2 Lesson 1',17,'Content for C1 M2 L1.'),
  (1,2,2,'C1 M2 Lesson 2',19,'Content for C1 M2 L2.'),
  (1,2,3,'C1 M2 Lesson 3',21,'Content for C1 M2 L3.'),
  (1,3,1,'C1 M3 Lesson 1',17,'Content for C1 M3 L1.'),
  (1,3,2,'C1 M3 Lesson 2',19,'Content for C1 M3 L2.'),
  (1,3,3,'C1 M3 Lesson 3',21,'Content for C1 M3 L3.'),
  (2,1,1,'C2 M1 Lesson 1',13,'Content for C2 M1 L1.'),
  (2,1,2,'C2 M1 Lesson 2',14,'Content for C2 M1 L2.'),
  (2,2,1,'C2 M2 Lesson 1',13,'Content for C2 M2 L1.'),
  (2,2,2,'C2 M2 Lesson 2',14,'Content for C2 M2 L2.'),
  (3,1,1,'C3 M1 Lesson 1',13,'Content for C3 M1 L1.'),
  (3,1,2,'C3 M1 Lesson 2',14,'Content for C3 M1 L2.'),
  (3,2,1,'C3 M2 Lesson 1',13,'Content for C3 M2 L1.'),
  (3,2,2,'C3 M2 Lesson 2',14,'Content for C3 M2 L2.'),
  (4,1,1,'C4 M1 Lesson 1',13,'Content for C4 M1 L1.'),
  (4,1,2,'C4 M1 Lesson 2',14,'Content for C4 M1 L2.'),
  (4,2,1,'C4 M2 Lesson 1',13,'Content for C4 M2 L1.'),
  (4,2,2,'C4 M2 Lesson 2',14,'Content for C4 M2 L2.'),
  (5,1,1,'C5 M1 Lesson 1',13,'Content for C5 M1 L1.'),
  (5,1,2,'C5 M1 Lesson 2',14,'Content for C5 M1 L2.'),
  (5,2,1,'C5 M2 Lesson 1',13,'Content for C5 M2 L1.'),
  (5,2,2,'C5 M2 Lesson 2',14,'Content for C5 M2 L2.'),
  (6,1,1,'C6 M1 Lesson 1',13,'Content for C6 M1 L1.'),
  (6,1,2,'C6 M1 Lesson 2',14,'Content for C6 M1 L2.'),
  (6,2,1,'C6 M2 Lesson 1',13,'Content for C6 M2 L1.'),
  (6,2,2,'C6 M2 Lesson 2',14,'Content for C6 M2 L2.'),
  (7,1,1,'C7 M1 Lesson 1',13,'Content for C7 M1 L1.'),
  (7,1,2,'C7 M1 Lesson 2',14,'Content for C7 M1 L2.'),
  (7,2,1,'C7 M2 Lesson 1',13,'Content for C7 M2 L1.'),
  (7,2,2,'C7 M2 Lesson 2',14,'Content for C7 M2 L2.'),
  (8,1,1,'C8 M1 Lesson 1',13,'Content for C8 M1 L1.'),
  (8,1,2,'C8 M1 Lesson 2',14,'Content for C8 M1 L2.'),
  (8,2,1,'C8 M2 Lesson 1',13,'Content for C8 M2 L1.'),
  (8,2,2,'C8 M2 Lesson 2',14,'Content for C8 M2 L2.'),
  (9,1,1,'C9 M1 Lesson 1',13,'Content for C9 M1 L1.'),
  (9,1,2,'C9 M1 Lesson 2',14,'Content for C9 M1 L2.'),
  (9,2,1,'C9 M2 Lesson 1',13,'Content for C9 M2 L1.'),
  (9,2,2,'C9 M2 Lesson 2',14,'Content for C9 M2 L2.'),
  (10,1,1,'C10 M1 Lesson 1',13,'Content for C10 M1 L1.'),
  (10,1,2,'C10 M1 Lesson 2',14,'Content for C10 M1 L2.'),
  (10,2,1,'C10 M2 Lesson 1',13,'Content for C10 M2 L1.'),
  (10,2,2,'C10 M2 Lesson 2',14,'Content for C10 M2 L2.'),
  (11,1,1,'C11 M1 Lesson 1',13,'Content for C11 M1 L1.'),
  (11,1,2,'C11 M1 Lesson 2',14,'Content for C11 M1 L2.'),
  (11,2,1,'C11 M2 Lesson 1',13,'Content for C11 M2 L1.'),
  (11,2,2,'C11 M2 Lesson 2',14,'Content for C11 M2 L2.'),
  (12,1,1,'C12 M1 Lesson 1',13,'Content for C12 M1 L1.'),
  (12,1,2,'C12 M1 Lesson 2',14,'Content for C12 M1 L2.'),
  (12,2,1,'C12 M2 Lesson 1',13,'Content for C12 M2 L1.'),
  (12,2,2,'C12 M2 Lesson 2',14,'Content for C12 M2 L2.');

-- COMPLETION (Alice completes some lessons in C1 M1 and C1 M2)
INSERT INTO completion(uid,cid,mid,lid,ts) VALUES
  (1,1,1,1,datetime('now','-72 hours')),
  (1,1,1,2,datetime('now','-60 hours')),
  (1,1,1,3,datetime('now','-48 hours')),
  (1,1,1,4,datetime('now','-36 hours')),
  (1,1,2,1,datetime('now','-30 hours')),
  (1,1,2,2,datetime('now','-24 hours')),
  (1,1,2,3,datetime('now','-22 hours')),
  (1,1,3,1,datetime('now','-17 hours')),
  (1,1,3,2,datetime('now','-14 hours')),
  (1,1,3,3,datetime('now','-10 hours')),
  (2,1,1,1,datetime('now','-20 hours')),
  (2,1,1,2,datetime('now','-19 hours')),
  (2,1,1,4,datetime('now','-18 hours')),
  (2,2,1,1,datetime('now','-90 hours')),
  (2,2,2,1,datetime('now','-84 hours'));

-- GRADES (Not sure should we add failed grades?)
INSERT INTO grades(uid,cid,mid,received_ts,grade) VALUES
  (1,1,1,datetime('now','-20 days'),78.88),
  (1,1,2,datetime('now','-18 days'),82),
  (1,1,3,datetime('now','-16 days'),75.52),
  (2,1,1,datetime('now','-12 days'),61),
  (2,1,2,datetime('now','-10 days'),59),
  (1,4,1,datetime('now','-9 days'),90),
  (1,4,2,datetime('now','-7 days'),85),
  (2,1,3,datetime('now','-9 days'),67),
  (2,2,1,datetime('now','-6 days'),80),
  (2,2,2,datetime('now','-5 days'),70);

-- CERTIFICATES
INSERT INTO certificates(cid,uid,received_ts,final_grade) VALUES
  (4,1,datetime('now','-6 days'),87.5),
  (2,2,datetime('now','-4 days'),75.0);

-- PAYMENTS (enough to test pagination: Alice 8 payments, Bob 6 payments)
INSERT INTO payments(uid,cid,ts,credit_card_no,expiry_date) VALUES
  (1,1,datetime('now','-1 days'),'4111111111111001',date('now','+2 years')),
  (1,2,datetime('now','-2 days'),'4111111111111002',date('now','+2 years')),
  (1,3,datetime('now','-3 days'),'4111111111111003',date('now','+2 years')),
  (1,4,datetime('now','-4 days'),'4111111111111004',date('now','+2 years')),
  (1,5,datetime('now','-5 days'),'4111111111111005',date('now','+2 years')),
  (1,6,datetime('now','-6 days'),'4111111111111006',date('now','+2 years')),
  (1,7,datetime('now','-7 days'),'4111111111111007',date('now','+2 years')),
  (1,8,datetime('now','-8 days'),'4111111111111008',date('now','+2 years')),
  (2,1,datetime('now','-2 days'),'4111111111112001',date('now','+2 years')),
  (2,2,datetime('now','-4 days'),'4111111111112002',date('now','+2 years')),
  (2,3,datetime('now','-6 days'),'4111111111112003',date('now','+2 years')),
  (2,4,datetime('now','-8 days'),'4111111111112004',date('now','+2 years')),
  (2,9,datetime('now','-3 days'),'4111111111112009',date('now','+2 years')),
  (2,10,datetime('now','-5 days'),'4111111111112010',date('now','+2 years'));
