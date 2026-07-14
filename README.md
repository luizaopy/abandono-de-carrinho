# Abandono de Carrinho

API REST em Flask que detecta carrinhos de e-commerce abandonados e notifica
os clientes por e-mail automaticamente, através de um scheduler que roda em
segundo plano.

## Stack

- **Python / Flask** — API REST com Application Factory e Blueprints
- **SQLAlchemy** — ORM para modelagem e persistência dos dados
- **SQLite** — banco de dados (configurável via `DATABASE_URL` para Postgres/MySQL em produção)
- **APScheduler** *(ou equivalente — ajuste aqui conforme o que você usou em `services/scheduler.py`)* — checagem periódica de carrinhos abandonados
- **SMTP** — envio de e-mail de recuperação de carrinho
- **Postman** — coleção pronta para testar a API (`postman_collection.json`)

## Arquitetura

```
app.py              → Application Factory: cria o Flask app, registra
                       blueprints, error handlers e inicia o banco
config.py            → Configurações centralizadas (env vars)

models/               → Modelos SQLAlchemy
  cliente.py
  produto.py
  carrinho.py
  item_carrinho.py
  email_log.py         → Registro de auditoria: cada e-mail enviado fica
                          salvo aqui, evitando notificação duplicada

routes/               → Blueprints (camada de API REST)
  clientes.py
  produtos.py
  carrinhos.py
  dashboard.py
  jobs.py

schemas/              → Serialização/validação dos dados de entrada e saída

services/             → Regras de negócio
  scheduler.py          → Roda a checagem de abandono periodicamente
                          (SCHEDULER_INTERVAL_MINUTES)

utils/                → Funções auxiliares (ex: responses.py, padroniza
                          respostas de erro da API)

tests/                → Testes automatizados
```

### Fluxo de detecção de abandono

1. O `scheduler` roda a cada `SCHEDULER_INTERVAL_MINUTES` (padrão: 5 min)
2. Busca carrinhos com status ativo sem atualização há mais de
   `CARRINHO_TIMEOUT_MINUTOS` (padrão: 30 min)
3. Para cada carrinho abandonado, envia e-mail via SMTP com os itens
   deixados para trás
4. Registra o envio em `email_log`, evitando notificar o mesmo carrinho
   mais de uma vez

## Endpoints

> Preencher com os paths exatos de cada blueprint (`routes/clientes.py`,
> `routes/produtos.py`, `routes/carrinhos.py`, `routes/dashboard.py`,
> `routes/jobs.py`). Estrutura sugerida abaixo — ajuste para refletir o
> que está implementado:

| Método | Rota                  | Descrição                              |
|--------|-----------------------|-----------------------------------------|
| GET    | `/clientes`           | Lista clientes                          |
| POST   | `/clientes`           | Cria cliente                            |
| GET    | `/produtos`           | Lista produtos                          |
| POST   | `/produtos`           | Cria produto                            |
| GET    | `/carrinhos`          | Lista carrinhos                         |
| POST   | `/carrinhos`          | Cria carrinho                           |
| GET    | `/dashboard`          | Métricas de carrinhos abandonados       |
| POST   | `/jobs/checar-abandono` | Dispara manualmente a checagem de abandono |

A coleção completa e testável está em `postman_collection.json` — importe
no Postman para ver todos os endpoints com exemplos de request/response.

## Como rodar

```bash
git clone https://github.com/luizaopy/abandono-de-carrinho.git
cd abandono-de-carrinho

python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env        # e preencha SMTP_USER / SMTP_PASSWORD

python3 app.py
```

A API sobe em `http://localhost:5000` e o scheduler começa a rodar
automaticamente em segundo plano.

## Variáveis de ambiente

| Variável                      | Descrição                                  | Padrão                  |
|--------------------------------|---------------------------------------------|--------------------------|
| `SECRET_KEY`                   | Chave secreta do Flask                      | `dev-secret-key`        |
| `DATABASE_URL`                 | String de conexão do banco                  | SQLite local             |
| `SMTP_SERVER`                  | Servidor SMTP                               | `smtp.gmail.com`         |
| `SMTP_PORT`                    | Porta SMTP                                  | `587`                    |
| `SMTP_USER` / `SMTP_PASSWORD`  | Credenciais de e-mail                       | —                        |
| `CARRINHO_TIMEOUT_MINUTOS`     | Tempo sem atualização até considerar abandono | `30`                   |
| `SCHEDULER_INTERVAL_MINUTES`   | Intervalo entre checagens automáticas        | `5`                     |

## Pontos técnicos para destacar

- **Application Factory + Blueprints**: separa a criação do app da
  configuração de rotas, facilitando testes e múltiplos ambientes.
- **Auditoria de notificação (`email_log`)**: evita reenviar e-mail pro
  mesmo carrinho, e permite consultar histórico de notificações.
- **Scheduler embutido**: a checagem de abandono roda sozinha junto com a
  aplicação, sem depender de cron externo (embora pudesse rodar assim em
  produção também).
- **Error handling padronizado**: respostas de erro (404/405/500)
  seguem sempre o mesmo formato via `utils/responses.py`.

## Possíveis evoluções

- Trocar SQLite por Postgres em produção (`DATABASE_URL`)
- Consumir a API de uma plataforma real (VTEX, Tray, Mercado Livre) em vez
  de gerenciar clientes/produtos/carrinhos internamente
- Adicionar autenticação nos endpoints administrativos (`/dashboard`, `/jobs`)
- Métricas de taxa de recuperação de carrinho (quantos e-mails viraram compra)
