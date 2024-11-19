// ADICIONAR QUESTÕES
document.getElementById('add-question-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const data = {
        question: formData.get('question').trim(),
        correct_answer: formData.get('correct_answer').trim(),
        incorrect_answers: formData.get('incorrect_answers').trim(),
    };

    if (!data.question || !data.correct_answer || !data.incorrect_answers) {
        alert('Todos os campos são obrigatórios');
        return;
    }

    const response = await fetch('/add-question', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    const result = await response.json();
    if (response.ok) {
        alert(result.message);
    } else {
        alert(result.error || 'Erro ao adicionar a pergunta');
    }
});

// DESTACAR ÀS FUNCIONALIDADES
document.querySelectorAll('.options li').forEach(option => {
    option.addEventListener('click', function () {
        document.querySelectorAll('.options li').forEach(opt => opt.classList.remove('selected'));
        this.classList.add('selected');
    });
});

document.getElementById('register-student-form').addEventListener('submit', function (e) {
    e.preventDefault();
    alert('Aluno registrado com sucesso!');
});


// Responder Perguntas

document.querySelectorAll('.options li').forEach(option => {
    option.addEventListener('click', async function () {
        const questionId = this.dataset.questionId; // ID da pergunta
        const studentId = 1; // Substituir pelo ID real do aluno (ex: login ou sessão)
        const selectedOption = this.textContent;

        const response = await fetch('/submit-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId, question_id: questionId, selected_option: selectedOption })
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.correct ? 'Resposta correta!' : 'Resposta incorreta!');
        } else {
            alert(result.error);
        }
    });
});

// Exibir Ranking
async function fetchRanking() {
    const response = await fetch('/get-ranking');
    const ranking = await response.json();

    const rankingTable = document.querySelector('.ranking tbody');
    rankingTable.innerHTML = '';

    ranking.forEach((entry, index) => {
        const row = `
            <tr>
                <td>${index + 1}</td>
                <td>${entry.name}</td>
                <td>${entry.score}</td>
            </tr>
        `;
        rankingTable.innerHTML += row;
    });
}

fetchRanking();

// RESETAR O BANCO DE DADOS
