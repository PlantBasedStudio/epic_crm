"""
Command Line Interface for Epic Events CRM
"""

import click
import sys
import logging
from datetime import datetime
from functools import wraps
from db_operations import (
    DatabaseManager, authenticate_user, create_user, update_user, delete_user,
    update_contract, update_event, Client, Contract, Event, User, Department
)
from auth import auth_manager, AuthenticationError, AuthorizationError
from sentry_logging import (
    init_sentry, capture_exception, log_user_creation, log_user_modification,
    log_user_deletion, log_contract_signed
)

logger = logging.getLogger(__name__)

class CLIError(Exception):
    """Custom CLI error"""
    pass

class EpicEventsInteractive:
    """Interactive CLI handler"""

    def __init__(self):
        self.db = DatabaseManager()
        self.current_user = None
        self.running = True
        init_sentry()
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        try:
            user = auth_manager.get_current_user()
            return user is not None
        except:
            return False
    
    def login_prompt(self):
        """Interactive login prompt"""
        print("\n=== Login Required ===")
        print("Type 'back' to return to main menu")
        
        while True:
            try:
                email = input("Email: ").strip()
                
                if email.lower() == 'back':
                    print("Login cancelled.")
                    return False
                
                if not email:
                    print("Please enter a valid email address.")
                    continue
                
                import getpass
                password = getpass.getpass("Password: ")
                
                if password.lower() == 'back':
                    print("Login cancelled.")
                    return False
                
                if not password:
                    print("Please enter a password.")
                    continue

                try:
                    user_data = authenticate_user(email, password)
                    if not user_data:
                        print("Invalid credentials. Please check your email and password.")
                        print("Type 'back' to return to main menu or try again.")
                        continue

                    # mock test token
                    class UserForToken:
                        def __init__(self, data):
                            self.id = data['id']
                            self.employee_id = data['employee_id']
                            self.name = data['name']
                            self.email = data['email']
                            self.department = type('Department', (), {'name': data['department']})()

                    user_obj = UserForToken(user_data)
                    token = auth_manager.generate_token(user_obj)
                    auth_manager.store_token(token)

                    print(f"\nWelcome {user_data['name']}!")
                    print(f"Department: {user_data['department']}")
                    print("Authentication successful.\n")

                    self.current_user = user_data
                    return True

                except Exception as auth_error:
                    capture_exception(auth_error)
                    print(f"Authentication error: {auth_error}")
                    print("Type 'back' to return to main menu or try again.")
                    continue

            except KeyboardInterrupt:
                print("\nLogin cancelled.")
                return False
            except Exception as e:
                capture_exception(e)
                print(f"Login error: {e}")
                print("Type 'back' to return to main menu or try again.")
                continue
    
    def ensure_auth(self):
        """Ensure user is authenticated"""
        if not self.is_authenticated():
            return self.login_prompt()
        return True
    
    def show_menu(self):
        """Show main menu"""
        if self.is_authenticated():
            user = auth_manager.get_current_user()
            print(f"\n=== Epic Events CRM - {user['name']} ({user['department']}) ===")
        else:
            print("\n=== Epic Events CRM ===")
        
        print("\nAvailable commands:")
        print("  login              - Login to the system")
        print("  logout             - Logout from the system")
        print("  whoami             - Show current user info")
        print("  clients            - Client management")
        print("  contracts          - Contract management")
        print("  events             - Event management")
        print("  users              - User management")
        print("  help               - Show this help")
        print("  exit/quit          - Exit the application")
        print("\nType a command or 'help <command>' for more info.")
    
    def handle_clients(self):
        """Handle client commands"""
        if not self.ensure_auth():
            return
        
        while True:
            print("\n=== Client Management ===")
            print("  list               - List all clients")
            print("  create             - Create new client")
            print("  update <id>        - Update client")
            print("  back               - Back to main menu")
            print("  help               - Show this help")
            
            cmd = input("\nclients> ").strip().lower()
            
            if cmd == 'back':
                break
            elif cmd == 'help':
                continue
            elif cmd == 'list':
                self.list_clients()
            elif cmd == 'create':
                self.create_client()
            elif cmd.startswith('update '):
                try:
                    client_id = int(cmd.split()[1])
                    self.update_client(client_id)
                except (IndexError, ValueError):
                    print("Usage: update <client_id>")
            else:
                print("Unknown command. Type 'help' for available commands or 'back' to return to main menu.")
    
    def handle_contracts(self):
        """Handle contract commands"""
        if not self.ensure_auth():
            return

        while True:
            print("\n=== Contract Management ===")
            print("  list               - List all contracts")
            print("  unsigned           - List unsigned contracts")
            print("  unpaid             - List unpaid contracts")
            print("  create             - Create new contract")
            print("  update <id>        - Update contract")
            print("  sign <id>          - Sign contract")
            print("  back               - Back to main menu")
            print("  help               - Show this help")

            cmd = input("\ncontracts> ").strip().lower()

            if cmd == 'back':
                break
            elif cmd == 'help':
                continue
            elif cmd == 'list':
                self.list_contracts()
            elif cmd == 'unsigned':
                self.list_contracts(unsigned=True)
            elif cmd == 'unpaid':
                self.list_contracts(unpaid=True)
            elif cmd == 'create':
                self.create_contract()
            elif cmd.startswith('update '):
                try:
                    contract_id = int(cmd.split()[1])
                    self.update_contract(contract_id)
                except (IndexError, ValueError):
                    print("Usage: update <contract_id>")
            elif cmd.startswith('sign '):
                try:
                    contract_id = int(cmd.split()[1])
                    self.sign_contract(contract_id)
                except (IndexError, ValueError):
                    print("Usage: sign <contract_id>")
            else:
                print("Unknown command. Type 'help' for available commands or 'back' to return to main menu.")
    
    def handle_events(self):
        """Handle event commands"""
        if not self.ensure_auth():
            return

        while True:
            print("\n=== Event Management ===")
            print("  list               - List all events")
            print("  no-support         - List events without support")
            print("  my-events          - List my events (Support only)")
            print("  create             - Create new event")
            print("  update <id>        - Update event")
            print("  assign <id>        - Assign support to event")
            print("  back               - Back to main menu")
            print("  help               - Show this help")

            cmd = input("\nevents> ").strip().lower()

            if cmd == 'back':
                break
            elif cmd == 'help':
                continue
            elif cmd == 'list':
                self.list_events()
            elif cmd == 'no-support':
                self.list_events(no_support=True)
            elif cmd == 'my-events':
                self.list_events(my_events=True)
            elif cmd == 'create':
                self.create_event()
            elif cmd.startswith('update '):
                try:
                    event_id = int(cmd.split()[1])
                    self.update_event(event_id)
                except (IndexError, ValueError):
                    print("Usage: update <event_id>")
            elif cmd.startswith('assign '):
                try:
                    event_id = int(cmd.split()[1])
                    self.assign_support(event_id)
                except (IndexError, ValueError):
                    print("Usage: assign <event_id>")
            else:
                print("Unknown command. Type 'help' for available commands or 'back' to return to main menu.")
    
    def handle_users(self):
        """Handle user commands"""
        if not self.ensure_auth():
            return

        user = auth_manager.get_current_user()
        if user['department'] != 'Management':
            print("Access denied. User management is for Management department only.")
            return

        while True:
            print("\n=== User Management ===")
            print("  list               - List all users")
            print("  create             - Create new user")
            print("  update <id>        - Update user")
            print("  delete <id>        - Delete user")
            print("  back               - Back to main menu")
            print("  help               - Show this help")

            cmd = input("\nusers> ").strip().lower()

            if cmd == 'back':
                break
            elif cmd == 'help':
                continue
            elif cmd == 'list':
                self.list_users()
            elif cmd == 'create':
                self.create_user()
            elif cmd.startswith('update '):
                try:
                    user_id = int(cmd.split()[1])
                    self.update_user(user_id)
                except (IndexError, ValueError):
                    print("Usage: update <user_id>")
            elif cmd.startswith('delete '):
                try:
                    user_id = int(cmd.split()[1])
                    self.delete_user(user_id)
                except (IndexError, ValueError):
                    print("Usage: delete <user_id>")
            else:
                print("Unknown command. Type 'help' for available commands or 'back' to return to main menu.")
    
    def list_clients(self):
        """List all clients"""
        try:
            with self.db.get_session() as session:
                clients = session.query(Client).all()
                
                if not clients:
                    print("No clients found.")
                    return
                
                print("\nClients List:")
                print("-" * 80)
                for client in clients:
                    commercial = client.commercial_contact.name if client.commercial_contact else "N/A"
                    print(f"ID: {client.id} | {client.full_name} ({client.company_name})")
                    print(f"  Email: {client.email} | Phone: {client.phone}")
                    print(f"  Commercial: {commercial}")
                    print(f"  Created: {client.creation_date.strftime('%Y-%m-%d')}")
                    print("-" * 80)
                    
        except Exception as e:
            capture_exception(e)
            print(f"Error listing clients: {e}")
    
    def create_client(self):
        """Create a new client"""
        try:
            user = auth_manager.get_current_user()
            if user['department'] != 'Commercial':
                print("Access denied. Only Commercial department can create clients.")
                return
            
            print("\n=== Create New Client ===")
            print("Type 'cancel' at any time to cancel creation")
            
            name = input("Full name: ").strip()
            if name.lower() == 'cancel':
                print("Client creation cancelled.")
                return
            if not name:
                print("Name is required.")
                return
            
            email = input("Email: ").strip()
            if email.lower() == 'cancel':
                print("Client creation cancelled.")
                return
            if not email:
                print("Email is required.")
                return
            
            phone = input("Phone: ").strip()
            if phone.lower() == 'cancel':
                print("Client creation cancelled.")
                return
            if not phone:
                print("Phone is required.")
                return
            
            company = input("Company name: ").strip()
            if company.lower() == 'cancel':
                print("Client creation cancelled.")
                return
            if not company:
                print("Company name is required.")
                return
            
            with self.db.get_session() as session:
                existing_client = session.query(Client).filter_by(email=email).first()
                if existing_client:
                    print(f"Error: A client with email '{email}' already exists.")
                    return
                
                commercial_user = session.query(User).filter_by(email=user['email']).first()
                if not commercial_user:
                    print("Error: Current user not found in database.")
                    return
                
                client = Client(
                    full_name=name,
                    email=email,
                    phone=phone,
                    company_name=company,
                    creation_date=datetime.utcnow(),
                    commercial_contact_id=commercial_user.id
                )
                
                session.add(client)
                session.flush()
                
                print(f"\nClient '{name}' created successfully!")
                print(f"Company: {company}")
                print(f"Email: {email}")
                print(f"Assigned to: {commercial_user.name}")
                
        except Exception as e:
            capture_exception(e)
            print(f"Error creating client: {e}")
    
    def update_client(self, client_id):
        """Update a client"""
        try:
            user = auth_manager.get_current_user()
            
            with self.db.get_session() as session:
                client = session.query(Client).filter_by(id=client_id).first()
                
                if not client:
                    print(f"Client with ID {client_id} not found.")
                    return
                
                current_user = session.query(User).filter_by(email=user['email']).first()
                if (user['department'] == 'Commercial' and 
                    client.commercial_contact_id != current_user.id):
                    print("You can only update your own clients.")
                    return
                
                print(f"\n=== Update Client: {client.full_name} ===")
                print("Press Enter to keep current value")
                
                name = input(f"Full name ({client.full_name}): ").strip()
                email = input(f"Email ({client.email}): ").strip()
                phone = input(f"Phone ({client.phone}): ").strip()
                company = input(f"Company ({client.company_name}): ").strip()
                
                updated_fields = []
                if name:
                    client.full_name = name
                    updated_fields.append(f"Name: {name}")
                if email:
                    client.email = email
                    updated_fields.append(f"Email: {email}")
                if phone:
                    client.phone = phone
                    updated_fields.append(f"Phone: {phone}")
                if company:
                    client.company_name = company
                    updated_fields.append(f"Company: {company}")
                
                if updated_fields:
                    client.last_update = datetime.utcnow()
                    print(f"\nClient updated successfully!")
                    for field in updated_fields:
                        print(f"  {field}")
                else:
                    print("No fields updated.")
                    
        except Exception as e:
            capture_exception(e)
            print(f"Error updating client: {e}")
    
    def list_contracts(self, unsigned=False, unpaid=False):
        """List contracts with optional filters"""
        try:
            with self.db.get_session() as session:
                query = session.query(Contract)
                
                if unsigned:
                    query = query.filter_by(is_signed=False)
                if unpaid:
                    query = query.filter(Contract.remaining_amount > 0)
                
                contracts = query.all()
                
                if not contracts:
                    print("No contracts found.")
                    return
                
                print("\nContracts List:")
                print("-" * 100)
                for contract in contracts:
                    status = "Signed" if contract.is_signed else "Pending"
                    payment_status = "Paid" if contract.remaining_amount == 0 else f"${contract.remaining_amount:.2f} remaining"
                    commercial = contract.commercial_contact.name if contract.commercial_contact else "N/A"
                    
                    print(f"ID: {contract.id} | Contract for {contract.client.full_name}")
                    print(f"  Status: {status} | Payment: {payment_status}")
                    print(f"  Total: ${contract.total_amount:.2f} | Commercial: {commercial}")
                    print(f"  Created: {contract.creation_date.strftime('%Y-%m-%d')}")
                    print("-" * 100)
                    
        except Exception as e:
            capture_exception(e)
            print(f"Error listing contracts: {e}")
    
    def create_contract(self):
        """Create a new contract"""
        try:
            user = auth_manager.get_current_user()
            if user['department'] != 'Management':
                print("Access denied. Only Management department can create contracts.")
                return
            
            print("\n=== Create New Contract ===")
            print("Type 'cancel' at any time to cancel creation")
            
            with self.db.get_session() as session:
                clients = session.query(Client).all()
                if not clients:
                    print("No clients available. Create a client first.")
                    return
                
                print("Available clients:")
                for client in clients:
                    print(f"  {client.id}: {client.full_name} ({client.company_name})")
            
            client_input = input("Client ID: ").strip()
            if client_input.lower() == 'cancel':
                print("Contract creation cancelled.")
                return
            
            try:
                client_id = int(client_input)
            except ValueError:
                print("Invalid client ID. Please enter a valid number.")
                return
            
            with self.db.get_session() as session:
                client = session.query(Client).filter_by(id=client_id).first()
                if not client:
                    print(f"Error: Client with ID {client_id} not found.")
                    return
                
                amount_input = input("Total amount: ").strip()
                if amount_input.lower() == 'cancel':
                    print("Contract creation cancelled.")
                    return
                
                remaining_input = input("Remaining amount: ").strip()
                if remaining_input.lower() == 'cancel':
                    print("Contract creation cancelled.")
                    return
                
                try:
                    amount = float(amount_input)
                    remaining = float(remaining_input)
                except ValueError:
                    print("Invalid amount format. Please enter valid numbers.")
                    return
                
                if remaining > amount:
                    print("Error: Remaining amount cannot be greater than total amount.")
                    return
                
                if amount <= 0:
                    print("Error: Total amount must be positive.")
                    return
                
                if remaining < 0:
                    print("Error: Remaining amount cannot be negative.")
                    return
                
                contract = Contract(
                    client_id=client_id,
                    commercial_contact_id=client.commercial_contact_id,
                    total_amount=amount,
                    remaining_amount=remaining,
                    creation_date=datetime.utcnow(),
                    is_signed=False
                )
                
                session.add(contract)
                session.flush()
                
                print(f"\nContract created successfully!")
                print(f"Contract ID: {contract.id}")
                print(f"Client: {client.full_name}")
                print(f"Total: ${amount:.2f}")
                print(f"Remaining: ${remaining:.2f}")
                
        except Exception as e:
            capture_exception(e)
            print(f"Error creating contract: {e}")
    
    def sign_contract(self, contract_id):
        """Sign a contract"""
        try:
            user = auth_manager.get_current_user()
            
            with self.db.get_session() as session:
                contract = session.query(Contract).filter_by(id=contract_id).first()
                
                if not contract:
                    print(f"Contract with ID {contract_id} not found.")
                    return
                
                if contract.is_signed:
                    print("Contract is already signed.")
                    return
                
                if user['department'] == 'Commercial':
                    current_user = session.query(User).filter_by(email=user['email']).first()
                    if contract.commercial_contact_id != current_user.id:
                        print("You can only sign contracts for your own clients.")
                        return
                elif user['department'] != 'Management':
                    print("Access denied. Only Commercial (own contracts) or Management can sign contracts.")
                    return
                
                contract.is_signed = True
                print(f"Contract #{contract_id} signed successfully!")

                log_contract_signed(
                    user_info=user,
                    contract_info={
                        'id': contract_id,
                        'client_name': contract.client.full_name,
                        'total_amount': float(contract.total_amount)
                    }
                )

        except Exception as e:
            capture_exception(e)
            print(f"Error signing contract: {e}")

    def update_contract(self, contract_id):
        """Update a contract"""
        try:
            user = auth_manager.get_current_user()

            with self.db.get_session() as session:
                contract = session.query(Contract).filter_by(id=contract_id).first()
                if not contract:
                    print(f"Contract with ID {contract_id} not found.")
                    return

                if user['department'] == 'Commercial':
                    current_user = session.query(User).filter_by(email=user['email']).first()
                    if contract.commercial_contact_id != current_user.id:
                        print("You can only update contracts for your own clients.")
                        return
                elif user['department'] != 'Management':
                    print("Access denied. Only Commercial (own contracts) or Management can update contracts.")
                    return

                print(f"\n=== Update Contract #{contract.id} ===")
                print(f"Client: {contract.client.full_name}")
                print("Press Enter to keep current value, type 'cancel' to abort")

                total_input = input(f"Total amount ({contract.total_amount:.2f}): ").strip()
                if total_input.lower() == 'cancel':
                    print("Contract update cancelled.")
                    return

                remaining_input = input(f"Remaining amount ({contract.remaining_amount:.2f}): ").strip()
                if remaining_input.lower() == 'cancel':
                    print("Contract update cancelled.")
                    return

                try:
                    total_amount = float(total_input) if total_input else None
                    remaining_amount = float(remaining_input) if remaining_input else None
                except ValueError:
                    print("Invalid amount format. Please enter valid numbers.")
                    return

            update_contract(
                contract_id,
                total_amount=total_amount,
                remaining_amount=remaining_amount
            )
            print(f"Contract #{contract_id} updated successfully!")

        except Exception as e:
            capture_exception(e)
            print(f"Error updating contract: {e}")

    def update_event(self, event_id):
        """Update an event"""
        try:
            user = auth_manager.get_current_user()

            with self.db.get_session() as session:
                event = session.query(Event).filter_by(id=event_id).first()
                if not event:
                    print(f"Event with ID {event_id} not found.")
                    return

                if user['department'] == 'Support':
                    current_user = session.query(User).filter_by(email=user['email']).first()
                    if event.support_contact_id != current_user.id:
                        print("You can only update events assigned to you.")
                        return
                elif user['department'] != 'Management':
                    print("Access denied. Only Support (own events) or Management can update events.")
                    return

                print(f"\n=== Update Event: {event.name} ===")
                print("Press Enter to keep current value, type 'cancel' to abort")

                name = input(f"Name ({event.name}): ").strip()
                if name.lower() == 'cancel':
                    print("Event update cancelled.")
                    return

                start_date = input(f"Start date ({event.start_date.strftime('%Y-%m-%d %H:%M')}): ").strip()
                if start_date.lower() == 'cancel':
                    print("Event update cancelled.")
                    return

                end_date = input(f"End date ({event.end_date.strftime('%Y-%m-%d %H:%M')}): ").strip()
                if end_date.lower() == 'cancel':
                    print("Event update cancelled.")
                    return

                location = input(f"Location ({event.location}): ").strip()
                if location.lower() == 'cancel':
                    print("Event update cancelled.")
                    return

                attendees_input = input(f"Attendees ({event.attendees_count}): ").strip()
                if attendees_input.lower() == 'cancel':
                    print("Event update cancelled.")
                    return

                notes = input(f"Notes ({event.notes or 'None'}): ").strip()
                if notes.lower() == 'cancel':
                    print("Event update cancelled.")
                    return

                start_dt = None
                end_dt = None
                if start_date:
                    try:
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
                    except ValueError:
                        print("Invalid start date format. Please use YYYY-MM-DD HH:MM")
                        return

                if end_date:
                    try:
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
                    except ValueError:
                        print("Invalid end date format. Please use YYYY-MM-DD HH:MM")
                        return

                attendees = None
                if attendees_input:
                    try:
                        attendees = int(attendees_input)
                    except ValueError:
                        print("Invalid number of attendees.")
                        return

            update_event(
                event_id,
                name=name if name else None,
                start_date=start_dt,
                end_date=end_dt,
                location=location if location else None,
                attendees_count=attendees,
                notes=notes if notes else None
            )
            print(f"Event updated successfully!")

        except Exception as e:
            capture_exception(e)
            print(f"Error updating event: {e}")

    def list_events(self, no_support=False, my_events=False):
        """List events with optional filters"""
        try:
            user = auth_manager.get_current_user()
            
            with self.db.get_session() as session:
                query = session.query(Event)
                
                if no_support:
                    query = query.filter(Event.support_contact_id.is_(None))
                
                if my_events:
                    if user['department'] != 'Support':
                        print("--my-events is only available for Support department.")
                        return
                    
                    current_user = session.query(User).filter_by(email=user['email']).first()
                    query = query.filter_by(support_contact_id=current_user.id)
                
                events = query.all()
                
                if not events:
                    print("No events found.")
                    return
                
                print("\nEvents List:")
                print("-" * 120)
                for event in events:
                    client_info = event.get_client_info()
                    client_name = client_info.get('client_name', 'N/A')
                    support = event.support_contact.name if event.support_contact else "No Support"
                    
                    print(f"ID: {event.id} | {event.name}")
                    print(f"  Client: {client_name}")
                    print(f"  Date: {event.start_date.strftime('%Y-%m-%d %H:%M')} - {event.end_date.strftime('%Y-%m-%d %H:%M')}")
                    print(f"  Location: {event.location}")
                    print(f"  Attendees: {event.attendees_count}")
                    print(f"  Support: {support}")
                    if event.notes:
                        print(f"  Notes: {event.notes}")
                    print("-" * 120)
                    
        except Exception as e:
            capture_exception(e)
            print(f"Error listing events: {e}")
    
    def create_event(self):
        """Create a new event"""
        try:
            user = auth_manager.get_current_user()
            if user['department'] != 'Commercial':
                print("Access denied. Only Commercial department can create events.")
                return
            
            print("\n=== Create New Event ===")
            print("Type 'cancel' at any time to cancel creation")
            
            with self.db.get_session() as session:
                current_user = session.query(User).filter_by(email=user['email']).first()
                if not current_user:
                    print("Error: Current user not found in database.")
                    return
                
                contracts = session.query(Contract).filter_by(
                    commercial_contact_id=current_user.id,
                    is_signed=True
                ).all()
                
                if not contracts:
                    print("No signed contracts available for your clients.")
                    return
                
                print("Available signed contracts:")
                for contract in contracts:
                    print(f"  {contract.id}: {contract.client.full_name} - ${contract.total_amount:.2f}")
            
            contract_input = input("Contract ID: ").strip()
            if contract_input.lower() == 'cancel':
                print("Event creation cancelled.")
                return
            
            try:
                contract_id = int(contract_input)
            except ValueError:
                print("Invalid contract ID. Please enter a valid number.")
                return
            
            with self.db.get_session() as session:
                contract = session.query(Contract).filter_by(id=contract_id).first()
                if not contract:
                    print(f"Error: Contract with ID {contract_id} not found.")
                    return
                
                if not contract.is_signed:
                    print("Error: Contract must be signed before creating an event.")
                    return
                
                current_user = session.query(User).filter_by(email=user['email']).first()
                if contract.commercial_contact_id != current_user.id:
                    print("Error: You can only create events for your own clients.")
                    return
                
                name = input("Event name: ").strip()
                if name.lower() == 'cancel':
                    print("Event creation cancelled.")
                    return
                if not name:
                    print("Event name is required.")
                    return
                
                start_date = input("Start date (YYYY-MM-DD HH:MM): ").strip()
                if start_date.lower() == 'cancel':
                    print("Event creation cancelled.")
                    return
                
                end_date = input("End date (YYYY-MM-DD HH:MM): ").strip()
                if end_date.lower() == 'cancel':
                    print("Event creation cancelled.")
                    return
                
                location = input("Location: ").strip()
                if location.lower() == 'cancel':
                    print("Event creation cancelled.")
                    return
                
                attendees_input = input("Number of attendees: ").strip()
                if attendees_input.lower() == 'cancel':
                    print("Event creation cancelled.")
                    return
                
                try:
                    attendees = int(attendees_input)
                except ValueError:
                    print("Invalid number of attendees. Please enter a valid number.")
                    return
                
                if attendees <= 0:
                    print("Number of attendees must be positive.")
                    return
                
                notes = input("Notes (optional): ").strip()
                if notes.lower() == 'cancel':
                    print("Event creation cancelled.")
                    return
                
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
                except ValueError:
                    print("Invalid date format. Please use YYYY-MM-DD HH:MM")
                    return
                
                if start_dt >= end_dt:
                    print("Error: Start date must be before end date.")
                    return
                
                if start_dt < datetime.now():
                    print("Warning: Event start date is in the past.")
                    confirm = input("Continue anyway? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("Event creation cancelled.")
                        return
                
                event = Event(
                    contract_id=contract_id,
                    name=name,
                    start_date=start_dt,
                    end_date=end_dt,
                    location=location,
                    attendees_count=attendees,
                    notes=notes if notes else None
                )
                
                session.add(event)
                session.flush()
                
                print(f"\nEvent '{name}' created successfully!")
                print(f"Event ID: {event.id}")
                print(f"Client: {contract.client.full_name}")
                print(f"Date: {start_dt.strftime('%Y-%m-%d %H:%M')} - {end_dt.strftime('%Y-%m-%d %H:%M')}")
                print(f"Location: {location}")
                print(f"Attendees: {attendees}")
                
        except Exception as e:
            capture_exception(e)
            print(f"Error creating event: {e}")
    
    def assign_support(self, event_id):
        """Assign support to an event"""
        try:
            user = auth_manager.get_current_user()
            if user['department'] != 'Management':
                print("Access denied. Only Management department can assign support.")
                return
            
            with self.db.get_session() as session:
                event = session.query(Event).filter_by(id=event_id).first()
                if not event:
                    print(f"Event with ID {event_id} not found.")
                    return
                
                from models import Department
                support_dept = session.query(Department).filter_by(name='Support').first()
                support_users = session.query(User).filter_by(department_id=support_dept.id).all()
                
                if not support_users:
                    print("No support users available.")
                    return
                
                print("Available support users:")
                for user in support_users:
                    print(f"  {user.id}: {user.name} ({user.email})")
                
                try:
                    support_id = int(input("Support user ID: ").strip())
                except ValueError:
                    print("Invalid user ID.")
                    return
                
                support_user = session.query(User).filter_by(id=support_id).first()
                if not support_user or support_user.department_id != support_dept.id:
                    print("Invalid support user.")
                    return
                
                event.support_contact_id = support_id
                print(f"Support user '{support_user.name}' assigned to event '{event.name}'!")
                
        except Exception as e:
            capture_exception(e)
            print(f"Error assigning support: {e}")
    
    def list_users(self):
        """List all users"""
        try:
            with self.db.get_session() as session:
                users = session.query(User).all()
                
                if not users:
                    print("No users found.")
                    return
                
                print("\nUsers List:")
                print("-" * 80)
                for user in users:
                    dept_name = user.department.name if user.department else "N/A"
                    print(f"ID: {user.id} | {user.name} ({user.employee_id})")
                    print(f"  Email: {user.email}")
                    print(f"  Department: {dept_name}")
                    print("-" * 80)
                    
        except Exception as e:
            capture_exception(e)
            print(f"Error listing users: {e}")
    
    def create_user(self):
        """Create a new user"""
        try:
            print("\n=== Create New User ===")
            print("Type 'cancel' at any time to cancel creation")
            
            employee_id = input("Employee ID: ").strip()
            if employee_id.lower() == 'cancel':
                print("User creation cancelled.")
                return
            if not employee_id:
                print("Employee ID is required.")
                return
            
            with self.db.get_session() as session:
                existing_user = session.query(User).filter_by(employee_id=employee_id).first()
                if existing_user:
                    print(f"Error: A user with employee ID '{employee_id}' already exists.")
                    return
            
            name = input("Full name: ").strip()
            if name.lower() == 'cancel':
                print("User creation cancelled.")
                return
            if not name:
                print("Name is required.")
                return
            
            email = input("Email: ").strip()
            if email.lower() == 'cancel':
                print("User creation cancelled.")
                return
            if not email:
                print("Email is required.")
                return
            
            with self.db.get_session() as session:
                existing_user = session.query(User).filter_by(email=email).first()
                if existing_user:
                    print(f"Error: A user with email '{email}' already exists.")
                    return
            
            print("Available departments: Commercial, Support, Management")
            department = input("Department: ").strip()
            if department.lower() == 'cancel':
                print("User creation cancelled.")
                return
            if department not in ['Commercial', 'Support', 'Management']:
                print("Error: Invalid department. Must be Commercial, Support, or Management.")
                return
            
            import getpass
            password = getpass.getpass("Password: ")
            if password.lower() == 'cancel':
                print("User creation cancelled.")
                return
            if not password:
                print("Password is required.")
                return
            
            if len(password) < 6:
                print("Error: Password must be at least 6 characters long.")
                return
            
            user = create_user(employee_id, name, email, department, password)
            if user:
                print(f"\nUser '{name}' created successfully!")
                print(f"Employee ID: {employee_id}")
                print(f"Email: {email}")
                print(f"Department: {department}")

                current_user = auth_manager.get_current_user()
                log_user_creation(
                    user_info=current_user,
                    created_user_info={'name': name, 'email': email, 'department': department}
                )
            else:
                print("Error: Failed to create user.")

        except Exception as e:
            capture_exception(e)
            print(f"Error creating user: {e}")

    def update_user(self, user_id):
        """Update an existing user"""
        try:
            with self.db.get_session() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    print(f"User with ID {user_id} not found.")
                    return

                print(f"\n=== Update User: {user.name} ===")
                print("Press Enter to keep current value, type 'cancel' to abort")

                name = input(f"Name ({user.name}): ").strip()
                if name.lower() == 'cancel':
                    print("User update cancelled.")
                    return

                email = input(f"Email ({user.email}): ").strip()
                if email.lower() == 'cancel':
                    print("User update cancelled.")
                    return

                print(f"Current department: {user.department.name}")
                print("Available departments: Commercial, Support, Management")
                department = input(f"Department ({user.department.name}): ").strip()
                if department.lower() == 'cancel':
                    print("User update cancelled.")
                    return

                import getpass
                password = getpass.getpass("New password (leave empty to keep current): ")
                if password.lower() == 'cancel':
                    print("User update cancelled.")
                    return

                if password and len(password) < 6:
                    print("Error: Password must be at least 6 characters long.")
                    return

                if department and department not in ['Commercial', 'Support', 'Management']:
                    print("Error: Invalid department. Must be Commercial, Support, or Management.")
                    return

            old_name = user.name
            old_email = user.email
            old_department = user.department.name

            updated = update_user(
                user_id,
                name=name if name else None,
                email=email if email else None,
                department_name=department if department else None,
                password=password if password else None
            )

            if updated:
                print(f"\nUser updated successfully!")

                changes = []
                if name:
                    changes.append(f"name: {old_name} -> {name}")
                if email:
                    changes.append(f"email: {old_email} -> {email}")
                if department:
                    changes.append(f"department: {old_department} -> {department}")
                if password:
                    changes.append("password changed")

                current_user = auth_manager.get_current_user()
                log_user_modification(
                    user_info=current_user,
                    modified_user_info={'name': name or old_name, 'email': email or old_email},
                    changes=", ".join(changes) if changes else "No changes"
                )
            else:
                print("Error: Failed to update user.")

        except Exception as e:
            capture_exception(e)
            print(f"Error updating user: {e}")

    def delete_user(self, user_id):
        """Delete a user"""
        try:
            current_user = auth_manager.get_current_user()

            with self.db.get_session() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if not user:
                    print(f"User with ID {user_id} not found.")
                    return

                if user.email == current_user['email']:
                    print("Error: You cannot delete yourself.")
                    return

                print(f"\n=== Delete User: {user.name} ===")
                print(f"Employee ID: {user.employee_id}")
                print(f"Email: {user.email}")
                print(f"Department: {user.department.name}")

                confirm = input("\nAre you sure you want to delete this user? (yes/no): ").strip().lower()
                if confirm != 'yes':
                    print("User deletion cancelled.")
                    return

                deleted_user_info = {'name': user.name, 'email': user.email}

            delete_user(user_id)
            print(f"User deleted successfully!")

            log_user_deletion(
                user_info=current_user,
                deleted_user_info=deleted_user_info
            )

        except Exception as e:
            capture_exception(e)
            print(f"Error deleting user: {e}")

    def run(self):
        """Main interactive loop"""
        print("=== Epic Events CRM ===")
        print("Welcome to Epic Events Customer Relationship Management System")
        
        self.show_menu()
        
        while self.running:
            try:
                command = input("\nCRM> ").strip().lower()
                
                if command in ['exit', 'quit']:
                    if self.is_authenticated():
                        user = auth_manager.get_current_user()
                        print(f"Goodbye {user['name']}!")
                    else:
                        print("Goodbye!")
                    self.running = False
                
                elif command == 'login':
                    self.login_prompt()
                
                elif command == 'logout':
                    if self.is_authenticated():
                        user = auth_manager.get_current_user()
                        print(f"Goodbye {user['name']}!")
                        auth_manager.clear_token()
                        print("Logged out successfully.")
                    else:
                        print("You are not logged in.")
                
                elif command == 'whoami':
                    if self.ensure_auth():
                        user = auth_manager.get_current_user()
                        print(f"\nCurrent User Information:")
                        print(f"  Name: {user['name']}")
                        print(f"  Email: {user['email']}")
                        print(f"  Department: {user['department']}")
                        print(f"  Employee ID: {user['employee_id']}")
                
                elif command == 'clients':
                    self.handle_clients()
                
                elif command == 'contracts':
                    self.handle_contracts()
                
                elif command == 'events':
                    self.handle_events()
                
                elif command == 'users':
                    self.handle_users()
                
                elif command == 'help':
                    self.show_menu()
                
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' or 'quit' to leave the application.")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                capture_exception(e)
                print(f"Error: {e}")

@click.group()
def cli():
    """Epic Events CRM - Command Line Interface"""
    pass

@cli.command()
def interactive():
    """Start interactive mode"""
    app = EpicEventsInteractive()
    app.run()

@cli.command()
@click.option('--email', prompt='Email', help='User email')
@click.option('--password', prompt='Password', hide_input=True, help='User password')
def login(email, password):
    """Login to Epic Events CRM"""
    try:
        user_data = authenticate_user(email, password)
        if not user_data:
            click.echo("Authentication failed. Please check your credentials.", err=True)
            sys.exit(1)

        class UserForToken:
            def __init__(self, data):
                self.id = data['id']
                self.employee_id = data['employee_id']
                self.name = data['name']
                self.email = data['email']
                self.department = type('Department', (), {'name': data['department']})()

        user_obj = UserForToken(user_data)
        token = auth_manager.generate_token(user_obj)
        auth_manager.store_token(token)

        click.echo(f"Welcome {user_data['name']}!")
        click.echo(f"Department: {user_data['department']}")
        click.echo("Authentication successful. You can now use the CRM.")

    except Exception as e:
        capture_exception(e)
        logger.error(f"Login error: {e}")
        click.echo(f"Login failed: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        app = EpicEventsInteractive()
        app.run()
    else:
        cli()
