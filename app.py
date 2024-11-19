# instalando pacotes necessários automáticamente com pip
import subprocess
import sys

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

dependencies = ["flask"]  # o pacote necessário para gerar tabelas

for package in dependencies:
    install_and_import(package)

# Importando bibliotecas necessárias
from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# Banco de dados
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

        # Validação básica
        question = data.get('question')
        correct_answer = data.get('correct_answer')
        incorrect_answers = data.get('incorrect_answers')
        
        if not question or not correct_answer or not incorrect_answers:
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

        # Converte incorrect_answers para string se for lista
        if isinstance(incorrect_answers, list):
            incorrect_answers = ', '.join(incorrect_answers)

        # Salva no banco
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
            return jsonify({'error': f"Erro ao salvar no banco de dados: {e}"}), 500
        finally:
            conn.close()

    # Método GET: Renderiza o formulário
    return render_template('add_question.html')

# # TODA A PARTE DO QUIZ
@app.route('/quiz', methods=['GET'])
def quiz():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Obter perguntas
    cursor.execute("SELECT id, question, correct_answer, incorrect_answers FROM questions")
    questions = [{
        'id': row[0],
        'question': row[1],
        'correct_option': row[2],
        'incorrect_answers': row[3].split(', ')  # Converter string em lista
    } for row in cursor.fetchall()]

    # Obter alunos
    cursor.execute("SELECT id, name FROM students")
    students = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
    conn.close()

    # Renderizar o template do quiz
    return render_template('quiz.html', questions=questions, students=students)

@app.route('/get-questions', methods=['GET'])
def get_questions():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, question, correct_answer, incorrect_answers FROM questions')
        questions = cursor.fetchall()  # [(id, question, correct_option, incorrect_answers), ...]
        conn.close()

        # Formatar perguntas
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
        return jsonify({'error': f'Ocorreu um erro no banco de dados: {str(e)}'}), 500

# CONTINUAÇÃO DO QUIZ
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

    # Verificar a resposta correta
    cursor.execute('SELECT correct_answer FROM questions WHERE id = ?', (question_id,))
    correct_answer = cursor.fetchone()

    if not correct_answer:
        conn.close()
        return jsonify({'error': 'Pergunta não encontrada!'}), 404

    # Limpar espaços e comparar com case-insensitive
    is_correct = selected_option.strip().lower() == correct_answer[0].strip().lower()
    points = 10 if is_correct else 0

    # Atualizar pontuação do aluno apenas se acertar
    try:
        conn = sqlite3.connect('database.db', timeout=1)  # Adiciona timeout para evitar bloqueio
        cursor = conn.cursor()

        # Verifica a resposta correta e calcula pontos
        cursor.execute('UPDATE students SET score = score + ? WHERE id = ?', (points, student_id))
        conn.commit()  # Comita a transação

    except sqlite3.Error as e:
        print(f"Erro ao atualizar pontuação: {str(e)}")
    finally:
        conn.close()  # Sempre feche a conexão após a operação


    return jsonify({
        'correct': is_correct,
        'message': 'Resposta correta!' if is_correct else 'Resposta errada!',
        'correct_answer': correct_answer[0]
    }), 200


@app.route('/submit-score', methods=['POST'])
def submit_score():
    try:
        # Recebe os dados da requisição
        data = request.json
        name = data['name']
        score = data['score']

        # Conecta ao banco de dados com timeout para evitar bloqueios
        conn = sqlite3.connect('database.db', timeout=10)  # Timeout de 10 segundos
        cursor = conn.cursor()

        # Insere a pontuação no banco de dados
        cursor.execute("INSERT INTO scores (name, score) VALUES (?, ?)", (name, score))
        conn.commit()  # Confirma a transação

        return jsonify({'message': 'Score submitted successfully'}), 200

    except sqlite3.Error as e:
        # Em caso de erro no banco de dados, retorna a mensagem de erro
        return jsonify({'error': f'Erro ao processar a pontuação: {str(e)}'}), 500

    finally:
        # Garante que a conexão seja fechada
        conn.close()


@app.route('/register-student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        print("AQUI ATIVOOOOOOOOOOOOOOOOOOOO")
        
        # Verifica se o conteúdo da requisição é JSON
        if not request.is_json:
            return jsonify({'error': 'Content-Type deve ser application/json'}), 400

        # Tenta obter o JSON da requisição
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

            # Inserir aluno no banco de dados
            cursor.execute('INSERT INTO students (name, email) VALUES (?, ?)', (name, email))
            conn.commit()

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email já registrado!'}), 400
        except sqlite3.Error as e:
            return jsonify({'error': f'Ocorreu um erro no banco de dados: {str(e)}'}), 500
        finally:
            conn.close()

        return jsonify({'message': 'Aluno registrado com sucesso!'}), 200

    return render_template('register-student.html')

@app.route('/remove-student/<int:student_id>', methods=['DELETE'])
def remove_student(student_id):
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Deletar o aluno pelo ID
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()

        conn.close()

        # Retorna uma mensagem de sucesso
        return jsonify({'message': f'Aluno com ID {student_id} removido com sucesso!'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': f'Erro ao remover o aluno: {e}'}), 500

@app.route('/remove-all-students', methods=['DELETE'])
def remove_all_students():
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Deletar todos os alunos
        cursor.execute('DELETE FROM students')
        conn.commit()

        conn.close()

        # Retorna uma mensagem de sucesso
        return jsonify({'message': 'Todos os alunos foram removidos com sucesso!'}), 200
    except sqlite3.Error as e:
        return jsonify({'error': f'Erro ao remover os alunos: {e}'}), 500



@app.route('/get-students', methods=['GET'])
def get_students():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email FROM students')
        students = cursor.fetchall()  # [(id, name, email), ...]
        conn.close()

        # Retornar lista de dicionários
        students_list = [{'id': row[0], 'name': row[1], 'email': row[2]} for row in students]
        return jsonify(students_list), 200
    except sqlite3.Error as e:
        return jsonify({'error': f'Ocorreu um erro no banco de dados: {str(e)}'}), 500



@app.route('/ranking', methods=['GET'])
def ranking():
    # Conectar ao banco de dados
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Obter o ranking dos alunos, ordenando por score em ordem decrescente
    cursor.execute('SELECT name, score FROM students ORDER BY score DESC')
    ranking = cursor.fetchall()  # Obtém todos os resultados

    # Fechar a conexão com o banco de dados
    conn.close()

    # Se você quer renderizar uma página com o ranking
    return render_template('ranking.html', ranking=ranking)

@app.route('/api/ranking', methods=['GET'])
def api_ranking():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, score FROM students ORDER BY score DESC')
    ranking = cursor.fetchall()
    conn.close()
    
    # Retorna como JSON
    return jsonify([{'name': row[0], 'score': row[1]} for row in ranking])


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
