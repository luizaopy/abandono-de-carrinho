# Abandono de Carrinho

API REST para detecção e recuperação de **carrinhos de e-commerce abandonados**. O sistema acompanha o ciclo de vida dos carrinhos (aberto → finalizado ou abandonado), identifica automaticamente aqueles que ficaram inativos por tempo demais, marca-os como abandonados e dispara um e-mail de recuperação para o cliente, registrando cada tentativa de envio em um log de auditoria.

## Stack

- **Python 3.12**
- **Flask 3** — framework web / camada HTTP
- **Flask-SQLAlchemy 3 / SQLAlchemy 2** — ORM e mapeamento das entidades
- **SQLite** — banco de dados local (padrão), configurável via `DATABASE_URL`
- **APScheduler 3** — agendador embutido que roda a verificação de abandono em background
- **marshmallow 3** — validação e desserialização dos payloads de entrada
- **SMTP** (`smtplib` da biblioteca padrão) — envio dos e-mails de recuperação
- **python-dotenv** — carregamento das variáveis de ambiente do arquivo `.env`
- **pytest 8** — testes de fumaça da API

## Arquitetura

O projeto segue uma separação por camadas: as *rotas* cuidam apenas do HTTP, os *services* concentram a regra de negócio (sem conhecer HTTP) e os *models* representam os dados. Isso mantém cada camada testável e independente.

```
abandono-de-carrinho/
├── app.py                  # Application Factory: cria o app, registra blueprints,
│                           # error handlers e inicia o scheduler
├── config.py               # Configuração central (lê variáveis de ambiente)
│
├── models/                 # Entidades SQLAlchemy (camada de dados)
│   ├── __init__.py         #   instância única do db (SQLAlchemy)
│   ├── cliente.py          #   Cliente
│   ├── produto.py          #   Produto (com estoque)
│   ├── carrinho.py         #   Carrinho + enum StatusCarrinho
│   ├── item_carrinho.py    #   ItemCarrinho (associação carrinho↔produto)
│   └── email_log.py        #   EmailLog (auditoria dos envios)
│
├── routes/                 # Blueprints Flask (camada HTTP)
│   ├── clientes.py         #   CRUD de clientes
│   ├── produtos.py         #   CRUD de produtos
│   ├── carrinhos.py        #   operações de carrinho e checkout
│   ├── dashboard.py        #   métricas agregadas
│   └── jobs.py             #   disparo manual da verificação de abandono
│
├── schemas/                # Schemas marshmallow (validação de entrada)
│   ├── cliente_schema.py
│   ├── produto_schema.py
│   └── carrinho_schema.py
│
├── services/               # Regra de negócio (independente de HTTP)
│   ├── carrinho_service.py #   detecção de carrinhos abandonados
│   ├── email_service.py    #   envio de e-mails via SMTP
│   └── scheduler.py        #   configuração do job periódico (APScheduler)
│
├── utils/
│   └── responses.py        # Padroniza o formato JSON de sucesso/erro
│
├── tests/
│   └── test_api.py         # Smoke tests da API (pytest)
│
├── database/               # Banco SQLite local (ignorado pelo Git)
├── requirements.txt        # Dependências do projeto
├── postman_collection.json # Coleção Postman para testar os endpoints
└── .env.example            # Modelo das variáveis de ambiente
```

## Fluxo de detecção de abandono

O modelo `Carrinho` possui três status (`ABERTO`, `FINALIZADO`, `ABANDONADO`) e um campo `ultimo_acesso`. Toda vez que o carrinho é manipulado (produto adicionado/removido ou checkout), o `ultimo_acesso` é atualizado para o instante atual.

A verificação de abandono acontece em `services/carrinho_service.py` (`verificar_carrinhos_abandonados`) e funciona assim:

1. Calcula o limite de inatividade: `agora - CARRINHO_TIMEOUT_MINUTOS`.
2. Busca todos os carrinhos com status `ABERTO` cujo `ultimo_acesso` é anterior a esse limite.
3. Para cada carrinho encontrado:
   - marca o status como `ABANDONADO`;
   - tenta enviar o e-mail de recuperação via `EmailService`;
   - registra um `EmailLog` com o resultado (`SUCESSO` ou `ERRO`, e o detalhe do erro quando houver).
