import sqlite3

import pytest
from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get("/welcome")
    assert response.status_code == 200


def test_add_question(client):
    con = sqlite3.connect('database.db')
    cursor = con.cursor()
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM quiz")
    con.commit()
    cursor.execute("INSERT INTO quiz (quiz_name) VALUES (?)", ("Sample Quiz",))
    con.commit()
    con.close()

    con = sqlite3.connect('database.db')
    cursor = con.cursor()
    response = client.post("/add/1",data={"question": "Sample Quest?", "answer": "Sample Answer"})
    assert response.status_code == 200
    cursor.execute("SELECT * FROM questions WHERE question = ?", ('Sample Quest?',))
    con.close()


def test_change_question(client):
    con = sqlite3.connect('database.db')
    cursor = con.cursor()
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM quiz")
    con.commit()
    cursor.execute("INSERT INTO quiz (quiz_name) VALUES (?)", ("Sample Quiz",))
    quiz_id = cursor.lastrowid
    cursor.execute("INSERT INTO questions (quiz_id, question, answer) VALUES (?, ?, ?)",
                   (quiz_id, "Old Question", "Old Answer"))
    con.commit()
    question_id = cursor.lastrowid
    response = client.post(f"/change/{quiz_id}/{question_id}",
                           data={"question": "new quest?", "answer": "new answer"})
    assert response.status_code == 200
    cursor.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
    new_ques = cursor.fetchone()
    assert new_ques[1] == "new quest?"
    assert new_ques[3] == "new answer"
    con.close()

def test_delete_question(client):
    con = sqlite3.connect('database.db')
    cursor = con.cursor()
    cursor.execute("DELETE FROM questions")
    cursor.execute("DELETE FROM quiz")
    con.commit()
    cursor.execute("INSERT INTO quiz (quiz_name) VALUES (?)", ("Sample Quiz",))
    quiz_id = cursor.lastrowid
    cursor.execute("INSERT INTO questions (quiz_id, question, answer) VALUES (?, ?, ?)",
                   (quiz_id, "Question", "Answer"))
    con.commit()
    question_id = cursor.lastrowid
    response = client.post(f"/delete/{quiz_id}/{question_id}")
    assert response.status_code == 302
    cursor.execute("SELECT * FROM questions WHERE question_id = ?", (question_id,))
    delete_question = cursor.fetchone()
    con.close()
    assert delete_question is None
def test_view_question(client):
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    cursor.execute("INSERT OR IGNORE INTO questions (quiz_id, question, answer) VALUES (?,?,?)",
                   (1, "How r u?", "Okay"))
    connection.commit()
    connection.close()
    response = client.get("/view_questions/1")
    assert response.status_code == 200
    assert b"How r u?" in response.data


def test_create_quiz(client):
    response = client.post("/create",data={"quiz_name": "new_quiz"})
    assert response.status_code == 200
    connection = sqlite3.connect("database.db",)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM quiz WHERE quiz_name = ?", ("new_quiz",))
    result = cursor.fetchone()
    connection.close()
    assert result is not None

def test_crud_question(client):
    response = client.get("/crud_options/1")
    assert response.status_code == 200