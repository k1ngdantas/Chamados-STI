<<<<<<< HEAD
# Sistema de Chamados BDA AMV

Sistema completo de gerenciamento de chamados técnicos desenvolvido em Flask com interface moderna e responsiva.

## 🚀 Características

- **3 Níveis de Usuário**: Usuário, Gestor e Técnico
- **Dashboards Diferenciados**: Cada nível possui interface específica
- **Interface Moderna**: Design responsivo com Bootstrap 5
- **Gráficos Interativos**: Estatísticas em tempo real
- **Sistema de Comentários**: Comunicação entre usuários
- **Controle de Status**: Acompanhamento completo do ciclo de vida dos chamados
- **Atribuição de Técnicos**: Gestores podem atribuir chamados aos técnicos

## 📋 Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🛠️ Instalação

1. **Clone ou baixe o projeto**
   ```bash
   cd "F:\Chamados Bda Amv"
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação**
   ```bash
   python app.py
   ```

4. **Acesse o sistema**
   - Abra seu navegador
   - Acesse: `http://localhost:5000`

## 👥 Usuários de Teste

O sistema já vem com 3 usuários pré-configurados:

### Administrador (Gestor)
- **Email**: admin@bda.com
- **Senha**: admin123
- **Nível**: Gestor
- **Departamento**: TI

### Técnico
- **Email**: tecnico@bda.com
- **Senha**: tecnico123
- **Nível**: Técnico
- **Departamento**: TI

### Usuário
- **Email**: usuario@bda.com
- **Senha**: usuario123
- **Nível**: Usuário
- **Departamento**: RH

## 🎯 Funcionalidades por Nível

### 👤 Usuário
- Criar novos chamados
- Visualizar seus chamados
- Adicionar comentários
- Acompanhar status
- Dashboard com estatísticas pessoais
- Chat em tempo real com técnico quando chamado está em andamento

### 👔 Gestor
- Visualizar todos os chamados do departamento
- Atribuir técnicos aos chamados
- Atualizar status dos chamados
- Dashboard com estatísticas do departamento
- Visualizar técnicos disponíveis

### 🔧 Técnico
- Visualizar apenas chamados atribuídos a ele
- Atualizar status dos chamados
- Adicionar comentários técnicos
- Dashboard com produtividade
- Não visualiza chamados não atribuídos
- Chat em tempo real com usuários quando chamado está em andamento

## 📊 Categorias de Chamados

- Hardware
- Software
- Rede
- Internet
- Impressora
- Email
- Sistema
- Outros

## 🚦 Níveis de Prioridade

- **Baixa**: Verde
- **Média**: Amarelo
- **Alta**: Vermelho
- **Crítica**: Preto (com animação)

## 📈 Status dos Chamados

- **Aberto**: Aguardando atendimento
- **Em Andamento**: Sendo trabalhado (chat disponível)
- **Resolvido**: Problema solucionado
- **Fechado**: Chamado finalizado

## 💬 Chat em Tempo Real

O sistema inclui um chat em tempo real estilo Messenger que é ativado quando um chamado está em status "Em Andamento":

### Características do Chat
- **Painel Lateral**: Abre na lateral direita da tela, estilo Facebook
- **Mesma Página**: Não redireciona para outra página
- **Tempo Real**: Atualização automática a cada 3 segundos
- **Indicadores Visuais**: 
  - Bolhas de mensagem diferenciadas (enviadas/recebidas)
  - Avatares com iniciais dos usuários
  - Indicadores de leitura (✓ e ✓✓)
  - Status online
- **Funcionalidades**:
  - Envio com Enter ou botão
  - Scroll automático para novas mensagens
  - Histórico completo de conversas
  - Responsivo para mobile
  - Fechar com ESC ou clicando fora
  - Overlay escuro quando aberto

### Como Usar o Chat
1. **Usuário** cria um chamado
2. **Gestor** atribui o chamado a um técnico
3. **Técnico** muda status para "Em Andamento"
4. **Chat fica disponível** para ambos (usuário e técnico)
5. **Clique em "Abrir Chat"** na página do chamado
6. **Painel lateral abre** na direita da tela
7. **Comunicação direta** em tempo real
8. **Fechar com X, ESC ou clicando fora**
9. **Técnico** pode resolver o chamado quando necessário

## 🔄 Fluxo de Trabalho

1. **Usuário** cria um chamado
2. **Gestor** visualiza o chamado na seção "Aguardando Atribuição"
3. **Gestor** atribui o chamado a um técnico específico
4. **Técnico** recebe o chamado em sua dashboard
5. **Técnico** atualiza o status conforme trabalha
6. **Usuário** acompanha o progresso do chamado

## 🏗️ Estrutura do Projeto

```
Chamados Bda Amv/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── README.md             # Documentação
├── static/               # Arquivos estáticos
│   ├── css/
│   │   └── style.css     # Estilos personalizados
│   └── js/
│       └── script.js     # JavaScript personalizado
├── templates/            # Templates HTML
│   ├── base.html         # Template base
│   ├── login.html        # Tela de login
│   ├── dashboard_usuario.html
│   ├── dashboard_gestor.html
│   ├── dashboard_tecnico.html
│   ├── novo_chamado.html
│   └── visualizar_chamado.html
└── database/             # Diretório para banco de dados
    └── chamados.db       # Banco SQLite (criado automaticamente)
```

## 🔧 Configuração

### Variáveis de Ambiente (Opcional)
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Personalização
- **Cores**: Edite `static/css/style.css`
- **Funcionalidades**: Modifique `static/js/script.js`
- **Templates**: Personalize os arquivos em `templates/`

## 📱 Responsividade

O sistema é totalmente responsivo e funciona em:
- Desktop
- Tablet
- Smartphone

## 🔒 Segurança

- Senhas criptografadas com bcrypt
- Controle de sessão
- Validação de níveis de acesso
- Proteção contra CSRF

## 🚀 Deploy

### Desenvolvimento
```bash
python app.py
```

### Produção (Recomendado)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📝 Logs

O sistema gera logs automáticos para:
- Login/logout de usuários
- Criação de chamados
- Atualizações de status
- Erros do sistema

## 🔄 Backup

O banco de dados SQLite está localizado em:
```
database/chamados.db
```

**Recomendação**: Faça backup regular deste arquivo.

## 🐛 Solução de Problemas

### Erro de Porta em Uso
```bash
# Altere a porta no app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Erro de Dependências
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Erro de Banco de Dados
```bash
# Delete o arquivo do banco e reinicie
rm database/chamados.db
python app.py
```

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Verifique os logs do sistema
- Consulte a documentação
- Teste com os usuários padrão

## 🔄 Atualizações

Para atualizar o sistema:
1. Faça backup do banco de dados
2. Atualize os arquivos
3. Execute `python app.py`

## 📄 Licença

Este projeto foi desenvolvido para a BDA AMV.

## 🎉 Agradecimentos

- Flask Framework
- Bootstrap 5
- Chart.js
- Font Awesome
- SQLAlchemy

---

**Desenvolvido com ❤️ para a BDA AMV** 
=======
# Chamados-STI
Sistema de Chamados da Bda AMV
>>>>>>> 5e1b07181ffa2a64b1fdc2558bcb2b1f2ae0a187
