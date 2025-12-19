"""
Unit tests for database models
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_operations import Base, User, Client, Contract, Event, Department


@pytest.fixture
def test_engine():
    """Create a test database engine"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test session"""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_department(test_session):
    """Create a sample department"""
    dept = Department(name="Commercial", description="Sales department")
    test_session.add(dept)
    test_session.commit()
    return dept


@pytest.fixture
def sample_user(test_session, sample_department):
    """Create a sample user"""
    user = User(
        employee_id="COM001",
        name="John Doe",
        email="john.doe@epic.com",
        department_id=sample_department.id
    )
    user.set_password("password123")
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture
def sample_client(test_session, sample_user):
    """Create a sample client"""
    client = Client(
        full_name="Kevin Casey",
        email="kevin@startup.io",
        phone="+1234567890",
        company_name="Cool Startup LLC",
        commercial_contact_id=sample_user.id
    )
    test_session.add(client)
    test_session.commit()
    return client


class TestDepartmentModel:
    """Tests for Department model"""

    def test_create_department(self, test_session):
        """Test department creation"""
        dept = Department(name="Support", description="Support team")
        test_session.add(dept)
        test_session.commit()

        assert dept.id is not None
        assert dept.name == "Support"
        assert dept.description == "Support team"

    def test_department_repr(self, sample_department):
        """Test department string representation"""
        assert "Commercial" in repr(sample_department)


class TestUserModel:
    """Tests for User model"""

    def test_create_user(self, test_session, sample_department):
        """Test user creation"""
        user = User(
            employee_id="TEST001",
            name="Test User",
            email="test@epic.com",
            department_id=sample_department.id
        )
        user.set_password("testpass")
        test_session.add(user)
        test_session.commit()

        assert user.id is not None
        assert user.name == "Test User"
        assert user.employee_id == "TEST001"

    def test_password_hashing(self, sample_user):
        """Test password is hashed correctly"""
        assert sample_user.password_hash != "password123"
        assert sample_user.check_password("password123")
        assert not sample_user.check_password("wrongpassword")

    def test_user_department_relationship(self, sample_user, sample_department):
        """Test user-department relationship"""
        assert sample_user.department.name == "Commercial"

    def test_user_repr(self, sample_user):
        """Test user string representation"""
        assert "John Doe" in repr(sample_user)


class TestClientModel:
    """Tests for Client model"""

    def test_create_client(self, test_session, sample_user):
        """Test client creation"""
        client = Client(
            full_name="Test Client",
            email="client@test.com",
            phone="+9876543210",
            company_name="Test Company",
            commercial_contact_id=sample_user.id
        )
        test_session.add(client)
        test_session.commit()

        assert client.id is not None
        assert client.full_name == "Test Client"

    def test_client_commercial_relationship(self, sample_client, sample_user):
        """Test client-commercial relationship"""
        assert sample_client.commercial_contact.name == sample_user.name

    def test_client_creation_date(self, sample_client):
        """Test client has creation date"""
        assert sample_client.creation_date is not None

    def test_client_repr(self, sample_client):
        """Test client string representation"""
        assert "Kevin Casey" in repr(sample_client)


class TestContractModel:
    """Tests for Contract model"""

    def test_create_contract(self, test_session, sample_client, sample_user):
        """Test contract creation"""
        contract = Contract(
            client_id=sample_client.id,
            commercial_contact_id=sample_user.id,
            total_amount=10000.00,
            remaining_amount=5000.00,
            is_signed=False
        )
        test_session.add(contract)
        test_session.commit()

        assert contract.id is not None
        assert contract.total_amount == 10000.00
        assert contract.is_signed is False

    def test_contract_client_relationship(self, test_session, sample_client, sample_user):
        """Test contract-client relationship"""
        contract = Contract(
            client_id=sample_client.id,
            commercial_contact_id=sample_user.id,
            total_amount=5000.00,
            remaining_amount=5000.00,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        assert contract.client.full_name == sample_client.full_name

    def test_contract_repr(self, test_session, sample_client, sample_user):
        """Test contract string representation"""
        contract = Contract(
            client_id=sample_client.id,
            commercial_contact_id=sample_user.id,
            total_amount=1000.00,
            remaining_amount=500.00,
            is_signed=False
        )
        test_session.add(contract)
        test_session.commit()

        assert "Contract" in repr(contract)


class TestEventModel:
    """Tests for Event model"""

    def test_create_event(self, test_session, sample_client, sample_user):
        """Test event creation"""
        contract = Contract(
            client_id=sample_client.id,
            commercial_contact_id=sample_user.id,
            total_amount=10000.00,
            remaining_amount=0,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        event = Event(
            contract_id=contract.id,
            name="Company Meeting",
            start_date=datetime(2024, 6, 1, 14, 0),
            end_date=datetime(2024, 6, 1, 18, 0),
            location="Conference Room A",
            attendees_count=50,
            notes="Annual company meeting"
        )
        test_session.add(event)
        test_session.commit()

        assert event.id is not None
        assert event.name == "Company Meeting"
        assert event.attendees_count == 50

    def test_event_get_client_info(self, test_session, sample_client, sample_user):
        """Test event get_client_info method"""
        contract = Contract(
            client_id=sample_client.id,
            commercial_contact_id=sample_user.id,
            total_amount=5000.00,
            remaining_amount=0,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        event = Event(
            contract_id=contract.id,
            name="Test Event",
            start_date=datetime(2024, 7, 1, 10, 0),
            end_date=datetime(2024, 7, 1, 12, 0),
            location="Test Location",
            attendees_count=20
        )
        test_session.add(event)
        test_session.commit()

        client_info = event.get_client_info()
        assert client_info['client_name'] == sample_client.full_name

    def test_event_repr(self, test_session, sample_client, sample_user):
        """Test event string representation"""
        contract = Contract(
            client_id=sample_client.id,
            commercial_contact_id=sample_user.id,
            total_amount=3000.00,
            remaining_amount=0,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        event = Event(
            contract_id=contract.id,
            name="Birthday Party",
            start_date=datetime(2024, 8, 15, 18, 0),
            end_date=datetime(2024, 8, 16, 2, 0),
            location="Beach Resort",
            attendees_count=100
        )
        test_session.add(event)
        test_session.commit()

        assert "Birthday Party" in repr(event)
