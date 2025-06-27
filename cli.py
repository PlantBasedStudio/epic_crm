"""
Command Line Interface for Epic Events CRM
"""

import click
import sys
import logging
from datetime import datetime
from db_operations import DatabaseManager, authenticate_user, create_user, Client, Contract, Event, User
from auth import auth_manager, AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)

class CLIError(Exception):
    """Custom CLI error"""
    pass

@click.group()
def cli():
    """Epic Events CRM - Command Line Interface"""
    pass

@cli.command()
@click.option('--email', prompt='Email', help='User email')
@click.option('--password', prompt='Password', hide_input=True, help='User password')
def login(email, password):
    """Login to Epic Events CRM"""
    try:
        # Initialize database
        db = DatabaseManager()
        db.init_database()
        
        # Authenticate user
        user = authenticate_user(email, password)
        if not user:
            click.echo("Authentication failed. Please check your credentials.", err=True)
            sys.exit(1)
        
        # Generate and store JWT token
        token = auth_manager.generate_token(user)
        auth_manager.store_token(token)
        
        click.echo(f" Welcome {user.name}!")
        click.echo(f"Department: {user.department.name}")
        click.echo("Authentication successful. You can now use the CRM.")
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        click.echo(f"Login failed: {e}", err=True)
        sys.exit(1)

@cli.command()
def logout():
    """Logout from Epic Events CRM"""
    auth_manager.clear_token()
    click.echo("Logged out successfully.")

@cli.command()
def whoami():
    """Show current user information"""
    try:
        user = auth_manager.get_current_user()
        if not user:
            click.echo("Not authenticated. Please login first.", err=True)
            sys.exit(1)
        
        click.echo(" Current User Information:")
        click.echo(f"   Name: {user['name']}")
        click.echo(f"   Email: {user['email']}")
        click.echo(f"   Department: {user['department']}")
        click.echo(f"   Employee ID: {user['employee_id']}")
        
    except Exception as e:
        logger.error(f"Whoami error: {e}")
        click.echo(f"Error: {e}", err=True)

@cli.group()
def clients():
    """Client management commands"""
    pass

@clients.command('list')
@auth_manager.require_authentication
def list_clients():
    """List all clients"""
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            clients = session.query(Client).all()
            
            if not clients:
                click.echo("No clients found.")
                return
            
            click.echo("Clients:")
            for client in clients:
                click.echo(f"   • {client.full_name} ({client.company_name}) - {client.email}")
                
    except (AuthenticationError, AuthorizationError) as e:
        click.echo(f"{e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"List clients error: {e}")
        click.echo(f"Error: {e}", err=True)

@clients.command('create')
@auth_manager.require_permission('create_client')
@click.option('--name', prompt='Full name', help='Client full name')
@click.option('--email', prompt='Email', help='Client email')
@click.option('--phone', prompt='Phone', help='Client phone')
@click.option('--company', prompt='Company name', help='Company name')
def create_client(name, email, phone, company):
    """Create a new client"""
    try:
        user = auth_manager.get_current_user()
        db = DatabaseManager()
        
        with db.get_session() as session:
            commercial_user = session.query(User).filter_by(email=user['email']).first()
            
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
            
            click.echo(f"Client '{name}' created successfully!")
            
    except (AuthenticationError, AuthorizationError) as e:
        click.echo(f"{e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Create client error: {e}")
        click.echo(f"Error creating client: {e}", err=True)

@cli.group()
def contracts():
    """Contract management commands"""
    pass

@contracts.command('list')
@auth_manager.require_authentication
def list_contracts():
    """List all contracts"""
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            contracts = session.query(Contract).all()
            
            if not contracts:
                click.echo("No contracts found.")
                return
            
            click.echo("Contracts:")
            for contract in contracts:
                status = "Signed" if contract.is_signed else "⏳ Pending"
                click.echo(f"   • Contract #{contract.id} - {contract.client.full_name} - {status}")
                click.echo(f"     Amount: ${contract.total_amount} (Remaining: ${contract.remaining_amount})")
                
    except (AuthenticationError, AuthorizationError) as e:
        click.echo(f"{e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"List contracts error: {e}")
        click.echo(f"Error: {e}", err=True)

@cli.group()
def events():
    """Event management commands"""
    pass

@events.command('list')
@auth_manager.require_authentication
def list_events():
    """List all events"""
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            events = session.query(Event).all()
            
            if not events:
                click.echo("No events found.")
                return
            
            click.echo("Events:")
            for event in events:
                support = event.support_contact.name if event.support_contact else "No support assigned"
                click.echo(f"   • {event.name}")
                click.echo(f"     Date: {event.start_date.strftime('%Y-%m-%d %H:%M')}")
                click.echo(f"     Location: {event.location}")
                click.echo(f"     Support: {support}")
                
    except (AuthenticationError, AuthorizationError) as e:
        click.echo(f"{e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"List events error: {e}")
        click.echo(f"Error: {e}", err=True)

@cli.group()
def users():
    """User management commands (Management only)"""
    pass

@users.command('create')
@auth_manager.require_permission('create_user')
@click.option('--employee-id', prompt='Employee ID', help='Employee ID')
@click.option('--name', prompt='Full name', help='User full name')
@click.option('--email', prompt='Email', help='User email')
@click.option('--department', prompt='Department', type=click.Choice(['Commercial', 'Support', 'Management']), help='User department')
@click.option('--password', prompt='Password', hide_input=True, help='User password')
def create_user_cmd(employee_id, name, email, department, password):
    """Create a new user"""
    try:
        user = create_user(employee_id, name, email, department, password)
        if user:
            click.echo(f" User '{name}' created successfully!")
        else:
            click.echo("Failed to create user.", err=True)
            
    except (AuthenticationError, AuthorizationError) as e:
        click.echo(f"{e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Create user error: {e}")
        click.echo(f"Error creating user: {e}", err=True)

if __name__ == '__main__':
    cli()
