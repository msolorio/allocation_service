from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import config
import domain.model as model
import adapters.orm as orm
import adapters.repository as repository
import service_layer.services as services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return "OK", 201


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    try:
        batchref = services.allocate(
            request.json["orderid"],
            request.json["sku"],
            request.json["qty"],
            repo,
            session,
        )

    except (services.InvalidSku, model.OutOfStock) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batchref}), 201


@app.route("/add_batch", methods=["POST"])
def add_batch_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)

    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()

    services.add_batch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        repo,
        session,
    )

    return "OK", 201