4. Uma falha de envio não interrompe o processamento dos demais carrinhos — o erro é capturado, logado e a execução continua.
5. Ao final, retorna um resumo: `carrinhos_processados`, `emails_enviados` e `emails_com_erro`.

Essa verificação é disparada de duas formas:

- **Automaticamente**, pelo `services/scheduler.py`, que registra um job do APScheduler executado a cada `SCHEDULER_INTERVAL_MINUTES` minutos (iniciado junto com o app em `python app.py`).
- **Manualmente**, pelo endpoint `POST /jobs/verificar-carrinhos`, útil para testes e demonstrações sem esperar o intervalo do agendador.

Como só carrinhos `ABERTO` são elegíveis e eles passam a `ABANDONADO` na primeira execução, cada carrinho é notificado uma única vez — não há reenvio em execuções subsequentes. O `EmailLog` complementa isso servindo de trilha de auditoria de todos os disparos (bem-sucedidos ou não).

## Endpoints

Todas as respostas seguem um envelope JSON padronizado (`utils/responses.py`):

```json
// sucesso
{ "success": true,  "message": "...", "data": { } }
// erro
{ "success": false, "message": "...", "errors": [ ] }
```

### Clientes — `routes/clientes.py`

| Método | Path                  | Descrição                                                        |
|--------|-----------------------|------------------------------------------------------------------|
| GET    | `/clientes`           | Lista todos os clientes (ordenados por id).                      |
| GET    | `/clientes/<id>`      | Retorna um cliente específico.                                   |
| POST   | `/clientes`           | Cria um cliente (`nome`, `email`). E-mail duplicado retorna 409. |
| PUT    | `/clientes/<id>`      | Atualiza `nome` e/ou `email` de um cliente.                      |
| DELETE | `/clientes/<id>`      | Remove um cliente.                                               |

### Produtos — `routes/produtos.py`

| Método | Path                  | Descrição                                                     |
|--------|-----------------------|--------------------------------------------------------------|
| GET    | `/produtos`           | Lista todos os produtos (ordenados por id).                  |
| GET    | `/produtos/<id>`      | Retorna um produto específico.                               |
| POST   | `/produtos`           | Cria um produto (`nome`, `preco`, `estoque`).                |
| PUT    | `/produtos/<id>`      | Atualiza `nome`, `preco` e/ou `estoque`.                     |
| DELETE | `/produtos/<id>`      | Remove um produto.                                           |

### Carrinhos — `routes/carrinhos.py`

| Método | Path                                        | Descrição                                                                                          |
|--------|---------------------------------------------|----------------------------------------------------------------------------------------------------|
| POST   | `/carrinhos`                                | Cria um carrinho `ABERTO` para um `cliente_id`.                                                     |
| GET    | `/carrinhos`                                | Lista carrinhos. Aceita filtro `?status=ABERTO\|FINALIZADO\|ABANDONADO`.                            |
| GET    | `/carrinhos/<id>`                           | Retorna um carrinho com seus itens e total.                                                        |
| POST   | `/carrinhos/<id>/produto`                   | Adiciona produto ao carrinho (`produto_id`, `quantidade`). Valida estoque e status `ABERTO`.       |
| DELETE | `/carrinhos/<id>/produto/<produto_id>`      | Remove um produto do carrinho.                                                                     |
| POST   | `/carrinhos/<id>/checkout`                  | Finaliza o carrinho, baixa o estoque e marca como `FINALIZADO` (permite recuperar um `ABANDONADO`). |

### Dashboard — `routes/dashboard.py`

| Método | Path          | Descrição                                                                                                   |
|--------|---------------|-------------------------------------------------------------------------------------------------------------|
| GET    | `/dashboard`  | Métricas agregadas: totais de clientes/produtos, carrinhos por status, e-mails enviados e compras recuperadas. |

### Jobs — `routes/jobs.py`

| Método | Path                        | Descrição                                                                        |
|--------|-----------------------------|----------------------------------------------------------------------------------|
| POST   | `/jobs/verificar-carrinhos` | Dispara manualmente a verificação de carrinhos abandonados e retorna o resumo.   |

## Variáveis de ambiente

Lidas em `config.py` (via `python-dotenv`). Um modelo está em `.env.example`.

