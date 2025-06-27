from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey, 
    DateTime, Boolean, Text, Numeric, UniqueConstraint
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.exc import IntegrityError
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
    creation_date = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_update = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullalbe=True)
    commercial_contact_id = Column(Integer, ForeignKey('users.id'))
    
    # Relations
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
    creation_date = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    is_signed = Column(Boolean, nullable=False, default=False)
    
    # Relations
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
    
    # Relations
    contract = relationship("Contract", back_populates="events")
    support_contact = relationship("User", foreign_keys=[support_contact_id])

    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', contract_id={self.contract_id})>"

    def get_client_info(self):
        """Return client information related to this event"""
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
    
    # Relations
    users = relationship("User", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    
    # Relations
    department = relationship("Department", back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', department_id={self.department_id})>"

    def set_password(self, password):
        """Hash and set the password"""
        self.hashed_password = pbkdf2_sha256.hash(password)

    def verify_password(self, password):
        """Verify the password"""
        return pbkdf2_sha256.verify(password, self.hashed_password)


class DatabaseManager:
    """Database manager using Singleton pattern"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.engine = None
            self.Session = None
            self.initialized = True
    
    def init_database(self):
        """Initialize database connection"""
        try:
            username = os.environ.get('DB_USERNAME')
            password = os.environ.get('DB_PASSWORD')
            db_name = os.environ.get('DB_NAME')
            host = os.environ.get('DB_HOST', 'localhost')
            port = os.environ.get('DB_PORT', '5432')
            
            if not all([username, password, db_name]):
                raise ValueError("Missing database environment variables")
            
            database_uri = f"postgresql://{username}:{password}@{host}:{port}/{db_name}"
            
            self.engine = create_engine(
                database_uri,
                echo=False,  # Set True for SQL debug
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True
            )
            
            self.Session = sessionmaker(bind=self.engine)
            
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


def init_departments():
    """Initialize default departments"""
    db = DatabaseManager()
    
    with db.get_session() as session:
        if session.query(Department).count() == 0:
            departments = [
                Department(name="Commercial", description="Commercial team"),
                Department(name="Support", description="Support team"),
                Department(name="Management", description="Management team")
            ]
            
            for dept in departments:
                session.add(dept)
            
            logger.info("Departments initialized")


def create_user(employee_id, name, email, department_name, password):
    """Create a new user"""
    db = DatabaseManager()
    
    with db.get_session() as session:
        try:
            department = session.query(Department).filter_by(name=department_name).first()
            if not department:
                logger.error(f"Department '{department_name}' does not exist")
                return None
            
            user = User(
                employee_id=employee_id,
                name=name,
                email=email,
                department_id=department.id
            )
            user.set_password(password)
            
            session.add(user)
            session.flush()
            
            logger.info(f"User created: {user.name}")
            return user
            
        except IntegrityError as e:
            logger.error(f"Integrity error creating user: {e}")
            return None


def authenticate_user(email, password):
    """Authenticate a user"""
    db = DatabaseManager()
    
    with db.get_session() as session:
        user = session.query(User).filter_by(email=email, is_active=True).first()
        if user and user.verify_password(password):
            logger.info(f"Authentication successful for: {email}")
            return user
        
        logger.warning(f"Authentication failed for: {email}")
        return None


def init_sample_data():
    """Initialize sample data"""
    db = DatabaseManager()
    
    with db.get_session() as session:
        if session.query(Client).count() > 0:
            logger.info("Sample data already exists")
            return
        
        try:
            commercial_dept = session.query(Department).filter_by(name="Commercial").first()
            commercial_user = User(
                employee_id="COM001",
                name="Bill Boquet",
                email="bill.boquet@epic.com",
                department_id=commercial_dept.id
            )
            commercial_user.set_password("password123")
            session.add(commercial_user)
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
                remaining_amount=10000.00,
                is_signed=False
            )
            session.add(contract)
            session.flush()
            
            event = Event(
                contract_id=contract.id,
                name="Lou Bouzin General Assembly",
                start_date=datetime(2023, 5, 5, 15, 0),
                end_date=datetime(2023, 5, 5, 17, 0),
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
    
    user = authenticate_user("bill.boquet@epic.com", "password123")
    if user:
        print(f"User logged in: {user.name} - Department: {user.department.name}")
    
    with db.get_session() as session:
        events = session.query(Event).all()
        for event in events:
            client_info = event.get_client_info()
            print(f"Event: {event.name}")
            print(f"Client: {client_info}")
