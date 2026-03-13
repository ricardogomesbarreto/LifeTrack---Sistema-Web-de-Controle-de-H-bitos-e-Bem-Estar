import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor
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
    """Estabelece conexão com o banco de dados usando PyMySQL"""
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="",
            database="diario_habitos",
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor  # IMPORTANTE: retorna dicionários
        )
        return conn
    except pymysql.Error as err:
        print(f"❌ Erro ao conectar: {err}")
        return None

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_senha(senha):
    """Cria hash da senha para segurança"""
    return hashlib.sha256(senha.encode()).hexdigest()

# ==================== ROTAS PÚBLICAS ====================

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
                except pymysql.IntegrityError:
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
            cursor = conn.cursor()
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

@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    return redirect(url_for('index'))

# ==================== ROTAS PROTEGIDAS (REQUER LOGIN) ====================

@app.route('/dashboard')
def dashboard():
    """Dashboard principal do usuário"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_bd()
    if not conn:
        return "Erro de conexão", 500
    
    cursor = conn.cursor()
    
    # Buscar dados do usuário
    cursor.execute(
        "SELECT peso, altura, objetivo, foto_perfil FROM usuarios WHERE id = %s",
        (session['usuario_id'],)
    )
    dados = cursor.fetchone()
    
    # Buscar hábitos
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
    
    # Data formatada
    data_atual = datetime.now().strftime('%d de %B de %Y')
    
    cursor.close()
    conn.close()
    
    # Dicas baseadas no objetivo e IMC
    dicas = []
    if dados and dados['objetivo']:
        objetivo = dados['objetivo'].lower()
        
        # Calcular IMC se tiver dados
        imc = 0
        if dados['peso'] > 0 and dados['altura'] > 0:
            imc = dados['peso'] / ((dados['altura']/100) ** 2)
        
        if objetivo == 'ganhar massa muscular':
            dicas = [
                '💪 Consuma 1.6 a 2.2g de proteína por kg de peso',
                '🏋️ Treine pesado com progressão de carga',
                '😴 Durma 7-9 horas para recuperação muscular',
                '🥩 Inclua carnes magras, ovos e leguminosas',
                '💧 Beba 35-40ml de água por kg de peso'
            ]
            if 0 < imc < 18.5:
                dicas.insert(0, '⚠️ Você está abaixo do peso - foco em superávit calórico!')
            elif imc > 25:
                dicas.insert(0, '⚠️ Combine ganho muscular com déficit calórico moderado')
                
        elif objetivo == 'perder peso':
            dicas = [
                '🥗 Déficit calórico de 300-500 kcal por dia',
                '🏃 150-300 minutos de cardio por semana',
                '💧 Beba 35ml de água por kg de peso',
                '🍎 Priorize alimentos integrais e fibras',
                '😴 Durma bem para controlar hormônios da fome'
            ]
            if imc > 30:
                dicas.insert(0, '⚠️ Obesidade - consulte um nutricionista!')
            elif 0 < imc < 18.5:
                dicas = ['⚠️ Você está abaixo do peso - não recomendamos perda de peso!']
                
        elif objetivo == 'manter a saúde':
            dicas = [
                '🚶 30 minutos de atividade física diária',
                '🥗 Dieta balanceada com todos os nutrientes',
                '😴 7-8 horas de sono por noite',
                '🧘 Pratique meditação ou alongamento',
                '💧 2 litros de água por dia'
            ]
            if imc > 25:
                dicas.insert(0, '⚠️ Sobrepeso - considere um plano de perda de peso')
            elif 0 < imc < 18.5:
                dicas.insert(0, '⚠️ Abaixo do peso - busque ganho de massa')
    
    return render_template(
        'dashboard.html',
        usuario=session['nome'],
        foto_url=session.get('foto_perfil'),
        habitos=habitos,
        habitos_feitos_hoje=habitos_feitos_hoje,
        peso=dados['peso'] if dados else 0,
        altura=dados['altura'] if dados else 0,
        objetivo=dados['objetivo'] if dados else '',
        dicas=dicas,
        data_atual=data_atual
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
            flash(f'Hábito "{nome}" adicionado com sucesso!', 'success')
        except pymysql.IntegrityError:
            flash('Este hábito já existe!', 'error')
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
            except pymysql.IntegrityError:
                pass  # Se já existe, ignora
        
        conn.commit()
        cursor.close()
        conn.close()
        flash('Progresso salvo com sucesso!', 'success')
    
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
        flash('Nenhum arquivo selecionado!', 'error')
        return redirect(url_for('perfil'))
    
    arquivo = request.files['foto_perfil']
    if arquivo.filename == '' or not allowed_file(arquivo.filename):
        flash('Arquivo inválido! Use apenas imagens PNG, JPG ou GIF.', 'error')
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
            flash('Foto atualizada com sucesso!', 'success')
    
    return redirect(url_for('perfil'))

@app.route('/atualizar_perfil', methods=['POST'])
def atualizar_perfil():
    """Atualiza o nome do usuário no perfil"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    novo_nome = request.form.get('nome', '').strip()
    
    if not novo_nome or len(novo_nome) < 3:
        flash('Nome deve ter pelo menos 3 caracteres!', 'error')
        return redirect(url_for('perfil'))
    
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET nome = %s WHERE id = %s",
                (novo_nome, session['usuario_id'])
            )
            conn.commit()
            
            # Atualizar a sessão
            session['nome'] = novo_nome
            
            flash('Nome atualizado com sucesso!', 'success')
            
        except Exception as e:
            flash(f'Erro ao atualizar nome: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Erro de conexão com o banco de dados!', 'error')
    
    return redirect(url_for('perfil'))

