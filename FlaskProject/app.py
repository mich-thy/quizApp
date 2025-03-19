from urllib import request

from flask import Flask, request, render_template_string, redirect, render_template
import sqlite3

app = Flask(__name__)

# initializes databases upon startup
def init_db():
    connect = sqlite3.connect('database.db')
    connect.execute("CREATE TABLE IF NOT EXISTS quiz (id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_name TEXT "
                    "NOT NULL UNIQUE)")
    connect.execute('CREATE TABLE IF NOT EXISTS questions(quiz_id INTEGER NOT NULL, question TEXT NOT NULL,question_id INTEGER PRIMARY KEY,'
                    'answer TEXT NOT NULL,UNIQUE(quiz_id, question),FOREIGN KEY (quiz_id) REFERENCES quiz(id))')
    connect.commit()
    connect.close()
init_db()

# starts homepage where users can select/create a quiz set
@app.route('/welcome',methods=['GET', 'POST'])
@app.route('/',methods=['GET', 'POST'])
def welcome():
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'select':  #if users want to select an existing set
            return redirect('/select')
        else:  # is users want to create a new set
            return redirect('/create')

    return render_template("welcome.html")

# page where users can add questions and answers to their quiz
@app.route('/add/<quiz_id>', methods=['GET','POST'])
def add_question(quiz_id):
    if request.method == 'POST':
        question = request.form.get('question').strip().lower()
        answer = request.form.get('answer').strip().lower()
        if question and answer: #if user fills both question and answer boxes
            connect = sqlite3.connect('database.db')
            cursor = connect.cursor()
            try:
                cursor.execute("INSERT INTO questions (quiz_id, question, answer) VALUES (?, ?, ?)", #
                               (quiz_id, question, answer))
                connect.commit()
            except sqlite3.IntegrityError: # if question is not unique, raise error
                connect.close()
                return render_template('add.html',alert="Question is not unique",quiz_id=str(quiz_id))
            # alert user that q&a are added properly
            return render_template('add.html',alert="Question and answer added successfully",quiz_id=str(quiz_id))
    return render_template('add.html',quiz_id=str(quiz_id))

# users can update an existing question or answer
@app.route('/change/<quiz_id>/<question_id>', methods=['GET','POST'])
def change_question(quiz_id, question_id):
    if request.method == 'POST':
        question = request.form.get('question').strip()
        answer = request.form.get('answer').strip()
        connect = sqlite3.connect('database.db')
        cursor = connect.cursor()

        if question: # if the user wants to update the question
            cursor.execute("UPDATE questions SET question = ? WHERE question_id = ?",(question, question_id))
            connect.commit()
        if answer: # if the user want to update the answer
            cursor.execute("""UPDATE questions SET answer = ? WHERE question_id = ?""",(answer,question_id))
            connect.commit()
        connect.close()
        if not question and not answer: # if the user did not fill out either blanks, alert the user
            return render_template('change.html',alert="Enter a Question or Answer",quiz_id=str(quiz_id))
        # question and answer are successfully changed
        return render_template('change.html',alert='Question or Answer successfully updated',quiz_id=str(quiz_id))
    return render_template('change.html',quiz_id=str(quiz_id))

# the selected question and answer are deleted
@app.route('/delete/<quiz_id>/<question_id>', methods=['GET','POST'])
def delete_question(quiz_id,question_id):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    # see if the question to delete exists in the database
    outcome = cursor.execute("SELECT EXISTS(SELECT 1 FROM questions WHERE question_id = ?) AS row_exists", (question_id,))
    if outcome: #if question exists --> delete
        cursor.execute("DELETE FROM questions WHERE question_id = ?", (question_id,))
        connect.commit()
    else:
        return "question not found" #question does not exist
    connect.close()
    return redirect(f'/view_questions/{quiz_id}') # refreshes page to show updated quiz set

# shows all the questions in quiz set to view
# users may delete a question or update on this page
@app.route('/view_questions/<quiz_id>', methods=['GET'])
def view_questions(quiz_id):
    connect = sqlite3.connect('database.db')
    cursor = connect.cursor()
    # selects all the questions from the quiz to display
    cursor.execute("SELECT * FROM questions WHERE quiz_id = ?", (int(quiz_id),))
    all_questions = cursor.fetchall() # fetches all the questions in quiz in a tuple
    connect.close()
    return render_template('view.html',all_questions=all_questions,quiz_id=str(quiz_id))

# users may select an existing quiz to work on
@app.route('/select',methods=['GET', 'POST'])
def select_quiz():
    # require ensures the box is filled in order to submit
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name').strip().lower()
        connect = sqlite3.connect('database.db')
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM quiz WHERE quiz_name = ?", (quiz_name,)) # searches for inserted quiz name
        found = cursor.fetchone() # if any quiz is found
        connect.close()
        if found:
            quiz_id = found[0] # returns the quiz set selected
            return redirect(f'/crud_options/{quiz_id}') # allows user to moidfy quiz
        else:
            #return render_template_string(select_html, alert="enter an existing quiz") # if the quiz does not exist, alert user
            return render_template('select.html', alert="enter an existing quiz")
    return render_template("select.html")

# users can create a new quiz set
@app.route('/create', methods=['GET', 'POST'])
def create_quiz():
    # required ensures that users fill the box in order to submit
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name').strip().lower()
        if quiz_name:
            connect = sqlite3.connect('database.db')
            cursor = connect.cursor()
            cursor.execute("SELECT * FROM quiz WHERE quiz_name = ?", (quiz_name,)) # check if name exists
            found = cursor.fetchone() # fetches results
            if found: # if quiz name exists, notify the user
                return render_template('create.html',alert="Quiz name already exists")
            else: # if quiz name is unused, add quiz to list
                cursor.execute("INSERT INTO quiz (quiz_name) VALUES (?)", (quiz_name,))
                connect.commit()
                connect.close()
                quiz_id = cursor.lastrowid # determines if quiz exists
                return redirect(f'/crud_options/{quiz_id}') # allow users to modify quiz
    return render_template('create.html')

@app.route('/crud_options/<quiz_id>',methods=['GET', 'POST'])
def crud_options(quiz_id):
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'add': # if users want to add a question and answer, direct page
            return redirect(f'/add/{quiz_id}')
        elif choice == 'view': # if users want to view all the questions to modify
            return redirect(f'/view_questions/{quiz_id}')
    return render_template('crud.html',quiz_id=str(quiz_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
