from flask import render_template, redirect, url_for, flash, request, abort
from forum import app, database, bcrypt
from forum.forms import FormLogin, FormCriarConta, FormEditarPerfil, FormCriarPost, FormJogos
from forum.models import Usuario, Post, Jogo
from flask_login import login_user, logout_user, current_user, login_required
import secrets
import os
from PIL import Image
import requests
from forum.import_all import sqliteToJson, compactar


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


@app.route('/usuarios')
@login_required
def usuarios():
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', lista_usuarios=lista_usuarios)


@app.route('/postagens')
@login_required
def postagens():
    posts = Post.query.order_by(Post.id.desc())
    return render_template('postagens.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form_login = FormLogin()
    if form_login.validate_on_submit() and 'botao_submit_login' in request.form:
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            login_user(usuario)
            flash(f'Login feito com sucesso no e-mail: {form_login.email.data}', 'alert-success')
            par_next = request.args.get('next')
            if par_next:
                return redirect(par_next)
            else:
                return redirect(url_for('home'))
        else:
            flash(f'Falha no Login. E-mail ou Senha Incorretos', 'alert-danger')
    return render_template('login.html', form_login=form_login)


@app.route('/criar-conta', methods=['GET', 'POST'])
def criar_conta():
    form_criarconta = FormCriarConta()
    if form_criarconta.validate_on_submit() and 'botao_submit_criarconta' in request.form:
        senha_cript = bcrypt.generate_password_hash(form_criarconta.senha.data)
        usuario = Usuario(username=form_criarconta.username.data, email=form_criarconta.email.data, senha=senha_cript)
        database.session.add(usuario)
        database.session.commit()
        flash(f'Conta criada para o e-mail: {form_criarconta.email.data}', 'alert-success')
        return redirect(url_for('home'))
    return render_template('criarconta.html', form_criarconta=form_criarconta)


@app.route('/sair')
@login_required
def sair():
    logout_user()
    flash(f'Logout Feito com Sucesso', 'alert-success')
    return redirect(url_for('home'))


@app.route('/perfil')
@login_required
def perfil():
    foto_perfil = url_for('static', filename='fotos_perfil/{}'.format(current_user.foto_perfil))
    return render_template('perfil.html', foto_perfil=foto_perfil, usuario=current_user)


@app.route('/post/criar', methods=['GET', 'POST'])
@login_required
def criar_post():
    form = FormCriarPost()
    if form.validate_on_submit():
        post = Post(titulo=form.titulo.data, corpo=form.corpo.data, autor=current_user)
        database.session.add(post)
        database.session.commit()
        flash('Post Criado com Sucesso', 'alert-success')
        return redirect(url_for('home'))
    return render_template('criarpost.html', form=form)


def salvar_imagem(imagem):
    codigo = secrets.token_hex(8)
    nome, extensao = os.path.splitext(imagem.filename)
    nome_arquivo = nome + codigo + extensao
    caminho_completo = os.path.join(app.root_path, 'static/fotos_perfil', nome_arquivo)
    tamanho = (400, 400)
    imagem_reduzida = Image.open(imagem)
    imagem_reduzida.thumbnail(tamanho)
    imagem_reduzida.save(caminho_completo)
    return nome_arquivo


def atualizar_linguagens(form):
    lista_linguagens = []
    for campo in form:
        if 'linguagem_' in campo.name:
            if campo.data:
                lista_linguagens.append(campo.label.text)
    return ';'.join(lista_linguagens)


@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = FormEditarPerfil()
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.username = form.username.data
        if form.foto_perfil.data:
            nome_imagem = salvar_imagem(form.foto_perfil.data)
            current_user.foto_perfil = nome_imagem
        current_user.linguagens = atualizar_linguagens(form)
        database.session.commit()
        flash('Perfil atualizado com Sucesso', 'alert-success')
        return redirect(url_for('perfil'))
    elif request.method == "GET":
        form.email.data = current_user.email
        form.username.data = current_user.username
    foto_perfil = url_for('static', filename='fotos_perfil/{}'.format(current_user.foto_perfil))
    return render_template('editarperfil.html', foto_perfil=foto_perfil, form=form)


@app.route('/post/<post_id>', methods=['GET', 'POST'])
@login_required
def exibir_post(post_id):
    post = Post.query.get(post_id)
    if current_user == post.autor:
        form = FormCriarPost()
        if request.method == 'GET':
            form.titulo.data = post.titulo
            form.corpo.data = post.corpo
        elif form.validate_on_submit():
            post.titulo = form.titulo.data
            post.corpo = form.corpo.data
            database.session.commit()
            flash('Post Atualizado com Sucesso', 'alert-success')
            return redirect(url_for('home'))
    else:
        form = None
    return render_template('post.html', post=post, form=form)


@app.route('/post/<post_id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_post(post_id):
    post = Post.query.get(post_id)
    if current_user == post.autor:
        database.session.delete(post)
        database.session.commit()
        flash('Post Excluído com Sucesso', 'alert-danger')
        return redirect(url_for('home'))
    else:
        abort(403)


@app.route('/jogos', methods=['GET', 'POST'])
@login_required
def jogos():
    url1 = "https://api.rawg.io/api/games/3498?key=c0d4bc0eb65a4a2daeabc1e8c6a07390"
    jogo1 = requests.request("GET", url1).json()
    url2 = "https://api.rawg.io/api/games/3328?key=c0d4bc0eb65a4a2daeabc1e8c6a07390"
    jogo2 = requests.request("GET", url2).json()
    url3 = "https://api.rawg.io/api/games/4291?key=c0d4bc0eb65a4a2daeabc1e8c6a07390"
    jogo3 = requests.request("GET", url3).json()
    lista_jogos = [jogo1, jogo2, jogo3]

    form = FormJogos()
    lista_jogos_usuario = list(map(lambda x: x.titulo, current_user.jogos))
    if form.validate_on_submit():
        for jogo in current_user.jogos:
            database.session.delete(jogo)
        for campo in form:
            if campo.name == 'jogo':
                if campo.data:
                    for valor in campo.raw_data:
                        jogo_adicionado = Jogo(usuario=current_user, titulo=valor)
                        database.session.add(jogo_adicionado)
        database.session.commit()
        flash('Jogos atualizados com sucesso.', 'alert-success')
        return redirect(url_for('home'))

    return render_template('jogos.html', jogos=lista_jogos, form=form, jogos_usuario=lista_jogos_usuario)


@app.route('/exportar')
@login_required
def exportar_dados():
    caminho_db = os.path.join(os.sep, 'c:\\', 'Users', 'silas', 'PycharmProjects', 'ProjetoP2', 'instance', 'forum.db')
    pasta_destino_json = os.path.join(os.sep, 'c:\\', 'Users', 'silas', 'PycharmProjects', 'ProjetoP2', 'db_json')
    pasta_destino_zip = os.path.join(os.sep, 'c:\\', 'Users', 'silas', 'PycharmProjects', 'ProjetoP2')
    sqliteToJson(caminho_db, pasta_destino_json)
    compactar(pasta_destino_json, pasta_destino_zip)
    flash('Dados exportados com sucesso!', 'alert-success')
    return redirect(url_for('home'))
