from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


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

        if foto.filename == "":
            continue

        nome_original = secure_filename(foto.filename)

        nome_arquivo = f"relato_{id_relato}_{indice}_{nome_original}"

        caminho = os.path.join(
            pasta_uploads,
            nome_arquivo
        )

        foto.save(caminho)

        print("Foto salva:", caminho)

    return jsonify({
        "sucesso": True,
        "mensagem": "Obrigado por contribuir! Sua solicitação foi enviada e está em análise."
    })


if __name__ == "__main__":
    app.run(debug=True)