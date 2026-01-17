"""
OpenSRP 2 FHIR Gateway Mock Routes

Implements FHIR R4 compliant endpoints for:
- Patient
- Location
- Organization
- Practitioner
- PractitionerRole
"""
import json
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

opensrp_fhir = Blueprint('opensrp_fhir', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fhir')

# In-memory stores
patients_store = None
locations_store = None
organizations_store = None
practitioners_store = None
practitioner_roles_store = None


def load_fhir_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)


def get_patients():
    global patients_store
    if patients_store is None:
        patients_store = load_fhir_data('patients.json')['patients']
    return patients_store


def get_locations():
    global locations_store
    if locations_store is None:
        locations_store = load_fhir_data('locations.json')['locations']
    return locations_store


def get_organizations():
    global organizations_store
    if organizations_store is None:
        organizations_store = load_fhir_data('organizations.json')['organizations']
    return organizations_store


def get_practitioners():
    global practitioners_store, practitioner_roles_store
    if practitioners_store is None:
        data = load_fhir_data('practitioners.json')
        practitioners_store = data['practitioners']
        practitioner_roles_store = data.get('practitionerRoles', [])
    return practitioners_store


def get_practitioner_roles():
    global practitioner_roles_store
    if practitioner_roles_store is None:
        get_practitioners()  # This loads both
    return practitioner_roles_store


def create_bundle(resources, resource_type):
    """Create a FHIR Bundle response."""
    return {
        'resourceType': 'Bundle',
        'id': str(uuid.uuid4()),
        'meta': {
            'lastUpdated': datetime.utcnow().isoformat() + 'Z'
        },
        'type': 'searchset',
        'total': len(resources),
        'entry': [
            {
                'fullUrl': f'urn:uuid:{r["id"]}',
                'resource': r,
                'search': {'mode': 'match'}
            }
            for r in resources
        ]
    }


def create_operation_outcome(severity, code, diagnostics):
    """Create a FHIR OperationOutcome for errors."""
    return {
        'resourceType': 'OperationOutcome',
        'issue': [
            {
                'severity': severity,
                'code': code,
                'diagnostics': diagnostics
            }
        ]
    }


# ==================== PATIENT ENDPOINTS ====================

@opensrp_fhir.route('/fhir/Patient', methods=['GET'])
def search_patients():
    """
    Search patients.
    Query params: _id, identifier, name, gender, birthdate
    """
    patients = get_patients()
    
    # Apply filters
    patient_id = request.args.get('_id')
    identifier = request.args.get('identifier')
    name = request.args.get('name')
    gender = request.args.get('gender')
    birthdate = request.args.get('birthdate')
    
    filtered = patients
    
    if patient_id:
        filtered = [p for p in filtered if p['id'] == patient_id]
    if identifier:
        filtered = [p for p in filtered if any(
            i.get('value') == identifier for i in p.get('identifier', [])
        )]
    if name:
        name_lower = name.lower()
        filtered = [p for p in filtered if any(
            name_lower in n.get('family', '').lower() or
            any(name_lower in g.lower() for g in n.get('given', []))
            for n in p.get('name', [])
        )]
    if gender:
        filtered = [p for p in filtered if p.get('gender') == gender]
    if birthdate:
        filtered = [p for p in filtered if p.get('birthDate') == birthdate]
    
    return jsonify(create_bundle(filtered, 'Patient'))


