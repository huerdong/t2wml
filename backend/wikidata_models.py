from uuid import uuid4
from app_config import db
from t2wml.wikification.wikidata_provider import FallbackSparql

class WikidataEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wd_id = db.Column(db.String(64), index=True)
    data_type = db.Column(db.String(64))
    label = db.Column(db.String(64))
    description = db.Column(db.String(200))
    P31 = db.Column(db.String(64))
    cache_id=db.Column(db.String(64), nullable=True)

    @staticmethod
    def add_or_update(wd_id, data_type=None, label=None, description=None, P31=None, cache_id=None, do_session_commit=True):
        wd = WikidataEntity.query.filter_by(wd_id=wd_id, cache_id=cache_id).first()
        if wd:
            added = False
        else:
            wd = WikidataEntity(wd_id=wd_id, cache_id=cache_id)
            added = True
        
        if data_type is not None:
            wd.data_type = data_type
        if label is not None:
            wd.label = label
        if description is not None:
            wd.description = description
        if P31 is not None:
            wd.P31 = P31

        db.session.add(wd)
        if do_session_commit:
            db.session.commit()
        return added
        
    @staticmethod
    def do_commit():
        try:
            db.session.commit()
        except:
            db.session.rollback()
            raise ValueError("Failed to commit to database session")


class DatabaseProvider(FallbackSparql):
    def __init__(self, project):
        self.project=project

        if self.project.cache_id:
            self.cache_id=self.project.cache_id
        else:
            self.cache_id=self.project.cache_id=str(uuid4())
            project.save()

        super().__init__(project.sparql_endpoint)

    def save_entry(self, wd_id, data_type, from_file=False, **kwargs):
        cache_id=None
        if from_file:
            cache_id=self.cache_id
        return WikidataEntity.add_or_update(wd_id, data_type, do_session_commit=False, cache_id=cache_id, **kwargs)

    def try_get_property_type(self, wikidata_property, *args, **kwargs):
        props = WikidataEntity.query.filter_by(wd_id=wikidata_property)
        if props is None:
            raise ValueError("Not found")
        matching_prop=None
        for prop in props:
            if prop.cache_id is None or prop.cache_id==self.cache_id:
                matching_prop=prop
                break
        if matching_prop is None:
            raise ValueError("Not found")
        if matching_prop.data_type is None:
            raise ValueError("No datatype defined for that ID")
        if matching_prop.data_type == "Property Not Found":
            raise ValueError("Not found")
        return matching_prop.data_type

    def __exit__(self, exc_type, exc_value, exc_traceback):
        WikidataEntity.do_commit()
