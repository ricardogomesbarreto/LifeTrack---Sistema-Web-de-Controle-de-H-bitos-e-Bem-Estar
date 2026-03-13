-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS diario_habitos;
USE diario_habitos;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    foto_perfil VARCHAR(255) DEFAULT 'default.png',
    peso DECIMAL(5,2) DEFAULT 0,
    altura DECIMAL(5,2) DEFAULT 0,
    objetivo VARCHAR(50) DEFAULT '',
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de hábitos
CREATE TABLE IF NOT EXISTS habitos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    data DATE NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_habito_usuario (usuario_id, nome)
);

-- Tabela de hábitos marcados como feitos
CREATE TABLE IF NOT EXISTS habitos_feitos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    nome_habito VARCHAR(100) NOT NULL,
    data DATE NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_registro_diario (usuario_id, nome_habito, data)
);