| Variável                     | Padrão                                        | Descrição                                                        |
|------------------------------|-----------------------------------------------|------------------------------------------------------------------|
| `SECRET_KEY`                 | `dev-secret-key`                              | Chave secreta do Flask.                                          |
| `DATABASE_URL`               | `sqlite:///<projeto>/database/database.db`    | URI de conexão do banco (SQLAlchemy).                           |
| `SMTP_SERVER`                | `smtp.gmail.com`                              | Servidor SMTP para envio dos e-mails.                           |
| `SMTP_PORT`                  | `587`                                         | Porta SMTP (STARTTLS).                                          |
| `SMTP_USER`                  | *(vazio)*                                     | Usuário/e-mail remetente.                                       |
| `SMTP_PASSWORD`              | *(vazio)*                                     | Senha (recomenda-se senha de app, no caso do Gmail).           |
| `CARRINHO_TIMEOUT_MINUTOS`   | `30`                                          | Minutos de inatividade até um carrinho ser considerado abandonado. |
| `SCHEDULER_INTERVAL_MINUTES` | `5`                                           | Intervalo, em minutos, entre execuções automáticas da verificação. |

> **Nota:** o `.env` real **não** é versionado (está no `.gitignore`). Use o `.env.example` como base.

## Como rodar localmente

Pré-requisito: **Python 3.12**.

```bash
# 1. Clonar o repositório
git clone https://github.com/luizaopy/abandono-de-carrinho.git
cd abandono-de-carrinho

# 2. Criar e ativar o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Configurar as variáveis de ambiente
cp .env.example .env
# edite o .env com suas credenciais SMTP (e demais valores, se quiser)

# 5. Rodar a aplicação
python app.py
```

A API sobe em `http://localhost:5000`. O banco SQLite e as tabelas são criados automaticamente na primeira execução, e o scheduler de verificação inicia junto com o app.

Para testar rapidamente, importe o `postman_collection.json` no Postman.

### Rodando os testes

```bash
pytest tests/ -v
```

## Pontos técnicos para destacar

- **Application Factory (`create_app`)** — o app é construído por uma função, o que facilita a injeção de configurações de teste (o `tests/test_api.py` sobe uma instância isolada com banco temporário) e evita estado global.
- **Separação de responsabilidades em camadas** — rotas (HTTP) → services (regra de negócio) → models (dados). Os services (`carrinho_service`, `email_service`) não conhecem Flask-request nem rotas, o que os torna reutilizáveis pelo scheduler e testáveis isoladamente.
- **Scheduler embutido (APScheduler)** — a verificação de abandono roda em background dentro do próprio processo, sem necessidade de um worker externo, abrindo um `app_context` dedicado para acessar o banco.
- **Trilha de auditoria com `EmailLog`** — cada tentativa de envio é registrada (sucesso/erro + detalhe). Combinada com a transição de status `ABERTO → ABANDONADO`, garante que cada carrinho seja notificado uma única vez e mantém histórico para o dashboard (métrica de "compras recuperadas").
- **Respostas JSON padronizadas + error handlers** — `utils/responses.py` centraliza o envelope de sucesso/erro, e `app.py` registra handlers para 404, 405 e 500, de modo que até os erros seguem o mesmo contrato da API.
- **Validação de entrada com marshmallow** — todos os payloads passam por schemas com regras (e-mail válido, preço/estoque não negativos, quantidade mínima), retornando 422 com os erros de campo quando inválidos.
- **Regras de negócio consistentes** — checagem de estoque na adição e no checkout, bloqueio de alteração em carrinhos não-abertos (409) e possibilidade de "recuperar" um carrinho abandonado ao finalizá-lo.

## Possíveis evoluções

- **Autenticação e autorização** (ex.: JWT) para proteger os endpoints de escrita e o dashboard.
- **Migrações de banco com Alembic/Flask-Migrate**, substituindo o `db.create_all()` para versionar a evolução do schema com segurança.
- **Envio de e-mail assíncrono / fila** (Celery + Redis, por exemplo) para não bloquear o job em envios lentos e permitir *retry* automático de falhas registradas no `EmailLog`.
- **Templates de e-mail e múltiplos lembretes** — mensagens em HTML mais ricas e uma sequência de lembretes (ex.: 30 min, 24 h, 72 h) com cupom de desconto progressivo.
- **Observabilidade** — trocar os `print` por logging estruturado e expor métricas (Prometheus) e testes de cobertura mais amplos.
