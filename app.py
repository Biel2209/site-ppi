from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "chave-temporaria")

@app.route("/")
def inicio():

    conexao = sqlite3.connect("mapa_cidade.db")
    cursor = conexao.cursor()

    # Quantidade de obras em andamento
    cursor.execute("""
        SELECT COUNT(*)
        FROM relatos
        WHERE status = ?
    """, ("Em andamento",))

    obras_andamento = cursor.fetchone()[0]


    # Quantidade de obras concluídas
    cursor.execute("""
        SELECT COUNT(*)
        FROM relatos
        WHERE status = ?
    """, ("Concluída",))

    obras_concluidas = cursor.fetchone()[0]


    # Quantidade total de problemas registrados
    cursor.execute("""
        SELECT COUNT(*)
        FROM relatos
    """)

    problemas_registrados = cursor.fetchone()[0]


    # Quantidade de solicitações em análise
    cursor.execute("""
        SELECT COUNT(*)
        FROM relatos
        WHERE status = ?
    """, ("Em análise",))

    solicitacoes_analise = cursor.fetchone()[0]


    conexao.close()


    return render_template(
        "index.html",
        obras_andamento=obras_andamento,
        obras_concluidas=obras_concluidas,
        problemas_registrados=problemas_registrados,
        solicitacoes_analise=solicitacoes_analise
    )

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "GET":
        return render_template("cadastro.html")

    nome = request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("senha")

    if not nome or not email or not senha:
        return "Preencha todos os campos."

    senha_hash = generate_password_hash(senha)

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    conexao = sqlite3.connect("mapa_cidade.db")
    cursor = conexao.cursor()

    try:

        cursor.execute("""
            INSERT INTO usuarios
            (nome, email, senha_hash, data_criacao)
            VALUES (?, ?, ?, ?)
        """, (
            nome,
            email,
            senha_hash,
            data
        ))

        conexao.commit()

    except sqlite3.IntegrityError:

        conexao.close()

        return "Esse e-mail já está cadastrado."

    conexao.close()

    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    senha = request.form.get("senha")

    if not email or not senha:
        return "Preencha todos os campos."

    conexao = sqlite3.connect("mapa_cidade.db")
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM usuarios
        WHERE email = ?
    """, (email,))

    usuario = cursor.fetchone()

    conexao.close()

    if usuario is None:
        return "E-mail ou senha incorretos."

    if not check_password_hash(usuario["senha_hash"], senha):
        return "E-mail ou senha incorretos."

    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]

    return redirect("/")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/mapa")
def mapa():
    return render_template("mapa.html")


@app.route("/obras")
def obras():
    return render_template("obras.html")


@app.route("/relatar")
def relatar():
    return render_template("relatar.html")


@app.route("/enviar-relato", methods=["POST"])
def enviar_relato():

    tipo = request.form.get("tipo")
    descricao = request.form.get("descricao")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")

    usuario_id = session.get("usuario_id")

    print("\n==============================")
    print("NOVO RELATO RECEBIDO")
    print("tipo:", tipo)
    print("descricao:", descricao)
    print("latitude:", latitude)
    print("longitude:", longitude)
    print("fotos:", request.files.getlist("fotos"))
    print("==============================\n")

    if not tipo or not descricao or not latitude or not longitude:
        return jsonify({
            "sucesso": False,
            "mensagem": "Dados incompletos."
        }), 400

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    conexao = sqlite3.connect("mapa_cidade.db")
    cursor = conexao.cursor()

    cursor.execute("""
    INSERT INTO relatos
    (tipo, descricao, latitude, longitude, status, data, usuario_id)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    tipo,
    descricao,
    latitude,
    longitude,
    "Em análise",
    data,
    usuario_id
))

    id_relato = cursor.lastrowid

    conexao.commit()
    conexao.close()

      # =========================
    # SALVAR FOTOS
    # =========================

    pasta_uploads = "static/uploads"

    os.makedirs(pasta_uploads, exist_ok=True)

    fotos = request.files.getlist("fotos")

    for indice, foto in enumerate(fotos):

        if foto.filename != "":

            nome_original = secure_filename(foto.filename)

            nome_arquivo = f"relato_{id_relato}_{indice}_{nome_original}"

            caminho = os.path.join(
                pasta_uploads,
                nome_arquivo
            )

            foto.save(caminho)

            print("Foto salva:", caminho)

            conexao = sqlite3.connect("mapa_cidade.db")
            cursor = conexao.cursor()

            cursor.execute("""
                INSERT INTO fotos (relato_id, arquivo)
                VALUES (?, ?)
            """, (
                id_relato,
                nome_arquivo
            ))
            

            conexao.commit()
            print("FOTO REGISTRADA NO BANCO:", nome_arquivo)
            conexao.close()


    return jsonify({
        "sucesso": True,
        "mensagem": "Obrigado por contribuir! Sua solicitação foi enviada e está em análise."
    })