@opensrp_fhir.route('/fhir/Patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get a specific patient by ID."""
    patients = get_patients()
    patient = next((p for p in patients if p['id'] == patient_id), None)
    
    if not patient:
        return jsonify(create_operation_outcome('error', 'not-found', f'Patient/{patient_id} not found')), 404
    
    return jsonify(patient)


@opensrp_fhir.route('/fhir/Patient', methods=['POST'])
def create_patient():
    """Create a new patient."""
    data = request.get_json()
    
    if not data or data.get('resourceType') != 'Patient':
        return jsonify(create_operation_outcome('error', 'invalid', 'Invalid Patient resource')), 400
    
    # Assign ID if not provided
    if 'id' not in data:
        data['id'] = f'patient-{str(uuid.uuid4())[:8]}'
    
    data['meta'] = {
        'versionId': '1',
        'lastUpdated': datetime.utcnow().isoformat() + 'Z'
    }
    
    get_patients().append(data)
    
    response = jsonify(data)
    response.status_code = 201
    response.headers['Location'] = f'/fhir/Patient/{data["id"]}'
    return response


@opensrp_fhir.route('/fhir/Patient/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Update an existing patient."""
    patients = get_patients()
    idx = next((i for i, p in enumerate(patients) if p['id'] == patient_id), None)
    
    data = request.get_json()
    
    if not data or data.get('resourceType') != 'Patient':
        return jsonify(create_operation_outcome('error', 'invalid', 'Invalid Patient resource')), 400
    
    data['id'] = patient_id
    current_version = 1
    if idx is not None:
        current_version = int(patients[idx].get('meta', {}).get('versionId', 0)) + 1
        patients[idx] = data
    else:
        patients.append(data)
    
    data['meta'] = {
        'versionId': str(current_version),
        'lastUpdated': datetime.utcnow().isoformat() + 'Z'
    }
    
    return jsonify(data)


# ==================== LOCATION ENDPOINTS ====================

@opensrp_fhir.route('/fhir/Location', methods=['GET'])
def search_locations():
    """
    Search locations.
    Query params: _id, identifier, name, status, type, partof
    """
    locations = get_locations()
    
    location_id = request.args.get('_id')
    identifier = request.args.get('identifier')
    name = request.args.get('name')
    status = request.args.get('status')
    partof = request.args.get('partof')
    
    filtered = locations
    
    if location_id:
        filtered = [l for l in filtered if l['id'] == location_id]
    if identifier:
        filtered = [l for l in filtered if any(
            i.get('value') == identifier for i in l.get('identifier', [])
        )]
    if name:
        name_lower = name.lower()
        filtered = [l for l in filtered if name_lower in l.get('name', '').lower()]
    if status:
        filtered = [l for l in filtered if l.get('status') == status]
    if partof:
        filtered = [l for l in filtered if l.get('partOf', {}).get('reference') == partof]
    
    return jsonify(create_bundle(filtered, 'Location'))


@opensrp_fhir.route('/fhir/Location/<location_id>', methods=['GET'])
def get_location(location_id):
    """Get a specific location by ID."""
    locations = get_locations()
    location = next((l for l in locations if l['id'] == location_id), None)
    
    if not location:
        return jsonify(create_operation_outcome('error', 'not-found', f'Location/{location_id} not found')), 404
    
    return jsonify(location)


@opensrp_fhir.route('/fhir/Location', methods=['POST'])
def create_location():
    """Create a new location."""
    data = request.get_json()
    
    if not data or data.get('resourceType') != 'Location':
        return jsonify(create_operation_outcome('error', 'invalid', 'Invalid Location resource')), 400
    
    if 'id' not in data:
        data['id'] = f'location-{str(uuid.uuid4())[:8]}'
    
    data['meta'] = {
        'versionId': '1',
        'lastUpdated': datetime.utcnow().isoformat() + 'Z'
    }
    
    get_locations().append(data)
    
    response = jsonify(data)
    response.status_code = 201
    response.headers['Location'] = f'/fhir/Location/{data["id"]}'
    return response


# ==================== ORGANIZATION ENDPOINTS ====================

@opensrp_fhir.route('/fhir/Organization', methods=['GET'])
def search_organizations():
    """
    Search organizations.
    Query params: _id, identifier, name, active, type, partof
    """
    organizations = get_organizations()
    
    org_id = request.args.get('_id')
    identifier = request.args.get('identifier')
    name = request.args.get('name')
    active = request.args.get('active')
    partof = request.args.get('partof')
    
    filtered = organizations
    
    if org_id:
        filtered = [o for o in filtered if o['id'] == org_id]
    if identifier:
        filtered = [o for o in filtered if any(
            i.get('value') == identifier for i in o.get('identifier', [])
        )]
    if name:
        name_lower = name.lower()
        filtered = [o for o in filtered if name_lower in o.get('name', '').lower()]
    if active is not None:
        active_bool = active.lower() == 'true'
        filtered = [o for o in filtered if o.get('active') == active_bool]
    if partof:
        filtered = [o for o in filtered if o.get('partOf', {}).get('reference') == partof]
    
    return jsonify(create_bundle(filtered, 'Organization'))


@opensrp_fhir.route('/fhir/Organization/<org_id>', methods=['GET'])
def get_organization(org_id):
    """Get a specific organization by ID."""
    organizations = get_organizations()
    org = next((o for o in organizations if o['id'] == org_id), None)
    
    if not org:
        return jsonify(create_operation_outcome('error', 'not-found', f'Organization/{org_id} not found')), 404
    
    return jsonify(org)


# ==================== PRACTITIONER ENDPOINTS ====================

@opensrp_fhir.route('/fhir/Practitioner', methods=['GET'])
def search_practitioners():
    """
    Search practitioners.
    Query params: _id, identifier, name, active
    """
    practitioners = get_practitioners()
    
    prac_id = request.args.get('_id')
    identifier = request.args.get('identifier')
    name = request.args.get('name')
    active = request.args.get('active')
    
    filtered = practitioners
    
    if prac_id:
        filtered = [p for p in filtered if p['id'] == prac_id]
    if identifier:
        filtered = [p for p in filtered if any(
            i.get('value') == identifier for i in p.get('identifier', [])
        )]
    if name:
        name_lower = name.lower()
        filtered = [p for p in filtered if any(
            name_lower in n.get('family', '').lower() or
            any(name_lower in g.lower() for g in n.get('given', []))
            for n in p.get('name', [])
        )]
    if active is not None:
        active_bool = active.lower() == 'true'
        filtered = [p for p in filtered if p.get('active') == active_bool]
    
    return jsonify(create_bundle(filtered, 'Practitioner'))


@opensrp_fhir.route('/fhir/Practitioner/<prac_id>', methods=['GET'])
def get_practitioner(prac_id):
    """Get a specific practitioner by ID."""
    practitioners = get_practitioners()
    prac = next((p for p in practitioners if p['id'] == prac_id), None)
    
    if not prac:
        return jsonify(create_operation_outcome('error', 'not-found', f'Practitioner/{prac_id} not found')), 404
    
    return jsonify(prac)


# ==================== PRACTITIONER ROLE ENDPOINTS ====================

@opensrp_fhir.route('/fhir/PractitionerRole', methods=['GET'])
def search_practitioner_roles():
    """
    Search practitioner roles.
    Query params: _id, practitioner, organization, location, active
    """
    roles = get_practitioner_roles()
    
    role_id = request.args.get('_id')
    practitioner = request.args.get('practitioner')
    organization = request.args.get('organization')
    location = request.args.get('location')
    active = request.args.get('active')
    
    filtered = roles
    
    if role_id:
        filtered = [r for r in filtered if r['id'] == role_id]
    if practitioner:
        filtered = [r for r in filtered if r.get('practitioner', {}).get('reference') == practitioner]
    if organization:
        filtered = [r for r in filtered if r.get('organization', {}).get('reference') == organization]
    if location:
        filtered = [r for r in filtered if any(
            l.get('reference') == location for l in r.get('location', [])
        )]
    if active is not None:
        active_bool = active.lower() == 'true'
        filtered = [r for r in filtered if r.get('active') == active_bool]
    
    return jsonify(create_bundle(filtered, 'PractitionerRole'))


@opensrp_fhir.route('/fhir/PractitionerRole/<role_id>', methods=['GET'])
def get_practitioner_role(role_id):
    """Get a specific practitioner role by ID."""
    roles = get_practitioner_roles()
    role = next((r for r in roles if r['id'] == role_id), None)
    
    if not role:
        return jsonify(create_operation_outcome('error', 'not-found', f'PractitionerRole/{role_id} not found')), 404
    
    return jsonify(role)


# ==================== METADATA ENDPOINT ====================

@opensrp_fhir.route('/fhir/metadata', methods=['GET'])
def capability_statement():
    """Return FHIR CapabilityStatement (metadata)."""
    return jsonify({
        'resourceType': 'CapabilityStatement',
        'status': 'active',
        'date': '2026-01-17',
        'kind': 'instance',
        'software': {
            'name': 'OpenSRP FHIR Gateway Mock',
            'version': '1.0.0'
        },
        'fhirVersion': '4.0.1',
        'format': ['json'],
        'rest': [
            {
                'mode': 'server',
                'resource': [
                    {'type': 'Patient', 'interaction': [{'code': 'read'}, {'code': 'search-type'}, {'code': 'create'}, {'code': 'update'}]},
                    {'type': 'Location', 'interaction': [{'code': 'read'}, {'code': 'search-type'}, {'code': 'create'}]},
                    {'type': 'Organization', 'interaction': [{'code': 'read'}, {'code': 'search-type'}]},
                    {'type': 'Practitioner', 'interaction': [{'code': 'read'}, {'code': 'search-type'}]},
                    {'type': 'PractitionerRole', 'interaction': [{'code': 'read'}, {'code': 'search-type'}]}
                ]
            }
        ]
    })
