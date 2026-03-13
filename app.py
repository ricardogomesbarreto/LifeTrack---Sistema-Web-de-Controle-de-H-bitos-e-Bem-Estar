import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime
import mysql.connector
from mysql.connector import IntegrityError
import hashlib

app = Flask(__name__)
app.secret_key = 'lifetrack_secret_key_2024'

# Configurações de upload
UPLOAD_FOLDER = os.path.join('static', 'fotos_perfil')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Criar pasta de upload se não existir
os.makedirs(os.path.join(app.root_path, 'static', 'fotos_perfil'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'img'), exist_ok=True)

def conectar_bd():
    """Estabelece conexão com o banco de dados"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="diario_habitos"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco: {err}")
        return None

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_senha(senha):
    """Cria hash da senha para segurança"""
    return hashlib.sha256(senha.encode()).hexdigest()

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Página de cadastro de usuário"""
    msg = ''
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        # Validações básicas
        if not nome or not email or not senha:
            msg = 'Todos os campos são obrigatórios!'
        elif len(senha) < 6:
            msg = 'A senha deve ter pelo menos 6 caracteres!'
        else:
            conn = conectar_bd()
            if conn:
                cursor = conn.cursor()
                try:
                    senha_hash = hash_senha(senha)
                    cursor.execute(
                        "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
                        (nome, email, senha_hash)
                    )
                    conn.commit()
                    return redirect(url_for('login', msg='Cadastro realizado com sucesso!'))
                except IntegrityError:
                    msg = 'Email já cadastrado!'
                except Exception as e:
                    msg = f'Erro ao cadastrar: {str(e)}'
                finally:
                    cursor.close()
                    conn.close()
            else:
                msg = 'Erro de conexão com o banco de dados!'
    
    return render_template('cadastro.html', msg=msg)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    msg = request.args.get('msg', '')
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor(dictionary=True)
            senha_hash = hash_senha(senha)
            
            cursor.execute(
                "SELECT id, nome, email, foto_perfil FROM usuarios WHERE email = %s AND senha = %s",
                (email, senha_hash)
            )
            usuario = cursor.fetchone()
            
            if usuario:
                session['usuario_id'] = usuario['id']
                session['nome'] = usuario['nome']
                session['email'] = usuario['email']
                session['foto_perfil'] = usuario['foto_perfil']
                return redirect(url_for('dashboard'))
            else:
                msg = "Email ou senha incorretos."
            
            cursor.close()
            conn.close()
        else:
            msg = 'Erro de conexão com o banco de dados!'
    
    return render_template('login.html', msg=msg)