@app.route("/apagar-relato/<int:id>", methods=["POST"])
def apagar_relato(id):

    conexao = sqlite3.connect("mapa_cidade.db")
    cursor = conexao.cursor()

    # Apaga as fotos relacionadas
    cursor.execute("""
        DELETE FROM fotos
        WHERE relato_id = ?
    """, (id,))

    # Apaga o relato
    cursor.execute("""
        DELETE FROM relatos
        WHERE id = ?
    """, (id,))

    conexao.commit()
    conexao.close()

    return redirect("/solicitacoes")

@app.route("/api/relatos")
def api_relatos():

    conexao = sqlite3.connect("mapa_cidade.db")
    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, tipo, descricao, latitude, longitude, status, data
        FROM relatos
        ORDER BY id DESC
    """)

    relatos = cursor.fetchall()

    dados = []

    for relato in relatos:

        cursor.execute("""
            SELECT arquivo
            FROM fotos
            WHERE relato_id = ?
        """, (relato["id"],))

        fotos = cursor.fetchall()

        dados.append({
            "id": relato["id"],
            "tipo": relato["tipo"],
            "descricao": relato["descricao"],
            "latitude": relato["latitude"],
            "longitude": relato["longitude"],
            "status": relato["status"],
            "data": relato["data"],
            "fotos": [
                foto["arquivo"]
                for foto in fotos
            ]
        })

    conexao.close()

    return jsonify(dados)

@app.route("/solicitacoes")
def solicitacoes():

    usuario_id = session.get("usuario_id")

    conexao = sqlite3.connect("mapa_cidade.db")
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    if usuario_id:

        cursor.execute("""
            SELECT *
            FROM relatos
            WHERE usuario_id = ?
            ORDER BY id DESC
        """, (usuario_id,))

    else:

        conexao.close()

        return render_template(
            "solicitacoes.html",
            relatos=[]
        )

    relatos = cursor.fetchall()

    dados = []

    for relato in relatos:

        cursor.execute("""
            SELECT arquivo
            FROM fotos
            WHERE relato_id = ?
        """, (relato["id"],))

        fotos = cursor.fetchall()

        dados.append({
            "relato": relato,
            "fotos": fotos
        })

    conexao.close()

    return render_template(
        "solicitacoes.html",
        relatos=dados
    )

@app.route("/cancelar-relato/<int:relato_id>", methods=["POST"])
def cancelar_relato(relato_id):

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return jsonify({
            "sucesso": False,
            "mensagem": "Você precisa estar logado."
        }), 401

    conexao = sqlite3.connect("mapa_cidade.db")
    conexao.row_factory = sqlite3.Row
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
        FROM relatos
        WHERE id = ?
        AND usuario_id = ?
    """, (relato_id, usuario_id))

    relato = cursor.fetchone()

    if relato is None:
        conexao.close()

        return jsonify({
            "sucesso": False,
            "mensagem": "Solicitação não encontrada."
        }), 404

    if relato["status"] != "Em análise":
        conexao.close()

        return jsonify({
            "sucesso": False,
            "mensagem": "Esta solicitação não pode mais ser cancelada."
        }), 400

    cursor.execute("""
        UPDATE relatos
        SET status = ?
        WHERE id = ?
        AND usuario_id = ?
    """, (
        "Cancelado",
        relato_id,
        usuario_id
    ))

    conexao.commit()
    conexao.close()

    return jsonify({
        "sucesso": True,
        "mensagem": "Solicitação cancelada com sucesso."
    })


if __name__ == "__main__":
    app.run(debug=True)