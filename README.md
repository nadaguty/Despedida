# 👑 Royal Salute — Fundo do Grupo

Aplicação web Full Stack para acompanhar a arrecadação coletiva do grupo.

## Stack
- **Backend:** Python 3.11 + Flask + SQLAlchemy
- **Banco de dados:** PostgreSQL
- **Frontend:** HTML/CSS/JS puro (sem framework) integrado via Fetch API
- **Deploy:** Render (gratuito)

---

## Estrutura de pastas

```
royal-salute/
├── app.py               ← servidor Flask + modelos SQLAlchemy
├── requirements.txt
├── .env.example
├── README.md
└── templates/
    └── index.html       ← template Jinja2 (todo o frontend)
```

---

## Rodando localmente

### 1. Pré-requisitos
- Python 3.10+
- PostgreSQL rodando localmente

### 2. Instalar dependências
```bash
python -m venv venv
source venv/bin/activate          # Linux/Mac
# ou: venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 3. Configurar variável de ambiente
Crie um arquivo `.env` na raiz:
```
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/royal_salute
FLASK_DEBUG=1
```

### 4. Criar o banco de dados
```bash
# No psql ou pgAdmin, crie o banco:
createdb royal_salute

# As tabelas são criadas automaticamente ao iniciar o app
```

### 5. Iniciar o servidor
```bash
python app.py
```
Acesse: http://localhost:5000

---

## Deploy no Render (gratuito)

1. Crie conta em https://render.com
2. **New → PostgreSQL** → crie um banco gratuito → copie a `DATABASE_URL`
3. **New → Web Service** → conecte seu repositório GitHub
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variable:** `DATABASE_URL` = (URL copiada no passo 2)
5. Clique em **Deploy** — o Render cria as tabelas automaticamente na primeira inicialização.

---

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Página principal |
| GET | `/api/stats` | Resumo: total, meta, percentual, falta |
| GET | `/api/config` | Configurações (pix, meta, mensalidade) |
| PUT | `/api/config` | Atualiza configurações |
| GET | `/api/participantes` | Lista todos os participantes |
| POST | `/api/participantes` | Adiciona participante |
| PUT | `/api/participantes/<id>` | Edita participante |
| DELETE | `/api/participantes/<id>` | Remove participante |
| GET | `/api/pagamentos` | Lista pagamentos (filtra por `?participante_id=`) |
| POST | `/api/pagamentos` | Registra pagamento |
| DELETE | `/api/pagamentos/<id>` | Remove pagamento |

### Exemplo `/api/stats`
```json
{
  "total_arrecadado": 850.00,
  "meta": 1200.00,
  "falta": 350.00,
  "percentual": 70.83,
  "participantes_ativos": 4,
  "mensalidade_padrao": 100.00,
  "pix_key": "11999999999",
  "bank_name": "Nubank — João"
}
```
