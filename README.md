# OpenLMIS & OpenSRP FHIR Gateway Mock Server

A Python Flask server that simulates OpenLMIS 2 backend and OpenSRP 2 FHIR Gateway APIs for local development and testing.

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

Server starts at `http://localhost:5000`

## OpenLMIS 2 Endpoints

### Authentication

```bash
# Get access token
curl -X POST http://localhost:5000/api/oauth/token \
  -d "username=administrator&password=password"

# Response: {"access_token": "...", "token_type": "bearer", ...}
```

### Requisitions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/requisitions` | List requisitions |
| GET | `/api/requisitions/{id}` | Get by ID |
| POST | `/api/requisitions` | Create new |
| PUT | `/api/requisitions/{id}/submit` | Submit |
| PUT | `/api/requisitions/{id}/authorize` | Authorize |
| PUT | `/api/requisitions/{id}/approve` | Approve |

### Stock Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stockCards` | Get stock cards |
| GET | `/api/stockCardSummaries` | Get summaries |
| POST | `/api/stockEvents` | Record stock event |
| GET | `/api/validSources` | Valid sources |
| GET | `/api/validDestinations` | Valid destinations |

### Reference Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/facilities` | List facilities |
| GET | `/api/programs` | List programs |
| GET | `/api/orderables` | List products |
| GET | `/api/processingPeriods` | List periods |

## OpenSRP FHIR Gateway Endpoints

All FHIR endpoints follow HL7 FHIR R4 specification.

### FHIR Resources

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/fhir/Patient` | Search patients |
| GET/POST | `/fhir/Patient/{id}` | Get/Update patient |
| GET | `/fhir/Location` | Search locations |
| GET | `/fhir/Organization` | Search organizations |
| GET | `/fhir/Practitioner` | Search practitioners |
| GET | `/fhir/PractitionerRole` | Search roles |
| GET | `/fhir/metadata` | CapabilityStatement |

### Example FHIR Queries

```bash
# Search patients by name
curl "http://localhost:5000/fhir/Patient?name=James"

# Get specific location
curl http://localhost:5000/fhir/Location/location-001

# Search by organization
curl "http://localhost:5000/fhir/PractitionerRole?organization=Organization/org-002"
```

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| administrator | password | ADMIN |
| warehouse_manager | password | WAREHOUSE_MANAGER |
| storeroom_manager | password | STOREROOM_MANAGER |

## Configuration

```bash
python app.py --host 0.0.0.0 --port 8080 --debug
```

## Project Structure

```
openlmis-opensrp-mock/
├── app.py                 # Main application
├── requirements.txt       # Dependencies
├── data/                  # Sample data
│   ├── users.json
│   ├── requisitions.json
│   ├── stock.json
│   ├── reference.json
│   └── fhir/
│       ├── patients.json
│       ├── locations.json
│       ├── organizations.json
│       └── practitioners.json
└── routes/                # API routes
    ├── openlmis_auth.py
    ├── openlmis_requisition.py
    ├── openlmis_stock.py
    ├── openlmis_reference.py
    └── opensrp_fhir.py
```

## License

MIT
