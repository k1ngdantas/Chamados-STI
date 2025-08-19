from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chamados_bda_amv_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chamados.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False  # Para desenvolvimento local
app.config['SESSION_COOKIE_HTTPONLY'] = False  # Para permitir acesso via JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Para permitir cross-origin

# Configuração CORS para permitir cookies
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

db = SQLAlchemy(app)

# Modelos do banco de dados
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    identidade_militar = db.Column(db.String(10), unique=True, nullable=False)  # 10 dígitos numéricos
    senha = db.Column(db.String(200), nullable=False)
    nivel = db.Column(db.String(20), nullable=False)  # usuario, gestor, tecnico
    secao = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

class Chamado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(20), nullable=False)  # baixa, media, alta, critica
    status = db.Column(db.String(20), default='aberto')  # aberto, em_andamento, resolvido, fechado
    categoria = db.Column(db.String(50), nullable=False)
    solucao = db.Column(db.Text)  # Solução do chamado quando fechado
    solicitante_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tecnico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    data_abertura = db.Column(db.DateTime, default=datetime.utcnow)
    data_fechamento = db.Column(db.DateTime)
    comentarios = db.relationship('Comentario', backref='chamado', lazy=True)
    
    # Relacionamentos
    solicitante = db.relationship('Usuario', foreign_keys=[solicitante_id], backref='chamados_solicitados')
    tecnico = db.relationship('Usuario', foreign_keys=[tecnico_id], backref='chamados_atendidos')

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamado.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    usuario = db.relationship('Usuario', backref='comentarios')

class MensagemChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    chamado_id = db.Column(db.Integer, db.ForeignKey('chamado.id'), nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    lida = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='mensagens_chat')
    chamado = db.relationship('Chamado', backref='mensagens_chat')

class Agenda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    assunto = db.Column(db.Text, nullable=False)
    data = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    link_videoconferencia = db.Column(db.String(500), nullable=False)
    sala = db.Column(db.String(20), nullable=False)  # sala 1 ou sala 2
    organizador_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    organizador = db.relationship('Usuario', backref='agendas_organizadas')

