# Schema ERD - Epic Events CRM

```
                                    EPIC EVENTS CRM - DATABASE SCHEMA

    +------------------+          +------------------+          +------------------+
    |   DEPARTMENTS    |          |      USERS       |          |     CLIENTS      |
    +------------------+          +------------------+          +------------------+
    | PK id            |<---------| PK id            |<---------| PK id            |
    |    name          |    1   n |    employee_id   |    1   n |    full_name     |
    |    description   |          |    name          |          |    email         |
    +------------------+          |    email         |          |    phone         |
                                  |    password_hash |          |    company_name  |
                                  | FK department_id |          |    creation_date |
                                  |    creation_date |          |    last_update   |
                                  +------------------+          | FK commercial_id |
                                           |                    +------------------+
                                           |                            |
                                           |                            |
                                           v                            v
                                  +------------------+          +------------------+
                                  |    CONTRACTS     |          |      EVENTS      |
                                  +------------------+          +------------------+
                                  | PK id            |<---------| PK id            |
                                  | FK client_id     |    1   n | FK contract_id   |
                                  | FK commercial_id |          |    name          |
                                  |    total_amount  |          |    start_date    |
                                  |    remaining_amt |          |    end_date      |
                                  |    creation_date |          | FK support_id    |
                                  |    is_signed     |          |    location      |
                                  +------------------+          |    attendees     |
                                                                |    notes         |
                                                                +------------------+
```