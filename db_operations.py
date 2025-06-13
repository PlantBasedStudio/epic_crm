from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
import os

load_dotenv()

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    creation_date = Column(String, nullable=False)
    commercial_contact = Column(String)
    contracts = relationship("Contract", back_populates="client")

class Contract(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    client = relationship("Client", back_populates="contracts")
    total_amount = Column(Integer, nullable=False)
    remaining_amount = Column(Integer, nullable=False)
    creation_date = Column(String, nullable=False)
    status = Column(String, nullable=False)
    events = relationship("Event", back_populates="contract")

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    contract = relationship("Contract", back_populates="events")
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    support_contact = Column(String, nullable=False)
    location = Column(String, nullable=False)
    number_of_attendees = Column(Integer, nullable=False)

    def get_client_info(self):
        return {
            "client_name": self.contract.client.company_name,
            "commercial_contact": self.contract.client.commercial_contact
        }

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'))
    role = relationship("Role", back_populates="users")

    def set_password(self, password):
        self.hashed_password = pbkdf2_sha256.hash(password)

    def verify_password(self, password):
        return pbkdf2_sha256.verify(password, self.hashed_password)
    

print("DB Username:", os.environ.get('DB_USERNAME'))
print("DB Password:", os.environ.get('DB_PASSWORD'))
print("DB Name:", os.environ.get('DB_NAME'))

DATABASE_URI = f"postgresql://{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}@localhost:5432/{os.environ['DB_NAME']}"
engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def init_roles():
    if session.query(Role).count() == 0: 
        admin_role = Role(name="Admin")
        user_role = Role(name="User")
        session.add(admin_role)
        session.add(user_role)
        session.commit()

def create_user(session, employee_id, name, email, department, password, role_name):
    role = session.query(Role).filter_by(name=role_name).first()
    if not role:
        print("Role does not exist.")
        return
    user = User(employee_id=employee_id, name=name, email=email, department=department, password=password)
    user.role = role
    session.add(user)
    session.commit()

def authenticate_user(session, email, password):
    user = session.query(User).filter_by(email=email).first()
    if user and user.verify_password(password):
        return user
    return None

def init_data():
    commercial_contact = "Bill Boquet"
    client = Client(full_name="Kevin Casey", email="kevin@startup.io", phone="+678 123 456 78", company_name="Cool Startup LLC", creation_date="2021-04-18", commercial_contact=commercial_contact)

    session.add(client)
    session.commit()

    contract = Contract(client=client, total_amount=10000, remaining_amount=10000, creation_date="2023-03-29", status="not signed")
    session.add(contract)
    session.commit()

    event = Event(contract=contract, start_date="2023-05-05 15:00", end_date="2023-05-05 17:00", support_contact="Aliénor Vichum", location="Salle des fêtes de Mufflins", number_of_attendees=200)
    client_info = event.get_client_info()
    print(client_info)

    session.add(event)
    session.commit()

if __name__ == "__db_operations__":
    init_roles()
    init_data() 
