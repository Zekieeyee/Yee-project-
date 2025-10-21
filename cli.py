#!/usr/bin/env python3
import argparse
from typing import List, Optional
import sqlite3
from db import ensure_initialized, get_connection, now_iso, get_db_path


def _print_table(headers: List[str], rows: List[List[object]]) -> None:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    def fmt_line(values: List[object]) -> str:
        return "  ".join(str(v).ljust(widths[i]) for i, v in enumerate(values))

    print(fmt_line(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt_line(row))


# Students commands

def add_student(name: str, email: str) -> None:
    ensure_initialized()
    with get_connection() as connection:
        try:
            connection.execute(
                "INSERT INTO students (name, email, created_at) VALUES (?, ?, ?)",
                (name, email, now_iso()),
            )
            print(f"Student added: {name} <{email}>")
        except sqlite3.IntegrityError as err:
            print(f"Error: could not add student ({err})")


def list_students() -> None:
    ensure_initialized()
    with get_connection(True) as connection:
        rows = list(connection.execute(
            "SELECT id, name, email, created_at FROM students ORDER BY id"
        ))
        if not rows:
            print("No students found.")
            return
        _print_table(["id", "name", "email", "created_at"], [list(r) for r in rows])


def show_student(student_id: Optional[int], email: Optional[str]) -> None:
    ensure_initialized()
    if (student_id is None) == (email is None):
        print("Error: provide exactly one of --id or --email")
        return
    query = "SELECT id, name, email, created_at FROM students WHERE "
    args: List[object]
    if student_id is not None:
        query += "id = ?"
        args = [student_id]
    else:
        query += "email = ?"
        args = [email]
    with get_connection(True) as connection:
        row = connection.execute(query, args).fetchone()
        if row is None:
            print("Student not found.")
            return
        _print_table(["id", "name", "email", "created_at"], [list(row)])


def delete_student(student_id: Optional[int], email: Optional[str]) -> None:
    ensure_initialized()
    if (student_id is None) == (email is None):
        print("Error: provide exactly one of --id or --email")
        return
    query = "DELETE FROM students WHERE "
    args: List[object]
    if student_id is not None:
        query += "id = ?"
        args = [student_id]
    else:
        query += "email = ?"
        args = [email]
    with get_connection() as connection:
        cur = connection.execute(query, args)
        if cur.rowcount == 0:
            print("Student not found.")
        else:
            print("Student deleted.")


# Courses commands

def add_course(code: str, title: str, capacity: int) -> None:
    ensure_initialized()
    with get_connection() as connection:
        try:
            connection.execute(
                "INSERT INTO courses (code, title, capacity, created_at) VALUES (?, ?, ?, ?)",
                (code, title, capacity, now_iso()),
            )
            print(f"Course added: {code} - {title} (capacity {capacity})")
        except sqlite3.IntegrityError as err:
            print(f"Error: could not add course ({err})")


def list_courses() -> None:
    ensure_initialized()
    with get_connection(True) as connection:
        rows = list(connection.execute(
            "SELECT id, code, title, capacity, created_at FROM courses ORDER BY id"
        ))
        if not rows:
            print("No courses found.")
            return
        _print_table(["id", "code", "title", "capacity", "created_at"], [list(r) for r in rows])


def show_course(course_id: Optional[int], code: Optional[str]) -> None:
    ensure_initialized()
    if (course_id is None) == (code is None):
        print("Error: provide exactly one of --id or --code")
        return
    query = "SELECT id, code, title, capacity, created_at FROM courses WHERE "
    args: List[object]
    if course_id is not None:
        query += "id = ?"
        args = [course_id]
    else:
        query += "code = ?"
        args = [code]
    with get_connection(True) as connection:
        row = connection.execute(query, args).fetchone()
        if row is None:
            print("Course not found.")
            return
        _print_table(["id", "code", "title", "capacity", "created_at"], [list(row)])


def delete_course(course_id: Optional[int], code: Optional[str]) -> None:
    ensure_initialized()
    if (course_id is None) == (code is None):
        print("Error: provide exactly one of --id or --code")
        return
    query = "DELETE FROM courses WHERE "
    args: List[object]
    if course_id is not None:
        query += "id = ?"
        args = [course_id]
    else:
        query += "code = ?"
        args = [code]
    with get_connection() as connection:
        cur = connection.execute(query, args)
        if cur.rowcount == 0:
            print("Course not found.")
        else:
            print("Course deleted.")


# Enrollment commands

def enroll_student(student_id: int, course_id: int) -> None:
    ensure_initialized()
    with get_connection() as connection:
        # check course capacity
        course = connection.execute(
            "SELECT id, capacity FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()
        if course is None:
            print("Error: course not found.")
            return
        current = connection.execute(
            "SELECT COUNT(*) AS c FROM enrollments WHERE course_id = ?",
            (course_id,),
        ).fetchone()[0]
        if current >= course["capacity"]:
            print("Error: course is full.")
            return
        # ensure student exists
        student = connection.execute(
            "SELECT id FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()
        if student is None:
            print("Error: student not found.")
            return
        try:
            connection.execute(
                "INSERT INTO enrollments (student_id, course_id, enrolled_at) VALUES (?, ?, ?)",
                (student_id, course_id, now_iso()),
            )
            print("Enrolled successfully.")
        except sqlite3.IntegrityError:
            print("Error: student already enrolled in this course.")


def drop_enrollment(student_id: int, course_id: int) -> None:
    ensure_initialized()
    with get_connection() as connection:
        cur = connection.execute(
            "DELETE FROM enrollments WHERE student_id = ? AND course_id = ?",
            (student_id, course_id),
        )
        if cur.rowcount == 0:
            print("Enrollment not found.")
        else:
            print("Enrollment dropped.")


def list_enrollments(student_id: Optional[int], course_id: Optional[int]) -> None:
    ensure_initialized()
    with get_connection(True) as connection:
        base = (
            "SELECT e.student_id, s.name AS student_name, e.course_id, c.code AS course_code, e.enrolled_at "
            "FROM enrollments e "
            "JOIN students s ON s.id = e.student_id "
            "JOIN courses c ON c.id = e.course_id "
        )
        args: List[object] = []
        if student_id is not None and course_id is not None:
            base += "WHERE e.student_id = ? AND e.course_id = ? "
            args = [student_id, course_id]
        elif student_id is not None:
            base += "WHERE e.student_id = ? "
            args = [student_id]
        elif course_id is not None:
            base += "WHERE e.course_id = ? "
            args = [course_id]
        base += "ORDER BY e.enrolled_at"
        rows = list(connection.execute(base, args))
        if not rows:
            print("No enrollments found.")
            return
        _print_table(
            ["student_id", "student_name", "course_id", "course_code", "enrolled_at"],
            [list(r) for r in rows],
        )


# CLI wiring

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mini Enrollment System CLI (SQLite-backed)",
    )
    sub = parser.add_subparsers(dest="command")

    # students
    p_students = sub.add_parser("students", help="Manage students")
    sub_students = p_students.add_subparsers(dest="action")

    p_stu_add = sub_students.add_parser("add", help="Add a student")
    p_stu_add.add_argument("--name", required=True)
    p_stu_add.add_argument("--email", required=True)

    sub_students.add_parser("list", help="List students")

    p_stu_show = sub_students.add_parser("show", help="Show a student")
    g = p_stu_show.add_mutually_exclusive_group(required=True)
    g.add_argument("--id", type=int)
    g.add_argument("--email")

    p_stu_del = sub_students.add_parser("delete", help="Delete a student")
    g = p_stu_del.add_mutually_exclusive_group(required=True)
    g.add_argument("--id", type=int)
    g.add_argument("--email")

    # courses
    p_courses = sub.add_parser("courses", help="Manage courses")
    sub_courses = p_courses.add_subparsers(dest="action")

    p_crs_add = sub_courses.add_parser("add", help="Add a course")
    p_crs_add.add_argument("--code", required=True)
    p_crs_add.add_argument("--title", required=True)
    p_crs_add.add_argument("--capacity", type=int, required=True)

    sub_courses.add_parser("list", help="List courses")

    p_crs_show = sub_courses.add_parser("show", help="Show a course")
    g = p_crs_show.add_mutually_exclusive_group(required=True)
    g.add_argument("--id", type=int)
    g.add_argument("--code")

    p_crs_del = sub_courses.add_parser("delete", help="Delete a course")
    g = p_crs_del.add_mutually_exclusive_group(required=True)
    g.add_argument("--id", type=int)
    g.add_argument("--code")

    # enrollments
    p_enr = sub.add_parser("enrollments", help="Manage enrollments")
    sub_enr = p_enr.add_subparsers(dest="action")

    p_enroll = sub_enr.add_parser("enroll", help="Enroll a student in a course")
    p_enroll.add_argument("--student-id", type=int, required=True)
    p_enroll.add_argument("--course-id", type=int, required=True)

    p_drop = sub_enr.add_parser("drop", help="Drop an enrollment")
    p_drop.add_argument("--student-id", type=int, required=True)
    p_drop.add_argument("--course-id", type=int, required=True)

    p_list = sub_enr.add_parser("list", help="List enrollments")
    p_list.add_argument("--student-id", type=int)
    p_list.add_argument("--course-id", type=int)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "students":
        if args.action == "add":
            add_student(args.name, args.email)
        elif args.action == "list":
            list_students()
        elif args.action == "show":
            show_student(args.id, args.email)
        elif args.action == "delete":
            delete_student(args.id, args.email)
        else:
            parser.print_help()
    elif args.command == "courses":
        if args.action == "add":
            add_course(args.code, args.title, args.capacity)
        elif args.action == "list":
            list_courses()
        elif args.action == "show":
            show_course(args.id, args.code)
        elif args.action == "delete":
            delete_course(args.id, args.code)
        else:
            parser.print_help()
    elif args.command == "enrollments":
        if args.action == "enroll":
            enroll_student(args["student_id"] if isinstance(args, dict) else args.student_id, args["course_id"] if isinstance(args, dict) else args.course_id)
        elif args.action == "drop":
            drop_enrollment(args.student_id, args.course_id)
        elif args.action == "list":
            list_enrollments(args.student_id, args.course_id)
        else:
            parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
