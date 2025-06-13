class Client:
    def __init__(self, full_name, email, phone, company_name, creation_date, commercial_contact=None):
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.company_name = company_name
        self.creation_date = creation_date
        self.commercial_contact = commercial_contact
        self.contracts = []

class Contract:
    def __init__(self, client, total_amount, remaining_amount, creation_date, status):
        self.client = client
        self.total_amount = total_amount
        self.remaining_amount = remaining_amount
        self.creation_date = creation_date
        self.status = status
        self.events = []

class Event:
    def __init__(self, contract, start_date, end_date, support_contact, location, number_of_attendees):
        self.contract = contract
        self.client = contract.client
        self.start_date = start_date
        self.end_date = end_date
        self.support_contact = support_contact
        self.location = location
        self.number_of_attendees = number_of_attendees
        
    def get_client_info(self):
        return {
            "full_name": self.client.full_name,
            "email": self.client.email,
            "phone": self.client.phone,
            "company_name": self.client.company_name,
            "commercial_contact": self.client.commercial_contact
        }