@app.route('/atualizar_dados', methods=['POST'])
def atualizar_dados():
    """Atualiza peso, altura e objetivo do usuário"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    # Pegar dados do formulário
    peso = request.form.get('peso', 0)
    altura = request.form.get('altura', 0)
    objetivo = request.form.get('objetivo', '')
    
    # Validações
    try:
        peso = float(peso) if peso else 0
        altura = float(altura) if altura else 0
    except ValueError:
        flash('Valores de peso e altura devem ser números!', 'error')
        return redirect(url_for('dashboard'))
    
    if peso < 0 or peso > 300:
        flash('Peso deve estar entre 0 e 300 kg!', 'error')
        return redirect(url_for('dashboard'))
    
    if altura < 0 or altura > 250:
        flash('Altura deve estar entre 0 e 250 cm!', 'error')
        return redirect(url_for('dashboard'))
    
    # Atualizar no banco
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE usuarios SET peso = %s, altura = %s, objetivo = %s WHERE id = %s",
                (peso, altura, objetivo, session['usuario_id'])
            )
            conn.commit()
            flash('Dados atualizados com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao atualizar dados: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
    else:
        flash('Erro de conexão com o banco de dados!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/apagar_foto', methods=['POST'])
def apagar_foto():
    """Apaga a foto de perfil do usuário"""
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    conn = conectar_bd()
    if conn:
        cursor = conn.cursor()
        try:
            # Buscar nome da foto atual
            cursor.execute(
                "SELECT foto_perfil FROM usuarios WHERE id = %s",
                (session['usuario_id'],)
            )
            resultado = cursor.fetchone()
            
            if resultado and resultado['foto_perfil'] and resultado['foto_perfil'] != 'default.png':
                # Apagar arquivo físico
                caminho_foto = os.path.join(app.root_path, 'static', 'fotos_perfil', resultado['foto_perfil'])
                if os.path.exists(caminho_foto):
                    os.remove(caminho_foto)
                
                # Atualizar banco para default.png
                cursor.execute(
                    "UPDATE usuarios SET foto_perfil = 'default.png' WHERE id = %s",
                    (session['usuario_id'],)
                )
                conn.commit()
                
                # Atualizar sessão
                session['foto_perfil'] = 'default.png'
                
                flash('Foto removida com sucesso!', 'success')
            else:
                flash('Você já está usando a foto padrão!', 'info')
                
        except Exception as e:
            flash(f'Erro ao remover foto: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return redirect(url_for('perfil'))

# ==================== INICIALIZAÇÃO ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)