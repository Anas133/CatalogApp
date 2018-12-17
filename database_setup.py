from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):

        return {
        'name' : self.name,
        'id' : self.id
        }

class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key = True)
    name = Column(String(50), nullable = False)
    description = Column(String(300))
    time = Column(String(200), nullable = False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):

        return {
        'category_id' : self.category_id,
        'description' : self.description,
        'name' : self.name,
        'id' : self.id,
        }

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
