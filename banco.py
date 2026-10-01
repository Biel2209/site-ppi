import sqlite3


def criar_banco():

    conexao = sqlite3.connect("mapa_cidade.db")
    conexao.execute("PRAGMA foreign_keys = ON")
    cursor = conexao.cursor()

    # =========================
    # TABELA DE RELATOS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Em análise',
            data TEXT NOT NULL
        )
    """)

    # Verifica as colunas atuais dos relatos
    cursor.execute("""
        PRAGMA table_info(relatos)
    """)

    colunas_relatos = cursor.fetchall()
    nomes_colunas_relatos = []

    for coluna in colunas_relatos:
        nomes_colunas_relatos.append(coluna[1])

    # Adiciona usuario_id se ainda não existir
    if "usuario_id" not in nomes_colunas_relatos:

        cursor.execute("""
            ALTER TABLE relatos
            ADD COLUMN usuario_id INTEGER
        """)

    # Adiciona rua se ainda não existir
    if "rua" not in nomes_colunas_relatos:

        cursor.execute("""
            ALTER TABLE relatos
            ADD COLUMN rua TEXT
        """)

    # Adiciona bairro se ainda não existir
    if "bairro" not in nomes_colunas_relatos:

        cursor.execute("""
            ALTER TABLE relatos
            ADD COLUMN bairro TEXT
        """)

    # =========================
    # TABELA DE FOTOS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            relato_id INTEGER NOT NULL,
            arquivo TEXT NOT NULL,
            FOREIGN KEY (relato_id) REFERENCES relatos(id)
        )
    """)

    # =========================
    # TABELA DE USUÁRIOS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            data_criacao TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'usuario'
        )
    """)

    # Verifica as colunas dos usuários
    cursor.execute("""
        PRAGMA table_info(usuarios)
    """)

    colunas_usuarios = cursor.fetchall()
    nomes_colunas_usuarios = []

    for coluna in colunas_usuarios:
        nomes_colunas_usuarios.append(coluna[1])

    # Adiciona perfil se ainda não existir
    if "perfil" not in nomes_colunas_usuarios:

        cursor.execute("""
            ALTER TABLE usuarios
            ADD COLUMN perfil TEXT NOT NULL DEFAULT 'usuario'
        """)

    # Mantém contas existentes utilizáveis e adiciona os dados de verificação.
    cursor.execute("PRAGMA table_info(usuarios)")
    nomes_colunas_usuarios = [coluna[1] for coluna in cursor.fetchall()]
    colunas_verificacao = {
        "email_verificado": "INTEGER NOT NULL DEFAULT 1",
        "codigo_verificacao_hash": "TEXT",
        "codigo_expira_em": "TEXT",
        "codigo_ultimo_envio_em": "TEXT",
        "codigo_tentativas": "INTEGER NOT NULL DEFAULT 0",
    }
    for nome_coluna, definicao in colunas_verificacao.items():
        if nome_coluna not in nomes_colunas_usuarios:
            cursor.execute(
                f"ALTER TABLE usuarios ADD COLUMN {nome_coluna} {definicao}"
            )

    # =========================
    # TABELA DE FEEDBACKS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nota INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
            comentario TEXT NOT NULL,
            data_criacao TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)

    # =========================
    # TABELA DE OBRAS
    # =========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            localizacao TEXT NOT NULL,
            status TEXT NOT NULL,
            previsao TEXT,
            descricao TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    # Verifica as colunas atuais das obras
    cursor.execute("""
        PRAGMA table_info(obras)
    """)

    colunas_obras = cursor.fetchall()
    nomes_colunas_obras = []

    for coluna in colunas_obras:
        nomes_colunas_obras.append(coluna[1])

    # Adiciona rua se ainda não existir
    if "rua" not in nomes_colunas_obras:

        cursor.execute("""
            ALTER TABLE obras
            ADD COLUMN rua TEXT
        """)

    # Adiciona bairro se ainda não existir
    if "bairro" not in nomes_colunas_obras:

        cursor.execute("""
            ALTER TABLE obras
            ADD COLUMN bairro TEXT
        """)

    # =========================
    # OBRAS INICIAIS
    # =========================

    cursor.execute("""
        SELECT COUNT(*)
        FROM obras
    """)

    quantidade_obras = cursor.fetchone()[0]

    if quantidade_obras == 0:

        cursor.execute("""
            INSERT INTO obras
            (
                titulo,
                localizacao,
                rua,
                bairro,
                status,
                previsao,
                descricao,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Pavimentação da rua",
            "Centro",
            "Rua dos Estudantes",
            "Centro",
            "Em andamento",
            "Dezembro/2026",
            "Obra de pavimentação e melhoria da via.",
            -20.4695,
            -55.7860
        ))

        cursor.execute("""
            INSERT INTO obras
            (
                titulo,
                localizacao,
                rua,
                bairro,
                status,
                previsao,
                descricao,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Reforma da praça",
            "Alto",
            "Rua da Praça",
            "Alto",
            "Concluída",
            "Setembro/2026",
            "Reforma e revitalização da praça.",
            -20.4730,
            -55.7890
        ))

        cursor.execute("""
            INSERT INTO obras
            (
                titulo,
                localizacao,
                rua,
                bairro,
                status,
                previsao,
                descricao,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Melhoria na iluminação",
            "Nova Aquidauana",
            "Rua Principal",
            "Nova Aquidauana",
            "Em análise",
            None,
            "Avaliação para melhoria da iluminação pública.",
            -20.4660,
            -55.7830
        ))

        cursor.execute("""
            INSERT INTO obras
            (
                titulo,
                localizacao,
                rua,
                bairro,
                status,
                previsao,
                descricao,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "Manutenção da via",
            "Guanandi",
            "Rua Guanandi",
            "Guanandi",
            "Em andamento",
            "Novembro/2026",
            "Manutenção e recuperação da via.",
            -20.4780,
            -55.7920
        ))

    conexao.commit()
    conexao.close()


criar_banco()


# =========================
# DEFINE O ADMINISTRADOR
# =========================

email_admin = "adm@exemplo.com"

conexao = sqlite3.connect("mapa_cidade.db")
conexao.execute("PRAGMA foreign_keys = ON")
cursor = conexao.cursor()

try:
    cursor.execute("""
        UPDATE usuarios
        SET perfil = 'admin'
        WHERE email = ?
    """, (email_admin,))
    conexao.commit()
finally:
    conexao.close()
