from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey, 
    DateTime, Boolean, Text, Numeric, UniqueConstraint, text
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timezone
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

Base = declarative_base()

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    company_name = Column(String(100), nullable=False)
    creation_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_update = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=True)
    commercial_contact_id = Column(Integer, ForeignKey('users.id'))
    
    contracts = relationship("Contract", back_populates="client", cascade="all, delete-orphan")
    commercial_contact = relationship("User", foreign_keys=[commercial_contact_id])

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.full_name}', company='{self.company_name}')>"

class Contract(Base):
    __tablename__ = 'contracts'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    commercial_contact_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    remaining_amount = Column(Numeric(10, 2), nullable=False)
    creation_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    is_signed = Column(Boolean, nullable=False, default=False)
    
    client = relationship("Client", back_populates="contracts")
    commercial_contact = relationship("User", foreign_keys=[commercial_contact_id])
    events = relationship("Event", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contract(id={self.id}, client_id={self.client_id}, signed={self.is_signed})>"

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'), nullable=False)
    name = Column(String(200), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    support_contact_id = Column(Integer, ForeignKey('users.id'))
    location = Column(String(200), nullable=False)
    attendees_count = Column(Integer, nullable=False)
    notes = Column(Text)
    
    contract = relationship("Contract", back_populates="events")
    support_contact = relationship("User", foreign_keys=[support_contact_id])

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', contract_id={self.contract_id})>"

    def get_client_info(self):
        if self.contract and self.contract.client:
            return {
                "client_name": self.contract.client.full_name,
                "company_name": self.contract.client.company_name,
                "commercial_contact": self.contract.commercial_contact.name if self.contract.commercial_contact else None
            }
        return {}

class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    
    users = relationship("User", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    creation_date = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    department = relationship("Department", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint('employee_id', name='uq_employee_id'),
        UniqueConstraint('email', name='uq_email'),
    )

    def set_password(self, password):
        self.password_hash = pbkdf2_sha256.hash(password)

    def check_password(self, password):
        return pbkdf2_sha256.verify(password, self.password_hash)

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', department='{self.department.name if self.department else None}')>"

class DatabaseManager:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'postgresql://epic_user:epic_password@localhost/epic_crm')
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    @contextmanager
    def get_session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def drop_and_create_database(self):
        try:
            admin_engine = create_engine('postgresql://epic_user:epic_password@localhost/postgres')
            
            with admin_engine.connect() as conn:
                conn.execute(text("COMMIT"))
                conn.execute(text("DROP DATABASE IF EXISTS epic_crm"))
                conn.execute(text("CREATE DATABASE epic_crm"))
                logger.info("Database dropped and recreated successfully")
                
        except Exception as e:
            logger.error(f"Error dropping/creating database: {e}")
            raise

    def init_database(self):
        try:
            self.drop_and_create_database()
            
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

def init_departments():
    db = DatabaseManager()
    
    departments_data = [
        {"name": "Commercial", "description": "Sales and client relationship management"},
        {"name": "Support", "description": "Event organization and customer support"},
        {"name": "Management", "description": "Administration and management"}
    ]
    
    with db.get_session() as session:
        for dept_data in departments_data:
            department = Department(**dept_data)
            session.add(department)
            logger.info(f"Created department: {dept_data['name']}")

def authenticate_user(email, password):
    db = DatabaseManager()
    
    with db.get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        
        if user and user.check_password(password):
            logger.info(f"User authenticated successfully: {user.name}")
            return user
        
        logger.warning(f"Authentication failed for: {email}")
        return None
    

def create_user(employee_id, name, email, department_name, password):
    """Create a new user"""
    db = DatabaseManager()
    
    with db.get_session() as session:
        try:
            department = session.query(Department).filter_by(name=department_name).first()
            if not department:
                raise ValueError(f"Department '{department_name}' not found")
            
            user = User(
                employee_id=employee_id,
                name=name,
                email=email,
                department_id=department.id
            )
            user.set_password(password)
            
            session.add(user)
            session.flush()
            
            logger.info(f"User created: {name} ({department_name})")
            return user
            
        except IntegrityError as e:
            logger.error(f"User creation failed - duplicate data: {e}")
            raise ValueError("Employee ID or email already exists")
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            raise


def init_sample_data():
    db = DatabaseManager()
    
    with db.get_session() as session:
        try:
            commercial_dept = session.query(Department).filter_by(name="Commercial").first()
            support_dept = session.query(Department).filter_by(name="Support").first()
            management_dept = session.query(Department).filter_by(name="Management").first()
            
            commercial_user = User(
                employee_id="COM001",
                name="Bill Boquet",
                email="bill.boquet@epic.com",
                department_id=commercial_dept.id
            )
            commercial_user.set_password("password123")
            session.add(commercial_user)
            
            support_user = User(
                employee_id="SUP001",
                name="Kate Hastroff",
                email="kate.hastroff@epic.com",
                department_id=support_dept.id
            )
            support_user.set_password("password123")
            session.add(support_user)
            
            management_user = User(
                employee_id="MAN001",
                name="Alice Manager",
                email="alice.manager@epic.com",
                department_id=management_dept.id
            )
            management_user.set_password("admin123")
            session.add(management_user)
            
            session.flush()
            
            client = Client(
                full_name="Kevin Casey",
                email="kevin@startup.io",
                phone="+678 123 456 78",
                company_name="Cool Startup LLC",
                commercial_contact_id=commercial_user.id
            )
            session.add(client)
            session.flush()
            
            contract = Contract(
                client_id=client.id,
                commercial_contact_id=commercial_user.id,
                total_amount=10000.00,
                remaining_amount=5000.00,
                is_signed=True
            )
            session.add(contract)
            session.flush()
            
            event = Event(
                contract_id=contract.id,
                name="Lou Bouzin General Assembly",
                start_date=datetime(2023, 5, 5, 15, 0),
                end_date=datetime(2023, 5, 5, 17, 0),
                support_contact_id=support_user.id,
                location="Salle des fêtes de Mufflins",
                attendees_count=200,
                notes="General assembly of shareholders (~200 people)."
            )
            session.add(event)
            
            logger.info("Sample data created successfully")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            raise

if __name__ == "__main__":
    db = DatabaseManager()
    db.init_database()
    
    init_departments()
    init_sample_data()
    
    print("Database initialization completed!")
    
    test_users = [
        ("bill.boquet@epic.com", "password123"),
        ("kate.hastroff@epic.com", "password123"),
        ("alice.manager@epic.com", "admin123")
    ]
    
    for email, password in test_users:
        user = authenticate_user(email, password)
        if user:
            print(f"{user.name} ({user.department.name})")
        else:
            print(f"Failed: {email}")
    
    with db.get_session() as session:
        clients_count = session.query(Client).count()
        contracts_count = session.query(Contract).count()
        events_count = session.query(Event).count()
        
        print(f"\nDatabase Summary:")
        print(f"   - {clients_count} clients")
        print(f"   - {contracts_count} contracts")
        print(f"   - {events_count} events")
