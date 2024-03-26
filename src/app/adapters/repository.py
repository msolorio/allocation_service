from app.domain.model import Batch


class SqlAlchemyRepository:
    def __init__(self, session):
        self.session = session

    def add(self, batch: Batch):
        self.session.add(batch)

    def get(self, batch_ref: str) -> Batch:
        return self.session.query(Batch).filter_by(batch_ref=batch_ref).one()

    def list(self):
        return self.session.query(Batch).all()
