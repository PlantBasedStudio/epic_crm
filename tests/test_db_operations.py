"""
Unit tests for database operations
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_operations import (
    Base, User, Client, Contract, Event, Department,
    DatabaseManager
)


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
def setup_departments(test_session):
    """Setup all departments"""
    departments = [
        Department(name="Commercial", description="Sales department"),
        Department(name="Support", description="Support department"),
        Department(name="Management", description="Management department")
    ]
    for dept in departments:
        test_session.add(dept)
    test_session.commit()
    return departments


@pytest.fixture
def setup_users(test_session, setup_departments):
    """Setup sample users"""
    commercial_dept = test_session.query(Department).filter_by(name="Commercial").first()
    support_dept = test_session.query(Department).filter_by(name="Support").first()
    management_dept = test_session.query(Department).filter_by(name="Management").first()

    users = []

    commercial_user = User(
        employee_id="COM001",
        name="Bill Commercial",
        email="bill@epic.com",
        department_id=commercial_dept.id
    )
    commercial_user.set_password("password123")
    test_session.add(commercial_user)
    users.append(commercial_user)

    support_user = User(
        employee_id="SUP001",
        name="Kate Support",
        email="kate@epic.com",
        department_id=support_dept.id
    )
    support_user.set_password("password123")
    test_session.add(support_user)
    users.append(support_user)

    management_user = User(
        employee_id="MAN001",
        name="Alice Manager",
        email="alice@epic.com",
        department_id=management_dept.id
    )
    management_user.set_password("admin123")
    test_session.add(management_user)
    users.append(management_user)

    test_session.commit()
    return users


class TestUserOperations:
    """Tests for user operations"""

    def test_create_user(self, test_session, setup_departments):
        """Test user creation"""
        dept = test_session.query(Department).filter_by(name="Commercial").first()
        user = User(
            employee_id="NEW001",
            name="New User",
            email="new@epic.com",
            department_id=dept.id
        )
        user.set_password("newpass123")
        test_session.add(user)
        test_session.commit()

        saved_user = test_session.query(User).filter_by(employee_id="NEW001").first()
        assert saved_user is not None
        assert saved_user.name == "New User"

    def test_authenticate_user(self, test_session, setup_users):
        """Test user authentication"""
        user = test_session.query(User).filter_by(email="bill@epic.com").first()

        assert user is not None
        assert user.check_password("password123")
        assert not user.check_password("wrongpassword")

    def test_update_user_name(self, test_session, setup_users):
        """Test updating user name"""
        user = test_session.query(User).filter_by(email="bill@epic.com").first()
        user.name = "Bill Updated"
        test_session.commit()

        updated_user = test_session.query(User).filter_by(email="bill@epic.com").first()
        assert updated_user.name == "Bill Updated"

    def test_update_user_department(self, test_session, setup_users, setup_departments):
        """Test updating user department"""
        user = test_session.query(User).filter_by(email="bill@epic.com").first()
        support_dept = test_session.query(Department).filter_by(name="Support").first()

        user.department_id = support_dept.id
        test_session.commit()

        updated_user = test_session.query(User).filter_by(email="bill@epic.com").first()
        assert updated_user.department.name == "Support"

    def test_delete_user(self, test_session, setup_users):
        """Test user deletion"""
        user = test_session.query(User).filter_by(email="kate@epic.com").first()
        test_session.delete(user)
        test_session.commit()

        deleted_user = test_session.query(User).filter_by(email="kate@epic.com").first()
        assert deleted_user is None


class TestClientOperations:
    """Tests for client operations"""

    def test_create_client(self, test_session, setup_users):
        """Test client creation"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="Test Client",
            email="client@test.com",
            phone="+1234567890",
            company_name="Test Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        saved_client = test_session.query(Client).filter_by(email="client@test.com").first()
        assert saved_client is not None
        assert saved_client.full_name == "Test Client"
        assert saved_client.commercial_contact.name == commercial_user.name

    def test_update_client(self, test_session, setup_users):
        """Test client update"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="Original Name",
            email="original@test.com",
            phone="+1111111111",
            company_name="Original Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        client.full_name = "Updated Name"
        client.company_name = "Updated Company"
        test_session.commit()

        updated_client = test_session.query(Client).filter_by(email="original@test.com").first()
        assert updated_client.full_name == "Updated Name"
        assert updated_client.company_name == "Updated Company"


class TestContractOperations:
    """Tests for contract operations"""

    def test_create_contract(self, test_session, setup_users):
        """Test contract creation"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="Contract Client",
            email="contract@test.com",
            phone="+2222222222",
            company_name="Contract Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=10000.00,
            remaining_amount=10000.00,
            is_signed=False
        )
        test_session.add(contract)
        test_session.commit()

        saved_contract = test_session.query(Contract).filter_by(client_id=client.id).first()
        assert saved_contract is not None
        assert saved_contract.total_amount == 10000.00
        assert saved_contract.is_signed is False

    def test_sign_contract(self, test_session, setup_users):
        """Test contract signing"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="Sign Client",
            email="sign@test.com",
            phone="+3333333333",
            company_name="Sign Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=5000.00,
            remaining_amount=5000.00,
            is_signed=False
        )
        test_session.add(contract)
        test_session.commit()

        contract.is_signed = True
        test_session.commit()

        signed_contract = test_session.query(Contract).filter_by(id=contract.id).first()
        assert signed_contract.is_signed is True

    def test_filter_unsigned_contracts(self, test_session, setup_users):
        """Test filtering unsigned contracts"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="Filter Client",
            email="filter@test.com",
            phone="+4444444444",
            company_name="Filter Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        # Create signed and unsigned contracts
        for i in range(3):
            contract = Contract(
                client_id=client.id,
                commercial_contact_id=commercial_user.id,
                total_amount=1000.00 * (i + 1),
                remaining_amount=1000.00 * (i + 1),
                is_signed=(i % 2 == 0)
            )
            test_session.add(contract)
        test_session.commit()

        unsigned = test_session.query(Contract).filter_by(is_signed=False).all()
        assert len(unsigned) >= 1

    def test_filter_unpaid_contracts(self, test_session, setup_users):
        """Test filtering unpaid contracts"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="Unpaid Client",
            email="unpaid@test.com",
            phone="+5555555555",
            company_name="Unpaid Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        # Create paid and unpaid contracts
        contract1 = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=5000.00,
            remaining_amount=0,
            is_signed=True
        )
        contract2 = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=3000.00,
            remaining_amount=1500.00,
            is_signed=True
        )
        test_session.add_all([contract1, contract2])
        test_session.commit()

        unpaid = test_session.query(Contract).filter(Contract.remaining_amount > 0).all()
        assert len(unpaid) >= 1


class TestEventOperations:
    """Tests for event operations"""

    def test_create_event(self, test_session, setup_users):
        """Test event creation"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()
        support_user = test_session.query(User).filter_by(email="kate@epic.com").first()

        client = Client(
            full_name="Event Client",
            email="event@test.com",
            phone="+6666666666",
            company_name="Event Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=8000.00,
            remaining_amount=0,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        event = Event(
            contract_id=contract.id,
            name="Company Event",
            start_date=datetime(2024, 6, 15, 14, 0),
            end_date=datetime(2024, 6, 15, 22, 0),
            support_contact_id=support_user.id,
            location="Event Hall",
            attendees_count=100,
            notes="Annual celebration"
        )
        test_session.add(event)
        test_session.commit()

        saved_event = test_session.query(Event).filter_by(name="Company Event").first()
        assert saved_event is not None
        assert saved_event.attendees_count == 100
        assert saved_event.support_contact.name == support_user.name

    def test_filter_events_without_support(self, test_session, setup_users):
        """Test filtering events without support assigned"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()

        client = Client(
            full_name="NoSupport Client",
            email="nosupport@test.com",
            phone="+7777777777",
            company_name="NoSupport Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=6000.00,
            remaining_amount=0,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        event = Event(
            contract_id=contract.id,
            name="No Support Event",
            start_date=datetime(2024, 7, 1, 10, 0),
            end_date=datetime(2024, 7, 1, 18, 0),
            support_contact_id=None,
            location="Main Hall",
            attendees_count=50
        )
        test_session.add(event)
        test_session.commit()

        no_support_events = test_session.query(Event).filter(
            Event.support_contact_id.is_(None)
        ).all()
        assert len(no_support_events) >= 1

    def test_assign_support_to_event(self, test_session, setup_users):
        """Test assigning support to an event"""
        commercial_user = test_session.query(User).filter_by(email="bill@epic.com").first()
        support_user = test_session.query(User).filter_by(email="kate@epic.com").first()

        client = Client(
            full_name="Assign Client",
            email="assign@test.com",
            phone="+8888888888",
            company_name="Assign Company",
            commercial_contact_id=commercial_user.id
        )
        test_session.add(client)
        test_session.commit()

        contract = Contract(
            client_id=client.id,
            commercial_contact_id=commercial_user.id,
            total_amount=4000.00,
            remaining_amount=0,
            is_signed=True
        )
        test_session.add(contract)
        test_session.commit()

        event = Event(
            contract_id=contract.id,
            name="Assign Event",
            start_date=datetime(2024, 8, 1, 9, 0),
            end_date=datetime(2024, 8, 1, 17, 0),
            support_contact_id=None,
            location="Conference Center",
            attendees_count=75
        )
        test_session.add(event)
        test_session.commit()

        # Assign support
        event.support_contact_id = support_user.id
        test_session.commit()

        updated_event = test_session.query(Event).filter_by(name="Assign Event").first()
        assert updated_event.support_contact_id == support_user.id
        assert updated_event.support_contact.name == support_user.name
