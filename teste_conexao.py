#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" TESTE COMPLETO DO LIFETRACK """
""" Verifica todas as dependências e configurações necessárias para o sistema funcionar """

import sys
import os
import subprocess
import importlib.util
from datetime import datetime

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(texto):
    """Imprime um cabeçalho formatado"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}🔍 {texto}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(texto):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✅ {texto}{Colors.END}")

def print_warning(texto):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠️  {texto}{Colors.END}")

def print_error(texto):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}❌ {texto}{Colors.END}")

def print_info(texto):
    """Imprime mensagem informativa"""
    print(f"{Colors.BLUE}📌 {texto}{Colors.END}")

def verificar_python():
    """Verifica versão do Python"""
    print_header("VERIFICANDO PYTHON")
    
    versao = sys.version_info
    print(f"Versão: {sys.version}")
    
    if versao.major >= 3 and versao.minor >= 8:
        print_success(f"Python {versao.major}.{versao.minor}.{versao.micro} - Compatível")
        return True
    else:
        print_error(f"Python {versao.major}.{versao.minor} - Versão muito antiga. Necessário Python 3.8+")
        return False

def verificar_pacotes():
    """Verifica se todos os pacotes necessários estão instalados"""
    print_header("VERIFICANDO PACOTES PYTHON")
    
    pacotes_necessarios = {
        'flask': 'Flask',
        'pymysql': 'PyMySQL',
        'mysql.connector': 'mysql-connector-python',
        'werkzeug': 'Werkzeug',
        'jinja2': 'Jinja2'
    }
    
    pacotes_instalados = []
    pacotes_faltando = []
    pacotes_versao_errada = []
    
    for modulo, nome_pacote in pacotes_necessarios.items():
        spec = importlib.util.find_spec(modulo)
        if spec is not None:
            try:
                modulo_obj = __import__(modulo)
                if hasattr(modulo_obj, '__version__'):
                    versao = modulo_obj.__version__
                else:
                    versao = "versão desconhecida"
                print_success(f"{nome_pacote} - OK ({versao})")
                pacotes_instalados.append(nome_pacote)
            except:
                print_success(f"{nome_pacote} - OK")
                pacotes_instalados.append(nome_pacote)
        else:
            print_error(f"{nome_pacote} - NÃO INSTALADO")
            pacotes_faltando.append(nome_pacote)
    
    # Verificar versões específicas
    try:
        import pymysql
        print_success("PyMySQL - OK (recomendado para Windows)")
    except:
        pass
    
    try:
        import mysql.connector
        versao_mysql = mysql.connector.__version__
        if versao_mysql.startswith('8.0'):
            print_success(f"mysql-connector-python {versao_mysql} - OK")
        else:
            print_warning(f"mysql-connector-python {versao_mysql} - Pode causar problemas no Windows")
            pacotes_versao_errada.append(f"mysql-connector-python {versao_mysql} (recomendado: 8.0.x)")
    except:
        pass
    
    print(f"\n📊 Resumo: {len(pacotes_instalados)}/{len(pacotes_necessarios)} pacotes instalados")
    
    if pacotes_faltando:
        print_warning(f"Pacotes faltando: {', '.join(pacotes_faltando)}")
        print_info("Para instalar: pip install " + " ".join(pacotes_necessarios.values()))
    
    return len(pacotes_faltando) == 0

def verificar_mysql():
    """Verifica se o MySQL/MariaDB está instalado e rodando"""
    print_header("VERIFICANDO MYSQL/MARIADB")
    
    # Verificar se o MySQL está no PATH
    try:
        result = subprocess.run(['mysql', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            versao = result.stdout.strip()
            print_success(f"MySQL encontrado: {versao}")
            
            # Verificar se é MariaDB
            if 'MariaDB' in versao:
                print_info("✓ MariaDB detectado (compatível com MySQL)")
        else:
            print_error("MySQL não encontrado no PATH")
            return False
    except FileNotFoundError:
        print_error("MySQL não encontrado no PATH")
        print_info("Procure o MySQL em: C:\\xampp\\mysql\\bin\\mysql.exe")
        return False
    except subprocess.TimeoutExpired:
        print_error("Timeout ao verificar MySQL")
        return False
    
    # Verificar se o serviço MySQL está rodando
    try:
        # Verificar processo mysqld
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], 
                               capture_output=True, text=True)
        if 'mysqld.exe' in result.stdout:
            print_success("Serviço MySQL está rodando")
        else:
            # Verificar também mysqld.exe (MariaDB)
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], 
                                   capture_output=True, text=True)
            if 'mysqld.exe' in result.stdout:
                print_success("Serviço MariaDB está rodando")
            else:
                print_warning("Serviço MySQL/MariaDB não está rodando")
                print_info("Inicie o MySQL no XAMPP ou com 'net start MySQL'")
    except:
        print_warning("Não foi possível verificar o serviço MySQL")
    
    return True

def testar_conexao_mysql():
    """Testa a conexão com o banco de dados"""
    print_header("TESTANDO CONEXÃO COM O BANCO")
    
    # Tentar diferentes conectores
    conectores = []
    
    # Verificar PyMySQL
    try:
        import pymysql
        from pymysql.cursors import DictCursor
        conectores.append(('pymysql', pymysql))
    except ImportError:
        pass
    
    # Verificar mysql.connector
    try:
        import mysql.connector
        conectores.append(('mysql.connector', mysql.connector))
    except ImportError:
        pass
    
    if not conectores:
        print_error("Nenhum conector MySQL encontrado!")
        print_info("Instale com: pip install pymysql cryptography")
        return False
    
    print_info(f"Conectores disponíveis: {', '.join([c[0] for c in conectores])}")
    
    # Configurações de conexão
    configs = [
        {'host': 'localhost', 'user': 'root', 'password': '', 'database': 'diario_habitos'},
        {'host': '127.0.0.1', 'user': 'root', 'password': '', 'database': 'diario_habitos'},
        {'host': 'localhost', 'user': 'root', 'password': 'root', 'database': 'diario_habitos'},
    ]
    
    conexao_bem_sucedida = False
    
    for nome_conector, conector in conectores:
        print_info(f"\nTestando com {nome_conector}:")
        
        for i, config in enumerate(configs, 1):
            try:
                if nome_conector == 'pymysql':
                    conn = conector.connect(
                        host=config['host'],
                        user=config['user'],
                        password=config['password'],
                        database=config['database'],
                        charset='utf8mb4',
                        cursorclass=DictCursor,
                        connect_timeout=5
                    )
                else:
                    conn = conector.connect(
                        host=config['host'],
                        user=config['user'],
                        password=config['password'],
                        database=config['database'],
                        connection_timeout=5
                    )
                
                print_success(f"Conexão bem-sucedida (config {i})")
                print_info(f"  Host: {config['host']}")
                print_info(f"  User: {config['user']}")
                print_info(f"  Database: {config['database']}")
                
                # Testar consulta
                cursor = conn.cursor()
                cursor.execute("SELECT VERSION()")
                versao = cursor.fetchone()
                if nome_conector == 'pymysql':
                    print_info(f"  Versão MySQL: {versao['VERSION()']}")
                else:
                    print_info(f"  Versão MySQL: {versao[0]}")
                
                # Verificar tabelas
                cursor.execute("SHOW TABLES")
                tabelas = cursor.fetchall()
                print_info(f"  Tabelas encontradas: {len(tabelas)}")
                for tabela in tabelas:
                    if nome_conector == 'pymysql':
                        nome_tabela = list(tabela.values())[0]
                    else:
                        nome_tabela = tabela[0]
                    print(f"    - {nome_tabela}")
                
                cursor.close()
                conn.close()
                
                # Salvar configuração que funcionou
                with open('config_bd.txt', 'w') as f:
                    f.write(f"{nome_conector}\n{config['host']}\n{config['user']}\n{config['password']}")
                
                conexao_bem_sucedida = True
                return True
                
            except Exception as e:
                if i < len(configs):
                    print_warning(f"Config {i} falhou: {str(e)[:50]}...")
                else:
                    print_error(f"Config {i} falhou: {str(e)[:50]}...")
    
    if not conexao_bem_sucedida:
        print_error("\n❌ NENHUMA CONEXÃO BEM-SUCEDIDA!")
        print_info("\nPossíveis soluções:")
        print_info("1. Verifique se o MySQL está rodando (XAMPP)")
        print_info("2. Verifique se o banco 'diario_habitos' existe")
        print_info("3. Tente com senha: root, 123456, ou vazio")
        print_info("4. Execute: CREATE DATABASE diario_habitos;")
    
    return conexao_bem_sucedida

def verificar_estrutura_projeto():
    """Verifica se a estrutura de pastas e arquivos está correta"""
    print_header("VERIFICANDO ESTRUTURA DO PROJETO")
    
    estrutura_necessaria = {
        'pastas': [
            'static',
            'static/img',
            'static/fotos_perfil',
            'templates'
        ],
        'arquivos': [
            'app.py',
            'static/img/default.png',
            'templates/base.html',
            'templates/index.html',
            'templates/login.html',
            'templates/cadastro.html',
            'templates/dashboard.html',
            'templates/perfil.html'
        ]
    }
    
    # Verificar pastas
    todas_pastas_ok = True
    for pasta in estrutura_necessaria['pastas']:
        if os.path.exists(pasta):
            print_success(f"Pasta encontrada: {pasta}")
        else:
            print_error(f"Pasta não encontrada: {pasta}")
            print_info(f"Crie com: mkdir {pasta}")
            todas_pastas_ok = False
    
    # Verificar arquivos
    todos_arquivos_ok = True
    for arquivo in estrutura_necessaria['arquivos']:
        if os.path.exists(arquivo):
            print_success(f"Arquivo encontrado: {arquivo}")
        else:
            print_error(f"Arquivo não encontrado: {arquivo}")
            todos_arquivos_ok = False
    
    return todas_pastas_ok and todos_arquivos_ok

def verificar_imagem_padrao():
    """Verifica se a imagem padrão existe e é válida"""
    print_header("VERIFICANDO IMAGEM PADRÃO")
    
    caminho_img = 'static/img/default.png'
    
    if os.path.exists(caminho_img):
        tamanho = os.path.getsize(caminho_img)
        if tamanho > 0:
            print_success(f"Imagem padrão encontrada ({tamanho} bytes)")
            
            # Verificar se é realmente uma imagem (básico)
            with open(caminho_img, 'rb') as f:
                cabecalho = f.read(8)
                if cabecalho.startswith(b'\x89PNG'):
                    print_success("✓ Formato PNG válido")
                elif cabecalho.startswith(b'\xff\xd8'):
                    print_success("✓ Formato JPEG válido")
                else:
                    print_warning("Formato de imagem não reconhecido")
        else:
            print_error("Imagem padrão existe mas está vazia")
    else:
        print_error("Imagem padrão não encontrada!")
        print_info("Coloque uma imagem em: static/img/default.png")
        return False
    
    return True

def verificar_permissoes():
    """Verifica permissões de pastas importantes"""
    print_header("VERIFICANDO PERMISSÕES")
    
    pastas_escrita = [
        'static/fotos_perfil',
        'static/img'
    ]
    
    todas_ok = True
    for pasta in pastas_escrita:
        if os.path.exists(pasta):
            if os.access(pasta, os.W_OK):
                print_success(f"Pasta {pasta} tem permissão de escrita")
            else:
                print_error(f"Pasta {pasta} NÃO tem permissão de escrita")
                todas_ok = False
        else:
            print_warning(f"Pasta {pasta} não existe")
            todas_ok = False
    
    return todas_ok

def gerar_relatorio():
    """Gera um relatório completo da verificação"""
    print_header("RELATÓRIO COMPLETO DO LIFETRACK")
    print(f"Data da verificação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Sistema Operacional: {sys.platform}")
    print(f"Diretório atual: {os.getcwd()}")
    
    resultados = {}
    
    # Executar todas as verificações
    resultados['python'] = verificar_python()
    resultados['pacotes'] = verificar_pacotes()
    resultados['mysql'] = verificar_mysql()
    resultados['conexao'] = testar_conexao_mysql()
    resultados['estrutura'] = verificar_estrutura_projeto()
    resultados['imagem'] = verificar_imagem_padrao()
    resultados['permissoes'] = verificar_permissoes()
    
    # Resumo final
    print_header("RESUMO DA VERIFICAÇÃO")
    
    todos_ok = True
    for chave, valor in resultados.items():
        status = f"{Colors.GREEN}✓ OK{Colors.END}" if valor else f"{Colors.RED}✗ FALHOU{Colors.END}"
        nome_teste = chave.replace('_', ' ').title()
        print(f"{nome_teste}: {status}")
        if not valor:
            todos_ok = False
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    
    if todos_ok:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ SISTEMA PRONTO PARA EXECUÇÃO!{Colors.END}")
        print(f"{Colors.GREEN}Execute: python app.py{Colors.END}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  SISTEMA COM PROBLEMAS A CORRIGIR{Colors.END}")
        print(f"{Colors.YELLOW}Corrija os erros acima antes de executar{Colors.END}")
    
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    return todos_ok

def menu_principal():
    """Menu interativo do script de teste"""
    while True:
        print_header("MENU DE TESTES DO LIFETRACK")
        print("1. Executar todos os testes")
        print("2. Testar apenas Python")
        print("3. Testar apenas pacotes")
        print("4. Testar apenas MySQL")
        print("5. Testar apenas conexão com banco")
        print("6. Testar apenas estrutura do projeto")
        print("7. Instalar dependências necessárias")
        print("8. Sair")
        
        opcao = input(f"\n{Colors.BOLD}Escolha uma opção: {Colors.END}").strip()
        
        if opcao == '1':
            gerar_relatorio()
        elif opcao == '2':
            verificar_python()
        elif opcao == '3':
            verificar_pacotes()
        elif opcao == '4':
            verificar_mysql()
        elif opcao == '5':
            testar_conexao_mysql()
        elif opcao == '6':
            verificar_estrutura_projeto()
        elif opcao == '7':
            print_header("INSTALANDO DEPENDÊNCIAS")
            pacotes = ['flask', 'pymysql', 'mysql-connector-python==8.0.33', 'werkzeug', 'cryptography']
            for pacote in pacotes:
                print_info(f"Instalando {pacote}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', pacote])
            print_success("Instalação concluída!")
        elif opcao == '8':
            print(f"{Colors.GREEN}Até logo!{Colors.END}")
            break
        else:
            print_error("Opção inválida!")
        
        input(f"\n{Colors.BOLD}Pressione Enter para continuar...{Colors.END}")

if __name__ == "__main__":
    # Verificar se está sendo executado como script
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        gerar_relatorio()
    else:
        menu_principal()