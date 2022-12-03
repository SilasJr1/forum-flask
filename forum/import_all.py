import os
import sqlite3
import json
import zipfile as zip


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


# conectar ao banco de dados
def abrir_conexao(caminho_db):
    connection = sqlite3.connect(caminho_db)
    connection.row_factory = dict_factory
    cursor = connection.cursor()
    return connection, cursor


def get_todos_registros_tabela(nome_tabela, caminho_db):
    conn, curs = abrir_conexao(caminho_db)
    conn.row_factory = dict_factory
    if nome_tabela == 'usuario':
        curs.execute("SELECT id, username, email, foto_perfil, linguagens FROM '{}' ".format(nome_tabela))
    else:
        curs.execute("SELECT * FROM '{}' ".format(nome_tabela))

    results = curs.fetchall()
    conn.close()

    return json.dumps(results, ensure_ascii=False, sort_keys=True, indent=4)


def sqliteToJson(caminho_db, pasta_destino):
    connection, cursor = abrir_conexao(caminho_db)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for nome_tabela in tables:
        results = get_todos_registros_tabela(nome_tabela['name'], caminho_db)

        caminho_final = os.path.join(os.sep, pasta_destino, nome_tabela['name'] + '.json')
        with open(caminho_final, 'w', encoding='utf-8') as arquivo:
            arquivo.write(results)

    connection.close()


def compactar(caminho_json, pasta_destino):
    path_zip = os.path.join(pasta_destino, 'database.zip')
    zf = zip.ZipFile(path_zip, 'w')
    for dirname, subdirs, files in os.walk(caminho_json):
        for filename in files:
            zf.write(os.path.join(dirname, filename), arcname=filename)
    zf.close()
