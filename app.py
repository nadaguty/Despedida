"""
Royal Salute — Fundo do Grupo
Backend Flask + PostgreSQL via SQLAlchemy
"""

import os
from datetime import datetime, date
from flask import Flask, jsonify, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()

# ─── APP CONFIG ──────────────────────────────────────────────────────

app = Flask(__name__)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/royal_salute"
)
# Render/Railway sometimes returns "postgres://" — SQLAlchemy needs "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ─── MODELS ──────────────────────────────────────────────────────────

class Config(db.Model):
    """Stores single-row app settings (meta, mensalidade, pix, bank)."""
    __tablename__ = "config"

    id          = db.Column(db.Integer, primary_key=True)
    meta        = db.Column(db.Numeric(10, 2), default=0)
    monthly     = db.Column(db.Numeric(10, 2), default=0)
    pix_key     = db.Column(db.String(200), default="")
    bank_name   = db.Column(db.String(200), default="")

    def to_dict(self):
        return {
            "meta":     float(self.meta or 0),
            "monthly":  float(self.monthly or 0),
            "pix":      self.pix_key or "",
            "bank":     self.bank_name or "",
        }


class Participante(db.Model):
    __tablename__ = "participante"

    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(150), nullable=False)
    mensalidade = db.Column(db.Numeric(10, 2), default=0)   # 0 = usa o padrão
    status      = db.Column(db.String(20), default="active") # active | inactive
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    pagamentos  = db.relationship("Pagamento", backref="participante",
                                  lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_total=True):
        d = {
            "id":         self.id,
            "nome":       self.nome,
            "mensalidade": float(self.mensalidade or 0),
            "status":     self.status,
            "criado_em":  self.criado_em.isoformat(),
        }
        if include_total:
            d["total"] = float(
                db.session.query(func.coalesce(func.sum(Pagamento.valor), 0))
                .filter(Pagamento.participante_id == self.id)
                .scalar()
            )
            d["num_pagamentos"] = len(self.pagamentos)
        return d


class Pagamento(db.Model):
    __tablename__ = "pagamento"

    id               = db.Column(db.Integer, primary_key=True)
    participante_id  = db.Column(db.Integer,
                                  db.ForeignKey("participante.id", ondelete="CASCADE"),
                                  nullable=False)
    valor            = db.Column(db.Numeric(10, 2), nullable=False)
    mes_referencia   = db.Column(db.String(7), nullable=False)  # "YYYY-MM"
    observacao       = db.Column(db.String(300), default="")
    criado_em        = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":              self.id,
            "participante_id": self.participante_id,
            "valor":           float(self.valor),
            "mes_referencia":  self.mes_referencia,
            "observacao":      self.observacao or "",
            "criado_em":       self.criado_em.isoformat(),
        }


# ─── DB INIT ─────────────────────────────────────────────────────────

def init_db():
    """Create tables and seed a default Config row if none exists."""
    db.create_all()
    if not Config.query.first():
        db.session.add(Config())
        db.session.commit()


# ─── HELPERS ─────────────────────────────────────────────────────────

def get_config() -> Config:
    return Config.query.first()


def total_arrecadado() -> float:
    return float(
        db.session.query(func.coalesce(func.sum(Pagamento.valor), 0)).scalar()
    )


# ─── ROUTES — PAGES ──────────────────────────────────────────────────

@app.route("/")
def index():
    cfg = get_config()
    return render_template("index.html", config=cfg.to_dict())


# ─── ROUTES — API ────────────────────────────────────────────────────

# ── Stats (rota bônus solicitada) ──
@app.route("/api/stats")
def api_stats():
    cfg = get_config()
    total   = total_arrecadado()
    meta    = float(cfg.meta or 0)
    falta   = max(0, meta - total)
    pct     = round((total / meta * 100), 2) if meta else 0
    ativos  = Participante.query.filter_by(status="active").count()

    return jsonify({
        "total_arrecadado": total,
        "meta":             meta,
        "falta":            falta,
        "percentual":       pct,
        "participantes_ativos": ativos,
        "mensalidade_padrao":   float(cfg.monthly or 0),
        "pix_key":          cfg.pix_key,
        "bank_name":        cfg.bank_name,
    })


# ── Config ──
@app.route("/api/config", methods=["GET"])
def api_get_config():
    return jsonify(get_config().to_dict())


@app.route("/api/config", methods=["PUT"])
def api_update_config():
    data = request.get_json(force=True)
    cfg = get_config()
    cfg.meta      = data.get("meta", cfg.meta)
    cfg.monthly   = data.get("monthly", cfg.monthly)
    cfg.pix_key   = data.get("pix", cfg.pix_key)
    cfg.bank_name = data.get("bank", cfg.bank_name)
    db.session.commit()
    return jsonify(cfg.to_dict())


# ── Participantes ──
@app.route("/api/participantes", methods=["GET"])
def api_list_participantes():
    participantes = Participante.query.order_by(Participante.criado_em).all()
    return jsonify([p.to_dict() for p in participantes])


@app.route("/api/participantes", methods=["POST"])
def api_add_participante():
    data = request.get_json(force=True)
    nome = (data.get("nome") or "").strip()
    if not nome:
        abort(400, "Nome é obrigatório")
    p = Participante(
        nome=nome,
        mensalidade=data.get("mensalidade", 0),
        status="active",
    )
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@app.route("/api/participantes/<int:pid>", methods=["PUT"])
def api_update_participante(pid):
    p = Participante.query.get_or_404(pid)
    data = request.get_json(force=True)
    if "nome" in data and data["nome"].strip():
        p.nome = data["nome"].strip()
    if "mensalidade" in data:
        p.mensalidade = data["mensalidade"]
    if "status" in data and data["status"] in ("active", "inactive"):
        p.status = data["status"]
    db.session.commit()
    return jsonify(p.to_dict())


@app.route("/api/participantes/<int:pid>", methods=["DELETE"])
def api_delete_participante(pid):
    p = Participante.query.get_or_404(pid)
    nome = p.nome
    db.session.delete(p)
    db.session.commit()
    return jsonify({"deleted": True, "nome": nome})


# ── Pagamentos ──
@app.route("/api/pagamentos", methods=["GET"])
def api_list_pagamentos():
    pid = request.args.get("participante_id", type=int)
    q = Pagamento.query
    if pid:
        q = q.filter_by(participante_id=pid)
    pagamentos = q.order_by(Pagamento.mes_referencia.desc()).all()
    return jsonify([pg.to_dict() for pg in pagamentos])


@app.route("/api/pagamentos", methods=["POST"])
def api_add_pagamento():
    data = request.get_json(force=True)
    pid   = data.get("participante_id")
    valor = data.get("valor")
    mes   = (data.get("mes_referencia") or "").strip()

    if not pid or not valor or not mes:
        abort(400, "participante_id, valor e mes_referencia são obrigatórios")

    Participante.query.get_or_404(pid)   # garante que o participante existe

    pg = Pagamento(
        participante_id=pid,
        valor=valor,
        mes_referencia=mes,
        observacao=data.get("observacao", ""),
    )
    db.session.add(pg)
    db.session.commit()
    return jsonify(pg.to_dict()), 201


@app.route("/api/pagamentos/<int:pgid>", methods=["DELETE"])
def api_delete_pagamento(pgid):
    pg = Pagamento.query.get_or_404(pgid)
    db.session.delete(pg)
    db.session.commit()
    return jsonify({"deleted": True})


# ─── ENTRY POINT ─────────────────────────────────────────────────────

if __name__ == "__main__":
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
