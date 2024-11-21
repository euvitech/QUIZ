#!/usr/bin/python
# vim: set fileencoding=UTF-8 :

import subprocess
import sys

from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        incorrect_answers TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        score INTEGER NOT NULL
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        score INTEGER DEFAULT 0
    )
    ''')
    

    conn.commit()
    conn.close()



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add-question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        data = request.get_json()

        question = data.get('question')
        correct_answer = data.get('correct_answer')
        incorrect_answers = data.get('incorrect_answers')
        #!/usr/bin/python
        # -*- coding: ascii -*-
        if not question or not correct_answer or not incorrect_answers:
          
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

        if isinstance(incorrect_answers, list):
            incorrect_answers = ', '.join(incorrect_answers)

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO questions (question, correct_answer, incorrect_answers) VALUES (?, ?, ?)",
                (question, correct_answer, incorrect_answers)
            )
            conn.commit()
            return jsonify({'message': 'Pergunta adicionada com sucesso!'}), 201
        except sqlite3.Error as e:
            return jsonify('error:' "Erro ao salvar no banco de dados: {}".format(e)), 500
        finally:
            conn.close()

    return render_template('add_question.html')

@app.route('/quiz', methods=['GET'])
def quiz():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, question, correct_answer, incorrect_answers FROM questions")
    questions = [{
        'id': row[0],
        'question': row[1],
        'correct_option': row[2],
        'incorrect_answers': row[3].split(', ') 
    } for row in cursor.fetchall()]

    cursor.execute("SELECT id, name FROM students")
    students = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    conn.close()

    return render_template('quiz.html', questions=questions, students=students)

@app.route('/get-questions', methods=['GET'])
def get_questions():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, question, correct_answer, incorrect_answers FROM questions')
        questions = cursor.fetchall()  
        conn.close()

        questions_list = [
            {
                'id': row[0],
                'question': row[1],
                'correct_option': row[2],
                'options': [row[2]] + row[3].split(', ')
            }
            for row in questions
        ]
        return jsonify(questions_list), 200
    except sqlite3.Error as e:
        return jsonify({'error:' "Ocorreu um erro no banco de dados: {}".format(str(e))}), 500
      
@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    data = request.get_json()
    student_id = data.get('student_id')
    question_id = data.get('question_id')
    selected_option = data.get('selected_option')

    if not student_id or not question_id or not selected_option:
        return jsonify({'error': 'Todos os campos são obrigatórios!'}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT correct_answer FROM questions WHERE id = ?', (question_id,))
    correct_answer = cursor.fetchone()

    if not correct_answer:
        conn.close()
        return jsonify({'error': 'Pergunta não encontrada!'}), 404

    is_correct = selected_option.strip().lower() == correct_answer[0].strip().lower()
    points = 10 if is_correct else 0

    try:
        conn = sqlite3.connect('database.db', timeout=1)  
        cursor = conn.cursor()

        cursor.execute('UPDATE students SET score = score + ? WHERE id = ?', (points, student_id))
        conn.commit()  
        
    except sqlite3.Error as e:
        print("Erro ao atualizar pontuação: {}".format(str(e)))
    finally:
        conn.close()


    return jsonify({
        'correct': is_correct,
        'message': 'Resposta correta!' if is_correct else 'Resposta errada!',
        'correct_answer': correct_answer[0]
    }), 200


@app.route('/submit-score', methods=['POST'])
def submit_score():
    try:
        data = request.json
        name = data['name']
        score = data['score']

        conn = sqlite3.connect('database.db', timeout=10)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO scores (name, score) VALUES (?, ?)", (name, score))
        conn.commit() 

        return jsonify({'message': 'Score submitted successfully'}), 200

    except sqlite3.Error as e:
        return jsonify({'error:' "Erro ao processar a pontuação: {}".format(str(e))}), 500

    finally:
        conn.close()


@app.route('/register-student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        print("AQUI ATIVOOOOOOOOOOOOOOOOOOOO")
        
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 400

        data = request.get_json()

        if not data:
            return jsonify({'error': 'Erro ao processar os dados!'}), 400

        name = data.get('name')
        email = data.get('email')

        if not name or not email:
            return jsonify({'error': 'Todos os campos são obrigatórios!'}), 400

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            cursor.execute('INSERT INTO students (name, email) VALUES (?, ?)', (name, email))
            conn.commit()

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email já registrado!'}), 400
        except sqlite3.Error as e:
            return jsonify({'error': "Ocorreu um erro no banco de dados: {}".format(str(e))}), 500
        finally:
            conn.close()

        return jsonify({'message': 'Aluno registrado com sucesso!'}), 200

    return render_template('register-student.html')

@app.route('/remove-student/<int:student_id>', methods=['DELETE'])
def remove_student(student_id):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()

        conn.close()

        return jsonify({'message': "Aluno com ID {} removido com sucesso!".format(student_id)}), 200
    except sqlite3.Error as e:
        return jsonify({'error': "Erro ao remover o aluno: {}".format(e)}), 500

@app.route('/remove-all-students', methods=['DELETE'])
def remove_all_students():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM students')
        conn.commit()

        conn.close()

        return jsonify({'message': 'Todos os alunos foram removidos com sucesso!'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': "Erro ao remover os alunos: {}".format(e)}), 500



@app.route('/get-students', methods=['GET'])
def get_students():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email FROM students')
        students = cursor.fetchall() 
        conn.close()

        students_list = [{'id': row[0], 'name': row[1], 'email': row[2]} for row in students]
        return jsonify(students_list), 200
    except sqlite3.Error as e:
        return jsonify({'error': "Ocorreu um erro no banco de dados: {}".format(str(e))}), 500



@app.route('/ranking', methods=['GET'])
def ranking():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT name, score FROM students ORDER BY score DESC')
    ranking = cursor.fetchall()  

    conn.close()

    return render_template('ranking.html', ranking=ranking)

@app.route('/api/ranking', methods=['GET'])
def api_ranking():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, score FROM students ORDER BY score DESC')
    ranking = cursor.fetchall()
    conn.close()
    
    return jsonify([{'name': row[0], 'score': row[1]} for row in ranking])


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