# Função para verificar se o usuário está logado
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Função para verificar nível de acesso
def nivel_required(nivel):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            usuario = db.session.get(Usuario, session['user_id'])
            if not usuario or usuario.nivel != nivel:
                flash('Acesso negado. Nível de permissão insuficiente.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identidade_militar = request.form['identidade_militar']
        senha = request.form['senha']
        
        usuario = Usuario.query.filter_by(identidade_militar=identidade_militar).first()
        
        if usuario and check_password_hash(usuario.senha, senha):
            session['user_id'] = usuario.id
            session['user_nome'] = usuario.nome
            session['user_nivel'] = usuario.nivel
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Identidade Militar ou senha incorretos.', 'error')
    
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    identidade_militar = data.get('username')  # React envia 'username' (será a identidade militar)
    senha = data.get('password')
    
    usuario = Usuario.query.filter_by(identidade_militar=identidade_militar).first()
    
    if usuario and check_password_hash(usuario.senha, senha):
        # Configurar a sessão
        session['user_id'] = usuario.id
        session['user_nome'] = usuario.nome
        session['user_nivel'] = usuario.nivel
        
        response = jsonify({
            'success': True,
            'user': {
                'id': usuario.id,
                'nome': usuario.nome,
                'identidade_militar': usuario.identidade_militar,
                'nivel': usuario.nivel,
                'secao': usuario.secao
            }
        })
        
        # Configurar cookies da sessão
        response.set_cookie(
            'session',
            session.sid if hasattr(session, 'sid') else 'session_cookie',
            max_age=3600,  # 1 hora
            httponly=False,
            samesite='Lax',
            secure=False  # False para desenvolvimento local
        )
        
        return response
    else:
        return jsonify({
            'success': False,
            'message': 'Identidade Militar ou senha incorretos.'
        }), 401

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    usuario = db.session.get(Usuario, session['user_id'])
    
    if usuario.nivel == 'usuario':
        chamados = Chamado.query.filter_by(solicitante_id=usuario.id).order_by(Chamado.data_abertura.desc()).all()
        return render_template('dashboard_usuario.html', usuario=usuario, chamados=chamados)
    
    elif usuario.nivel == 'gestor':
        # Buscar todos os chamados da seção
        chamados = Chamado.query.join(Usuario, Chamado.solicitante_id == Usuario.id).filter(
            Usuario.secao == usuario.secao
        ).order_by(Chamado.data_abertura.desc()).all()
        
        # Separar chamados sem técnico
        chamados_sem_tecnico = [c for c in chamados if not c.tecnico_id]
        
        tecnicos = Usuario.query.filter_by(nivel='tecnico').all()
        return render_template('dashboard_gestor.html', usuario=usuario, chamados=chamados, 
                             chamados_sem_tecnico=chamados_sem_tecnico, tecnicos=tecnicos)
    
    elif usuario.nivel == 'tecnico':
        # Técnicos só veem chamados que foram atribuídos a eles
        chamados = Chamado.query.filter_by(tecnico_id=usuario.id).order_by(Chamado.data_abertura.desc()).all()
        # Não mostrar chamados abertos sem atribuição na dashboard do técnico
        return render_template('dashboard_tecnico.html', usuario=usuario, chamados=chamados, chamados_abertos=[])

@app.route('/novo_chamado', methods=['GET', 'POST'])
@login_required
def novo_chamado():
    if request.method == 'POST':
        titulo = request.form['titulo']
        descricao = request.form['descricao']
        prioridade = request.form['prioridade']
        categoria = request.form['categoria']
        
        novo_chamado = Chamado(
            titulo=titulo,
            descricao=descricao,
            prioridade=prioridade,
            categoria=categoria,
            solicitante_id=session['user_id']
        )
        
        db.session.add(novo_chamado)
        db.session.commit()
        
        flash('Chamado criado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('novo_chamado.html')

@app.route('/chamado/<int:chamado_id>')
@login_required
def visualizar_chamado(chamado_id):
    chamado = Chamado.query.get_or_404(chamado_id)
    usuario = db.session.get(Usuario, session['user_id'])
    
    # Verificar se o usuário tem permissão para ver o chamado
    if usuario.nivel == 'usuario' and chamado.solicitante_id != usuario.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    comentarios = Comentario.query.filter_by(chamado_id=chamado_id).order_by(Comentario.data_criacao).all()
    tecnicos = Usuario.query.filter_by(nivel='tecnico').all() if usuario.nivel == 'gestor' else []
    
    return render_template('visualizar_chamado.html', chamado=chamado, usuario=usuario, comentarios=comentarios, tecnicos=tecnicos)

@app.route('/chat/<int:chamado_id>')
@login_required
def chat(chamado_id):
    usuario = db.session.get(Usuario, session['user_id'])
    chamado = db.session.get(Chamado, chamado_id)
    if not chamado:
        flash('Chamado não encontrado.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verificar se o usuário tem permissão para acessar o chat
    if (usuario.nivel == 'usuario' and chamado.solicitante_id != usuario.id) or \
       (usuario.nivel == 'tecnico' and chamado.tecnico_id != usuario.id) or \
       (usuario.nivel == 'gestor' and chamado.solicitante.secao != usuario.secao):
        flash('Você não tem permissão para acessar este chat.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verificar se o chamado está em andamento
    if chamado.status != 'em_andamento':
        flash('O chat só está disponível para chamados em andamento.', 'error')
        return redirect(url_for('visualizar_chamado', chamado_id=chamado_id))
    
    return render_template('chat.html', chamado=chamado, usuario=usuario)

@app.route('/chamado/<int:chamado_id>/comentar', methods=['POST'])
@login_required
def comentar_chamado(chamado_id):
    texto = request.form['comentario']
    
    novo_comentario = Comentario(
        texto=texto,
        usuario_id=session['user_id'],
        chamado_id=chamado_id
    )
    
    db.session.add(novo_comentario)
    db.session.commit()
    
    flash('Comentário adicionado com sucesso!', 'success')
    return redirect(url_for('visualizar_chamado', chamado_id=chamado_id))

@app.route('/chamado/<int:chamado_id>/atualizar_status', methods=['POST'])
@login_required
def atualizar_status_chamado(chamado_id):
    usuario = db.session.get(Usuario, session['user_id'])
    chamado = Chamado.query.get_or_404(chamado_id)
    
    if usuario.nivel not in ['gestor', 'tecnico']:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    novo_status = request.form['status']
    chamado.status = novo_status
    
    if novo_status == 'fechado':
        chamado.data_fechamento = datetime.utcnow()
    
    db.session.commit()
    flash('Status do chamado atualizado com sucesso!', 'success')
    return redirect(url_for('visualizar_chamado', chamado_id=chamado_id))

@app.route('/chamado/<int:chamado_id>/atribuir_tecnico', methods=['POST'])
@nivel_required('gestor')
def atribuir_tecnico(chamado_id):
    chamado = Chamado.query.get_or_404(chamado_id)
    tecnico_id = request.form['tecnico_id']
    
    # Buscar o técnico
    tecnico = db.session.get(Usuario, tecnico_id)
    if not tecnico or tecnico.nivel != 'tecnico':
        flash('Técnico não encontrado!', 'error')
        return redirect(url_for('visualizar_chamado', chamado_id=chamado_id))
    
    chamado.tecnico_id = tecnico_id
    db.session.commit()
    
    flash(f'Chamado #{chamado.id} atribuído com sucesso ao técnico {tecnico.nome}!', 'success')
    return redirect(url_for('dashboard'))

# API para atribuir técnico (React)
@app.route('/api/chamado/<int:chamado_id>/atribuir_tecnico', methods=['POST'])
# @nivel_required('gestor') # Removido para desenvolvimento
def api_atribuir_tecnico(chamado_id):
    try:
        data = request.get_json()
        tecnico_id = data.get('tecnico_id')
        
        if not tecnico_id:
            return jsonify({'error': 'ID do técnico é obrigatório'}), 400
        
        chamado = Chamado.query.get_or_404(chamado_id)
        tecnico = db.session.get(Usuario, tecnico_id)
        
        if not tecnico or tecnico.nivel != 'tecnico':
            return jsonify({'error': 'Técnico não encontrado'}), 404
        
        chamado.tecnico_id = tecnico_id
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Chamado #{chamado.id} atribuído com sucesso ao técnico {tecnico.nome}!',
            'chamado': {
                'id': chamado.id,
                'tecnico_id': chamado.tecnico_id,
                'tecnico_nome': tecnico.nome
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# API para buscar técnicos
@app.route('/api/tecnicos', methods=['GET'])
# @nivel_required('gestor') # Removido para desenvolvimento
def api_tecnicos():
    try:
        tecnicos = Usuario.query.filter_by(nivel='tecnico').all()
        return jsonify([{
            'id': tecnico.id,
            'nome': tecnico.nome,
            'identidade_militar': tecnico.identidade_militar
        } for tecnico in tecnicos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API para alterar status do chamado (React)
@app.route('/api/chamado/<int:chamado_id>/alterar_status', methods=['POST'])
# @login_required # Removido para desenvolvimento
def api_alterar_status_chamado(chamado_id):
    try:
        data = request.get_json()
        novo_status = data.get('status')
        solucao = data.get('solucao', '')
        # Tratar solução que pode ser None ou string
        if solucao is not None:
            solucao = solucao.strip()
        else:
            solucao = ''
        usuario_id = data.get('usuario_id', 1)  # ID do usuário logado
        
        if not novo_status:
            return jsonify({'error': 'Status é obrigatório'}), 400
        
        # Validar status permitidos
        status_permitidos = ['aberto', 'em_andamento', 'fechado']
        if novo_status not in status_permitidos:
            return jsonify({'error': 'Status inválido'}), 400
        
        # Se for fechar, validar se tem solução
        if novo_status == 'fechado' and not solucao:
            return jsonify({'error': 'É obrigatório informar a solução para fechar o chamado'}), 400
        
        chamado = Chamado.query.get_or_404(chamado_id)
        usuario = db.session.get(Usuario, usuario_id)
        
        # Verificar se o usuário tem permissão (gestor ou técnico)
        if not usuario or usuario.nivel not in ['gestor', 'tecnico']:
            return jsonify({'error': 'Acesso negado'}), 403
        
        # Se for técnico, verificar se é o técnico atribuído ao chamado
        if usuario.nivel == 'tecnico' and chamado.tecnico_id != usuario_id:
            return jsonify({'error': 'Apenas o técnico atribuído pode alterar o status'}), 403
        
        # Se o chamado estiver fechado, apenas gestores podem alterar
        if chamado.status == 'fechado' and usuario.nivel != 'gestor':
            return jsonify({'error': 'Apenas gestores podem alterar o status de chamados fechados'}), 403
        
        # Alterar status
        chamado.status = novo_status
        
        # Se fechado, definir data de fechamento e solução
        if novo_status == 'fechado':
            chamado.data_fechamento = datetime.utcnow()
            chamado.solucao = solucao
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status do chamado #{chamado.id} alterado para "{novo_status}" com sucesso!',
            'chamado': {
                'id': chamado.id,
                'status': chamado.status,
                'solucao': chamado.solucao,
                'data_fechamento': chamado.data_fechamento.strftime('%d/%m/%Y %H:%M') if chamado.data_fechamento else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500





@app.route('/api/chat/<int:chamado_id>/mensagens')
def api_mensagens_chat(chamado_id):
    # Para desenvolvimento, retornar todas as mensagens
    # Em produção, isso deveria verificar autenticação via token
    chamado = Chamado.query.get_or_404(chamado_id)
    
    # Buscar mensagens
    mensagens = MensagemChat.query.filter_by(chamado_id=chamado_id).order_by(MensagemChat.data_envio).all()
    
    return jsonify([{
        'id': m.id,
        'texto': m.texto,
        'usuario_id': m.usuario_id,
        'usuario_nome': m.usuario.nome,
        'usuario_nivel': m.usuario.nivel,
        'data_envio': m.data_envio.strftime('%d/%m/%Y %H:%M'),
        'lida': m.lida
    } for m in mensagens])

@app.route('/api/chat/<int:chamado_id>/enviar', methods=['POST'])
def api_enviar_mensagem(chamado_id):
    # Para desenvolvimento, permitir envio de mensagens
    # Em produção, isso deveria verificar autenticação via token
    chamado = Chamado.query.get_or_404(chamado_id)
    
    # Obter dados da requisição
    data = request.json
    texto = data.get('texto', '').strip()
    usuario_id = data.get('usuario_id', 1)  # Usar ID do frontend ou padrão 1
    
    # Verificar se o chamado está em andamento
    if chamado.status != 'em_andamento':
        return jsonify({'error': 'Chat não disponível'}), 400
    
    if not texto:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    # Criar nova mensagem
    nova_mensagem = MensagemChat(
        texto=texto,
        usuario_id=usuario_id,
        chamado_id=chamado_id
    )
    
    db.session.add(nova_mensagem)
    db.session.commit()
    
    return jsonify({
        'id': nova_mensagem.id,
        'texto': nova_mensagem.texto,
        'usuario_id': nova_mensagem.usuario_id,
        'usuario_nome': nova_mensagem.usuario.nome,
        'usuario_nivel': nova_mensagem.usuario.nivel,
        'data_envio': nova_mensagem.data_envio.strftime('%d/%m/%Y %H:%M'),
        'lida': nova_mensagem.lida
    })

@app.route('/api/estatisticas')
def estatisticas():
    # Para desenvolvimento, retornar estatísticas de todos os chamados
    # Em produção, isso deveria verificar autenticação via token
    total = Chamado.query.count()
    aberto = Chamado.query.filter_by(status='aberto').count()
    em_andamento = Chamado.query.filter_by(status='em_andamento').count()
    resolvido = Chamado.query.filter_by(status='fechado').count()
    total_usuarios = Usuario.query.count()
    
    return jsonify({
        'total_chamados': total,
        'chamados_abertos': aberto,
        'chamados_andamento': em_andamento,
        'chamados_fechados': resolvido,
        'total_usuarios': total_usuarios
    })

@app.route('/api/chamados', methods=['GET', 'POST'])
def api_chamados():
    if request.method == 'GET':
        # Para desenvolvimento, retornar todos os chamados
        # Em produção, isso deveria verificar autenticação via token
        chamados = Chamado.query.order_by(Chamado.data_abertura.desc()).all()
        
        chamados_data = []
        for chamado in chamados:
            chamados_data.append({
                'id': chamado.id,
                'titulo': chamado.titulo,
                'descricao': chamado.descricao,
                'prioridade': chamado.prioridade,
                'status': chamado.status,
                'categoria': chamado.categoria,
                'solucao': chamado.solucao,
                'data_criacao': chamado.data_abertura.strftime('%d/%m/%Y %H:%M'),
                'data_fechamento': chamado.data_fechamento.strftime('%d/%m/%Y %H:%M') if chamado.data_fechamento else None,
                'solicitante': {
                    'id': chamado.solicitante.id,
                    'nome': chamado.solicitante.nome
                } if chamado.solicitante else None,
                'tecnico': {
                    'id': chamado.tecnico.id,
                    'nome': chamado.tecnico.nome
                } if chamado.tecnico else None
            })
        
        return jsonify(chamados_data)
    
    elif request.method == 'POST':
        # Criar novo chamado
        try:
            data = request.get_json()
            
            # Validações
            if not data.get('titulo') or not data.get('descricao') or not data.get('prioridade') or not data.get('categoria'):
                return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
            
            # Validar prioridade
            prioridades_validas = ['baixa', 'media', 'alta', 'critica']
            if data['prioridade'] not in prioridades_validas:
                return jsonify({'error': 'Prioridade inválida'}), 400
            
            # Validar categoria
            categorias_validas = ['Hardware', 'Software', 'Rede', 'Outros']
            if data['categoria'] not in categorias_validas:
                return jsonify({'error': 'Categoria inválida'}), 400
            
            # Criar chamado
            novo_chamado = Chamado(
                titulo=data['titulo'],
                descricao=data['descricao'],
                prioridade=data['prioridade'],
                categoria=data['categoria'],
                solicitante_id=data.get('solicitante_id', 1),  # Default para desenvolvimento
                status='aberto'
            )
            
            db.session.add(novo_chamado)
            db.session.commit()
            
            return jsonify({
                'id': novo_chamado.id,
                'titulo': novo_chamado.titulo,
                'descricao': novo_chamado.descricao,
                'prioridade': novo_chamado.prioridade,
                'status': novo_chamado.status,
                'categoria': novo_chamado.categoria,
                'data_criacao': novo_chamado.data_abertura.strftime('%d/%m/%Y %H:%M'),
                'solicitante': {
                    'id': novo_chamado.solicitante.id,
                    'nome': novo_chamado.solicitante.nome
                } if novo_chamado.solicitante else None
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/api/chamado/<int:chamado_id>')
def api_chamado(chamado_id):
    # Para desenvolvimento, retornar dados do chamado
    # Em produção, isso deveria verificar autenticação via token
    chamado = Chamado.query.get_or_404(chamado_id)
    
    return jsonify({
        'id': chamado.id,
        'titulo': chamado.titulo,
        'descricao': chamado.descricao,
        'prioridade': chamado.prioridade,
        'status': chamado.status,
        'categoria': chamado.categoria,
        'solucao': chamado.solucao,
        'data_criacao': chamado.data_abertura.strftime('%d/%m/%Y %H:%M'),
        'data_fechamento': chamado.data_fechamento.strftime('%d/%m/%Y %H:%M') if chamado.data_fechamento else None,
        'solicitante': {
            'id': chamado.solicitante.id,
            'nome': chamado.solicitante.nome
        } if chamado.solicitante else None,
        'tecnico': {
            'id': chamado.tecnico.id,
            'nome': chamado.tecnico.nome
        } if chamado.tecnico else None
    })

# ===== ROTAS PARA GERENCIAMENTO DE USUÁRIOS =====

@app.route('/api/usuarios', methods=['GET'])
def api_usuarios():
    """Listar todos os usuários (apenas para gestores)"""
    try:
        # Para desenvolvimento, retornar todos os usuários
        # Em produção, verificar se o usuário logado é gestor
        usuarios = Usuario.query.order_by(Usuario.nome).all()
        
        usuarios_data = []
        for usuario in usuarios:
            usuarios_data.append({
                'id': usuario.id,
                'nome': usuario.nome,
                'identidade_militar': usuario.identidade_militar,
                'nivel': usuario.nivel,
                'secao': usuario.secao,
                'data_criacao': usuario.data_criacao.strftime('%d/%m/%Y %H:%M') if usuario.data_criacao else None
            })
        
        return jsonify(usuarios_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios', methods=['POST'])
def api_criar_usuario():
    """Criar novo usuário (apenas para gestores)"""
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('nome') or not data.get('identidade_militar') or not data.get('senha') or not data.get('nivel'):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
        
        # Validar formato da identidade militar (10 dígitos numéricos)
        identidade_militar = data['identidade_militar']
        if not identidade_militar.isdigit() or len(identidade_militar) != 10:
            return jsonify({'error': 'Identidade Militar deve ter exatamente 10 dígitos numéricos'}), 400
        
        # Verificar se identidade militar já existe
        if Usuario.query.filter_by(identidade_militar=identidade_militar).first():
            return jsonify({'error': 'Identidade Militar já cadastrada'}), 400
        
        # Validar nível
        niveis_validos = ['usuario', 'tecnico', 'gestor']
        if data['nivel'] not in niveis_validos:
            return jsonify({'error': 'Nível inválido'}), 400
        
        # Criar usuário
        novo_usuario = Usuario(
            nome=data['nome'],
            identidade_militar=identidade_militar,
            senha=generate_password_hash(data['senha']),
            nivel=data['nivel'],
            secao=data.get('secao', 'TI')
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário criado com sucesso',
            'usuario': {
                'id': novo_usuario.id,
                'nome': novo_usuario.nome,
                'identidade_militar': novo_usuario.identidade_militar,
                'nivel': novo_usuario.nivel,
                'secao': novo_usuario.secao,
                'data_criacao': novo_usuario.data_criacao.strftime('%d/%m/%Y %H:%M')
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['GET'])
def api_usuario(usuario_id):
    """Buscar usuário específico"""
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        return jsonify({
            'id': usuario.id,
            'nome': usuario.nome,
            'identidade_militar': usuario.identidade_militar,
            'nivel': usuario.nivel,
            'secao': usuario.secao,
            'data_criacao': usuario.data_criacao.strftime('%d/%m/%Y %H:%M') if usuario.data_criacao else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
def api_atualizar_usuario(usuario_id):
    """Atualizar usuário (apenas para gestores)"""
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        data = request.get_json()
        
        # Validações
        if not data.get('nome') or not data.get('identidade_militar') or not data.get('nivel'):
            return jsonify({'error': 'Nome, Identidade Militar e nível são obrigatórios'}), 400
        
        # Validar formato da identidade militar (10 dígitos numéricos)
        identidade_militar = data['identidade_militar']
        if not identidade_militar.isdigit() or len(identidade_militar) != 10:
            return jsonify({'error': 'Identidade Militar deve ter exatamente 10 dígitos numéricos'}), 400
        
        # Verificar se identidade militar já existe (exceto para o próprio usuário)
        identidade_existente = Usuario.query.filter_by(identidade_militar=identidade_militar).first()
        if identidade_existente and identidade_existente.id != usuario_id:
            return jsonify({'error': 'Identidade Militar já cadastrada'}), 400
        
        # Validar nível
        niveis_validos = ['usuario', 'tecnico', 'gestor']
        if data['nivel'] not in niveis_validos:
            return jsonify({'error': 'Nível inválido'}), 400
        
        # Atualizar dados
        usuario.nome = data['nome']
        usuario.identidade_militar = identidade_militar
        usuario.nivel = data['nivel']
        usuario.secao = data.get('secao', 'TI')
        
        # Atualizar senha se fornecida
        if data.get('senha'):
            usuario.senha = generate_password_hash(data['senha'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Usuário atualizado com sucesso',
            'usuario': {
                'id': usuario.id,
                'nome': usuario.nome,
                'identidade_militar': usuario.identidade_militar,
                'nivel': usuario.nivel,
                'secao': usuario.secao,
                'data_criacao': usuario.data_criacao.strftime('%d/%m/%Y %H:%M') if usuario.data_criacao else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def api_excluir_usuario(usuario_id):
    """Excluir usuário (apenas para gestores)"""
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Verificar se o usuário tem chamados associados
        chamados_solicitados = Chamado.query.filter_by(solicitante_id=usuario_id).count()
        chamados_atendidos = Chamado.query.filter_by(tecnico_id=usuario_id).count()
        
        if chamados_solicitados > 0 or chamados_atendidos > 0:
            return jsonify({
                'error': 'Não é possível excluir usuário com chamados associados',
                'chamados_solicitados': chamados_solicitados,
                'chamados_atendidos': chamados_atendidos
            }), 400
        
        # Verificar se é o último gestor
        if usuario.nivel == 'gestor':
            gestores_count = Usuario.query.filter_by(nivel='gestor').count()
            if gestores_count <= 1:
                return jsonify({'error': 'Não é possível excluir o último gestor'}), 400
        
        db.session.delete(usuario)
        db.session.commit()
        
        return jsonify({'message': 'Usuário excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Função para verificar autenticação via token (para API)
def get_user_from_token():
    """Verifica se o usuário está autenticado via token ou sessão"""
    # Primeiro tenta via sessão
    if 'user_id' in session:
        return Usuario.query.get(session['user_id'])
    
    # Se não há sessão, tenta via token no header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        # Para simplificar, vamos usar o token como user_id
        try:
            user_id = int(token)
            return Usuario.query.get(user_id)
        except (ValueError, TypeError):
            return None
    
    return None

# Rotas da API para Agenda
@app.route('/api/agenda', methods=['GET'])
def api_get_agenda():
    """Buscar eventos da agenda baseado no nível do usuário"""
    try:
        # Verificar se o usuário está logado
        user = get_user_from_token()
        
        if not user:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        # Filtrar eventos baseado no nível do usuário
        if user.nivel in ['gestor', 'agenda']:
            # Gestores e usuários agenda podem ver todos os eventos
            eventos = Agenda.query.order_by(Agenda.data.asc(), Agenda.hora_inicio.asc()).all()
        else:
            # Outros usuários só podem ver seus próprios eventos
            eventos = Agenda.query.filter_by(organizador_id=user.id).order_by(Agenda.data.asc(), Agenda.hora_inicio.asc()).all()
        
        eventos_data = []
        
        for evento in eventos:
            eventos_data.append({
                'id': evento.id,
                'titulo': evento.titulo,
                'assunto': evento.assunto,
                'data': evento.data.strftime('%Y-%m-%d'),
                'hora_inicio': evento.hora_inicio.strftime('%H:%M'),
                'hora_fim': evento.hora_fim.strftime('%H:%M'),
                'link_videoconferencia': evento.link_videoconferencia,
                'sala': evento.sala,
                'organizador_nome': evento.organizador.nome,
                'organizador_id': evento.organizador_id,
                'data_criacao': evento.data_criacao.strftime('%d/%m/%Y %H:%M') if evento.data_criacao else None
            })
        
        return jsonify(eventos_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agenda', methods=['POST'])
def api_criar_evento():
    """Criar novo evento na agenda"""
    try:
        # Verificar se o usuário está logado
        user = get_user_from_token()
        
        if not user:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        data = request.get_json()
        
        # Validações
        if not data.get('titulo') or not data.get('assunto') or not data.get('data') or not data.get('hora_inicio') or not data.get('hora_fim') or not data.get('link_videoconferencia') or not data.get('sala'):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
        
        # Validar sala
        if data['sala'] not in ['sala 1', 'sala 2']:
            return jsonify({'error': 'Sala deve ser "sala 1" ou "sala 2"'}), 400
        
        # Converter data e horas
        try:
            data_evento = datetime.strptime(data['data'], '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
            hora_fim = datetime.strptime(data['hora_fim'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de data ou hora inválido. Use YYYY-MM-DD para data e HH:MM para horas'}), 400
        
        # Verificar se hora_fim é posterior à hora_inicio
        if hora_fim <= hora_inicio:
            return jsonify({'error': 'Hora de fim deve ser posterior à hora de início'}), 400
        
        # Verificar se a sala está disponível no horário
        evento_conflitante = Agenda.query.filter(
            Agenda.sala == data['sala'],
            Agenda.data == data_evento,
            db.or_(
                db.and_(Agenda.hora_inicio <= hora_inicio, Agenda.hora_fim > hora_inicio),
                db.and_(Agenda.hora_inicio < hora_fim, Agenda.hora_fim >= hora_fim),
                db.and_(Agenda.hora_inicio >= hora_inicio, Agenda.hora_fim <= hora_fim)
            )
        ).first()
        
        if evento_conflitante:
            return jsonify({'error': f'O horário está indisponível. A {data["sala"]} já está ocupada das {evento_conflitante.hora_inicio.strftime("%H:%M")} às {evento_conflitante.hora_fim.strftime("%H:%M")} neste dia.'}), 400
        
        # Criar o evento
        novo_evento = Agenda(
            titulo=data['titulo'],
            assunto=data['assunto'],
            data=data_evento,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            link_videoconferencia=data['link_videoconferencia'],
            sala=data['sala'],
            organizador_id=user.id
        )
        
        db.session.add(novo_evento)
        db.session.commit()
        
        return jsonify({'message': 'Evento criado com sucesso!', 'id': novo_evento.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/agenda/<int:evento_id>', methods=['PUT'])
def api_atualizar_evento(evento_id):
    """Atualizar evento da agenda"""
    try:
        # Verificar se o usuário está logado
        user = get_user_from_token()
        
        if not user:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        evento = Agenda.query.get_or_404(evento_id)
        
        # Verificar permissões: apenas o organizador, gestor ou usuário agenda podem atualizar
        if user.nivel not in ['gestor', 'agenda'] and evento.organizador_id != user.id:
            return jsonify({'error': 'Você não tem permissão para atualizar este evento'}), 403
        
        data = request.get_json()
        
        # Validações
        if not data.get('titulo') or not data.get('assunto') or not data.get('data') or not data.get('hora_inicio') or not data.get('hora_fim') or not data.get('link_videoconferencia') or not data.get('sala'):
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
        
        # Validar sala
        if data['sala'] not in ['sala 1', 'sala 2']:
            return jsonify({'error': 'Sala deve ser "sala 1" ou "sala 2"'}), 400
        
        # Validar formato da data
        try:
            datetime.strptime(data['data'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Validar formato das horas
        try:
            hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M')
            hora_fim = datetime.strptime(data['hora_fim'], '%H:%M')
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400
        
        # Verificar se hora_fim é maior que hora_inicio
        
        if hora_fim <= hora_inicio:
            return jsonify({'error': 'Hora de fim deve ser maior que hora de início'}), 400
        
        # Verificar conflitos de horário (exceto o próprio evento)
        data_evento = datetime.strptime(data['data'], '%Y-%m-%d').date()
        
        conflitos = Agenda.query.filter(
            Agenda.id != evento_id,
            Agenda.data == data_evento,
            Agenda.sala == data['sala']
        ).all()
        
        for conflito in conflitos:
            conflito_inicio = conflito.hora_inicio
            conflito_fim = conflito.hora_fim
            novo_inicio = hora_inicio.time()
            novo_fim = hora_fim.time()
            
            # Verificar se há sobreposição
            if (novo_inicio < conflito_fim and novo_fim > conflito_inicio):
                return jsonify({
                    'error': f'O horário está indisponível. Conflito com evento "{conflito.titulo}" na {conflito.sala} das {conflito.hora_inicio.strftime("%H:%M")} às {conflito.hora_fim.strftime("%H:%M")}'
                }), 400
        
        # Atualizar o evento
        evento.titulo = data['titulo']
        evento.assunto = data['assunto']
        evento.data = data_evento
        evento.hora_inicio = hora_inicio.time()
        evento.hora_fim = hora_fim.time()
        evento.link_videoconferencia = data['link_videoconferencia']
        evento.sala = data['sala']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Evento atualizado com sucesso',
            'evento': {
                'id': evento.id,
                'titulo': evento.titulo,
                'assunto': evento.assunto,
                'data': evento.data.strftime('%Y-%m-%d'),
                'hora_inicio': evento.hora_inicio.strftime('%H:%M'),
                'hora_fim': evento.hora_fim.strftime('%H:%M'),
                'link_videoconferencia': evento.link_videoconferencia,
                'sala': evento.sala,
                'organizador_id': evento.organizador_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar evento: {str(e)}'}), 500

@app.route('/api/agenda/<int:evento_id>', methods=['DELETE'])
def api_excluir_evento(evento_id):
    """Excluir evento da agenda"""
    try:
        # Verificar se o usuário está logado
        user = get_user_from_token()
        
        if not user:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        evento = Agenda.query.get_or_404(evento_id)
        
        # Verificar permissões: apenas o organizador, gestor ou usuário agenda podem excluir
        if user.nivel not in ['gestor', 'agenda'] and evento.organizador_id != user.id:
            return jsonify({'error': 'Você não tem permissão para excluir este evento'}), 403
        
        db.session.delete(evento)
        db.session.commit()
        
        return jsonify({'message': 'Evento excluído com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Criar usuários padrão se não existirem
        if not Usuario.query.filter_by(identidade_militar='1234567890').first():
            admin = Usuario(
                nome='Administrador',
                identidade_militar='1234567890',
                senha=generate_password_hash('admin123'),
                nivel='gestor',
                secao='TI'
            )
            db.session.add(admin)
        
        if not Usuario.query.filter_by(identidade_militar='0987654321').first():
            tecnico = Usuario(
                nome='Técnico',
                identidade_militar='0987654321',
                senha=generate_password_hash('tecnico123'),
                nivel='tecnico',
                secao='TI'
            )
            db.session.add(tecnico)
        
        if not Usuario.query.filter_by(identidade_militar='1111111111').first():
            usuario = Usuario(
                nome='Usuário',
                identidade_militar='1111111111',
                senha=generate_password_hash('usuario123'),
                nivel='usuario',
                secao='TI'  # Mudando para TI para estar na mesma seção do gestor
            )
            db.session.add(usuario)
        
        if not Usuario.query.filter_by(identidade_militar='2222222222').first():
            agenda_user = Usuario(
                nome='Agenda',
                identidade_militar='2222222222',
                senha=generate_password_hash('agenda123'),
                nivel='agenda',
                secao='TI'
            )
            db.session.add(agenda_user)
        
        db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 