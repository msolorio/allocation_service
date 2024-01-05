from flask import Flask, request, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import model.model as model
import orm
import repository
import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    batches = repository.SqlAlchemyRepository(session).list()
    orderline = model.OrderLine(
        request.json["orderid"],
        request.json["sku"],
        request.json["qty"],
    )
    try:
        batchref = model.allocate(orderline, batches)
    except model.OutOfStock as e:
        return jsonify({"message": str(e)}), 400

    session.commit()

    return jsonify({"batchref": batchref}), 201
