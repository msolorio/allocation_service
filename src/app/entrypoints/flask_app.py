from datetime import datetime
from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import config
from app.adapters import orm, repository
from app.domain import model

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
    batches = repository.SqlAlchemyRepository(session).list()
    line = model.OrderLine(
        orderid=request.json["orderid"],
        sku=request.json["sku"],
        qty=request.json["qty"],
    )

    if not is_valid_sku(line.sku, batches):
        return jsonify({"message": f"Invalid sku {line.sku}"}), 400

    try:
        batch_ref = model.allocate(line, batches)
    except model.OutOfStock as e:
        return jsonify({"message": str(e)}), 400

    session.commit()
    return jsonify({"batchref": batch_ref}), 201
