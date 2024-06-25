from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import config
from app.adapters import orm, repository
from app.domain import model
from app.service_layer import services


db_engine = create_engine(config.get_postgres_uri())
orm.init(db_engine)
get_session = sessionmaker(bind=db_engine)
app = Flask(__name__)


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


@app.route("/allocation", methods=["POST"])
def allocate():
    session = get_session()
    try:
        batch_ref = services.allocate(
            orderid=request.json["orderid"],
            sku=request.json["sku"],
            qty=request.json["qty"],
            repo=repository.SqlAlchemyRepository(session),
            session=session,
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({"message": str(e)}), 400

    return jsonify({"batchref": batch_ref}), 201


@app.route("/allocation", methods=["DELETE"])
def deallocate():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    services.deallocate(
        orderid=request.json["orderid"],
        sku=request.json["sku"],
        repo=repo,
        session=session,
    )
    return "OK", 204


@app.route("/batch", methods=["POST"])
def add_batch():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta)
    services.add_batch(
        batchref=request.json["batchref"],
        sku=request.json["sku"],
        qty=request.json["qty"],
        eta=eta,
        repo=repo,
        session=session,
    )
    return "OK", 201
