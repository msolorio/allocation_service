from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import config
from app.adapters import orm, repository
from app.domain import model
from app.service_layer import services

orm.start_mappers()
db_engine = create_engine(config.get_postgres_uri())
get_session = sessionmaker(bind=db_engine)
app = Flask(__name__)


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/allocate", methods=["POST"])
def allocate():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    line = model.OrderLine(
        orderid=request.json["orderid"],
        sku=request.json["sku"],
        qty=request.json["qty"],
    )
    try:
        batch_ref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batch_ref}), 201
