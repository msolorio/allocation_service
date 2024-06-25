from app.adapters import repository


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = repository.SqlAlchemyRepository(self.session)
        # return super().__enter__()

    def __exit__(self, *args):
        self.rollback()
        self.session.close()

    def rollback(self):
        self.session.rollback()

    def commit(self):
        self.session.commit()