@app.route('/dashboard')
def dashboard():
    """Dashboard principal do usuário"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_bd()
    if not conn:
        return "Erro de conexão com o banco de dados", 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Buscar dados do usuário
    cursor.execute(
        "SELECT peso, altura, objetivo, foto_perfil FROM usuarios WHERE id = %s",
        (session['usuario_id'],)
    )
    dados = cursor.fetchone()
    
    # Buscar hábitos do usuário
    cursor.execute(
        "SELECT nome FROM habitos WHERE usuario_id = %s ORDER BY nome",
        (session['usuario_id'],)
    )
    habitos = [h['nome'] for h in cursor.fetchall()]
    
    # Buscar hábitos feitos hoje
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        "SELECT nome_habito FROM habitos_feitos WHERE usuario_id = %s AND data = %s",
        (session['usuario_id'], data_hoje)
    )
    habitos_feitos_hoje = [h['nome_habito'] for h in cursor.fetchall()]
    
    # Gerar dicas baseadas no objetivo
    dicas = []
    if dados and dados['objetivo']:
        objetivo = dados['objetivo'].lower()
        if objetivo == 'ganhar massa muscular':
            dicas = [
                '💪 Aumente a ingestão de proteínas',
                '🏋️ Faça musculação regularmente',
                '😴 Durma bem para recuperação muscular',
                '🥩 Inclua carnes magras na dieta',
                '💧 Beba bastante água durante o dia'
            ]
        elif objetivo == 'perder peso':
            dicas = [
                '🥗 Reduza calorias e açúcares',
                '🏃 Inclua exercícios aeróbicos',
                '💧 Beba muita água',
                '🍎 Coma mais frutas e verduras',
                '⏰ Faça refeições em horários regulares'
            ]
        elif objetivo == 'manter a saúde':
            dicas = [
                '🚶 Caminhe 30 minutos por dia',
                '🥗 Mantenha uma dieta balanceada',
                '😴 Durma 7-8 horas por noite',
                '🧘 Pratique meditação',
                '💧 Beba 2 litros de água diariamente'
            ]
    
    cursor.close()
    conn.close()
    
    return render_template(
        'dashboard.html',
        usuario=session['nome'],
        foto_url=session.get('foto_perfil', 'default.png'),
        habitos=habitos,
        habitos_feitos_hoje=habitos_feitos_hoje,
        peso=dados['peso'] if dados else 0,
        altura=dados['altura'] if dados else 0,
        objetivo=dados['objetivo'] if dados else '',
        dicas=dicas if dicas else ['🎯 Defina um objetivo para receber dicas personalizadas!']
    )

@app.route('/adicionar_habito', methods=['POST'])
def adicionar_habito():
    """Adiciona um novo hábito"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    nome = request.form['nome'].strip()
    if not nome:
        return redirect(url_for('dashboard'))
    
    data = datetime.now().strftime('%Y-%m-%d')
    
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO habitos (usuario_id, nome, data) VALUES (%s, %s, %s)",
                (session['usuario_id'], nome, data)
            )
            conn.commit()
        except IntegrityError:
            # Hábito já existe
            pass
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/marcar_habitos', methods=['POST'])
def marcar_habitos():
    """Marca hábitos como feitos no dia"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    usuario_id = session['usuario_id']
    habitos_feitos = request.form.getlist('habitos_feitos')
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        
        # Remover marcações do dia atual para evitar duplicatas
        cursor.execute(
            "DELETE FROM habitos_feitos WHERE usuario_id = %s AND data = %s",
            (usuario_id, data_hoje)
        )
        
        # Inserir novas marcações
        for habito in habitos_feitos:
            try:
                cursor.execute(
                    "INSERT INTO habitos_feitos (usuario_id, nome_habito, data) VALUES (%s, %s, %s)",
                    (usuario_id, habito, data_hoje)
                )
            except IntegrityError:
                pass  # Se já existe, ignora
        
        conn.commit()
        cursor.close()
        conn.close()
    
    return redirect(url_for('dashboard'))

@app.route('/perfil')
def perfil():
    """Página de perfil do usuário"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    return render_template(
        'perfil.html',
        nome=session.get('nome'),
        email=session.get('email'),
        foto_url=session.get('foto_perfil', 'default.png')
    )

@app.route('/upload_foto', methods=['POST'])
def upload_foto():
    """Upload de foto de perfil"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    if 'foto_perfil' not in request.files:
        return redirect(url_for('perfil'))
    
    arquivo = request.files['foto_perfil']
    if arquivo.filename == '' or not allowed_file(arquivo.filename):
        return redirect(url_for('perfil'))
    
    if arquivo:
        # Gerar nome único para o arquivo
        extensao = arquivo.filename.rsplit('.', 1)[1].lower()
        nome_arquivo = f"user_{session['usuario_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extensao}"
        
        # Salvar arquivo
        caminho_pasta = os.path.join(app.root_path, 'static', 'fotos_perfil')
        caminho = os.path.join(caminho_pasta, nome_arquivo)
        arquivo.save(caminho)
        
        # Atualizar banco de dados
        conn = conectar_bd()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET foto_perfil = %s WHERE id = %s",
                (nome_arquivo, session['usuario_id'])
            )
            conn.commit()
            cursor.close()
            conn.close()
            
            # Atualizar sessão
            session['foto_perfil'] = nome_arquivo
    
    return redirect(url_for('perfil'))

@app.route('/atualizar_perfil', methods=['POST'])
def atualizar_perfil():
    """Atualiza dados do perfil"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    nome = request.form.get('nome', '')
    peso = request.form.get('peso', 0)
    altura = request.form.get('altura', 0)
    objetivo = request.form.get('objetivo', '')
    
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET nome = %s, peso = %s, altura = %s, objetivo = %s WHERE id = %s",
            (nome, peso, altura, objetivo, session['usuario_id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        session['nome'] = nome
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)