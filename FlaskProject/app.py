from urllib import request

from flask import Flask, request, render_template_string, redirect
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

    return render_template_string("""
        <h1>Welcome to the Quiz App!</h1>
        <form method="POST">
            <button type="submit" name='choice' value="select">Select a Quiz Set</button>
            <br>
            <button type="submit" name='choice' value="create">Create a New Quiz Set</button>
        </form>
        """)

# page where users can add questions and answers to their quiz
@app.route('/add/<quiz_id>', methods=['GET','POST'])
def add_question(quiz_id):
    add_html = """
                    <h1>Add a quiz!</h1>
                    <a href="/welcome">Home</a><br>
                    <a href="/crud_options/{{quiz_id}}">Quiz Options</a><br>
                    <form method="POST">
                        <label for="ques">Question:</label><br>
                        <input type="text" name="question" id="question" required>
                        <br>
                        <label for="ans">Answer:</label><br>
                        <input type="text" name="answer" id="answer" required>
                        <button type="submit" name='fill' value="select">Submit Question</button>
                        </form>
                        {% if alert %}
                            <script>alert("{{ alert }}");</script>
                        {% endif %}
                """
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
                return render_template_string(add_html,alert="Question is not unique",quiz_id=str(quiz_id))
            # alert user that q&a are added properly
            return render_template_string(add_html,alert="Question and answer added successfully",quiz_id=str(quiz_id))
    return render_template_string(add_html,quiz_id=str(quiz_id))

# users can update an existing question or answer
@app.route('/change/<quiz_id>/<question_id>', methods=['GET','POST'])
def change_question(quiz_id, question_id):
    change_html = """
                    <h1>Edit Question or answer!</h1>
                    <a href="/welcome">Home</a><br>
                    <a href="/crud_options/{{quiz_id}}">Quiz Options</a><br>
                    <form method="POST">
                        <input type="text" name="question" id="question">
                        <input type="text" name="answer" id="answer">
                        <button type="submit" name='fill' value="select">Update Question/Answer</button>
                    </form>
                    {% if alert %}
                            <script>alert("{{ alert }}");</script>
                    {% endif %}
                    """
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
            return render_template_string(change_html,alert="Enter a Question or Answer",quiz_id=str(quiz_id))
        # question and answer are successfully changed
        return render_template_string(change_html,alert='Question or Answer successfully updated',quiz_id=str(quiz_id))
    return render_template_string(change_html,quiz_id=str(quiz_id))

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
    view_html = ("<h1>All Questions!</h1>"
                 '<a href="/welcome">Home</a><br>'
                 '<a href="/crud_options/{{quiz_id}}">Quiz Options</a><br><br>'
             "{% if all_questions %}"
                 "{% for question in all_questions %}"
                 "Question: {{ question[1] }}<br>"
                 "Answer: {{ question[3] }}"
                 '<form method="POST" action="/delete/{{quiz_id}}/{{question[2]}}"> '
                        '<button type="submit">Delete</button>'
                 '<br>'
                 '<a href="/change/{{quiz_id}}/{{question[2]}}"'
                        '<button type="submit">Update Question Or Answer</button>'
                '</a><br><br>'
                "{% endfor %}"
             "{% else %}"
                "No Questions added"
             "{% endif %}")

    return render_template_string(view_html,all_questions=all_questions,quiz_id=str(quiz_id))

# users may select an existing quiz to work on
@app.route('/select',methods=['GET', 'POST'])
def select_quiz():
    # require ensures the box is filled in order to submit
    select_html="""
                <h1>Enter Quiz Name!</h1>
                <a href="/welcome">Home</a><br>
                <form method="POST">
                    <input type="text" name="quiz_name" id="quiz_name" required>
                    <button type="submit" name='fill' value="select">Submit Name</button>
                </form>
                {% if alert %}
                        <script>alert("{{ alert }}");</script>
                {% endif %}
                """
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
            return render_template_string(select_html, alert="enter an existing quiz") # if the quiz does not exist, alert user
    return render_template_string(select_html)

# users can create a new quiz set
@app.route('/create', methods=['GET', 'POST'])
def create_quiz():
    # required ensures that users fill the box in order to submit
    create_html="""
            <h1>Enter Quiz Name!</h1>
            <a href="/welcome">Home</a><br>
            <form method="POST">
                <input type="text" name="quiz_name" id="quiz_name" required>
                <button type="submit" name='fill' value="create">Submit Name</button>
            </form>
            {% if alert %}
                        <script>alert("{{ alert }}");</script>
                {% endif %}
            """
    if request.method == 'POST':
        quiz_name = request.form.get('quiz_name').strip().lower()
        if quiz_name:
            connect = sqlite3.connect('database.db')
            cursor = connect.cursor()
            cursor.execute("SELECT * FROM quiz WHERE quiz_name = ?", (quiz_name,)) # check if name exists
            found = cursor.fetchone() # fetches results
            if found: # if quiz name exists, notify the user
                return render_template_string(create_html,alert="Quiz name already exists")
            else: # if quiz name is unused, add quiz to list
                cursor.execute("INSERT INTO quiz (quiz_name) VALUES (?)", (quiz_name,))
                connect.commit()
                connect.close()
                quiz_id = cursor.lastrowid # determines if quiz exists
                return redirect(f'/crud_options/{quiz_id}') # allow users to modify quiz
    return render_template_string(create_html)

@app.route('/crud_options/<quiz_id>',methods=['GET', 'POST'])
def crud_options(quiz_id):
    if request.method == 'POST':
        choice = request.form.get('choice')
        if choice == 'add': # if users want to add a question and answer, direct page
            return redirect(f'/add/{quiz_id}')
        elif choice == 'view': # if users want to view all the questions to modify
            return redirect(f'/view_questions/{quiz_id}')
    return render_template_string("""
            <h1>Quiz options</h1>
            <a href="/welcome">Home</a><br>
            <form method="POST">
                <button type="submit" name='choice' value="add">Add Q/At</button>
                <br>
                <button type="submit" name='choice' value="view">View All Questions Q/At</button>
            </form>
            """)

if __name__ == '__main__':
    app.run()
