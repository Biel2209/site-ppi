from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)


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
        (tipo, descricao, latitude, longitude, status, data)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        tipo,
        descricao,
        latitude,
        longitude,
        "Em análise",
        data
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

    conexao = sqlite3.connect("mapa_cidade.db")
    conexao.row_factory = sqlite3.Row

    cursor = conexao.cursor()

    cursor.execute("""
        SELECT *
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
            "relato": relato,
            "fotos": fotos
        })

    conexao.close()

    return render_template(
        "solicitacoes.html",
        relatos=dados
    )


if __name__ == "__main__":
    app.run(debug=True)