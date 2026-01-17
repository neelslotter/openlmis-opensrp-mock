"""
OpenLMIS Requisition Mock Routes
"""
import json
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

openlmis_requisition = Blueprint('openlmis_requisition', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_requisitions():
    with open(os.path.join(DATA_DIR, 'requisitions.json'), 'r') as f:
        return json.load(f)['requisitions']

# In-memory store for modifications
requisitions_store = None

def get_requisitions():
    global requisitions_store
    if requisitions_store is None:
        requisitions_store = load_requisitions()
    return requisitions_store


@openlmis_requisition.route('/api/requisitions', methods=['GET'])
def list_requisitions():
    """
    List requisitions with optional filtering.
    Query params: facilityId, programId, processingPeriodId, status
    """
    requisitions = get_requisitions()
    
    # Apply filters
    facility_id = request.args.get('facilityId')
    program_id = request.args.get('programId')
    period_id = request.args.get('processingPeriodId')
    status = request.args.get('status')
    
    filtered = requisitions
    
    if facility_id:
        filtered = [r for r in filtered if r['facilityId'] == facility_id]
    if program_id:
        filtered = [r for r in filtered if r['programId'] == program_id]
    if period_id:
        filtered = [r for r in filtered if r['processingPeriodId'] == period_id]
    if status:
        filtered = [r for r in filtered if r['status'] == status]
    
    return jsonify({
        'content': filtered,
        'totalElements': len(filtered),
        'totalPages': 1,
        'size': len(filtered),
        'number': 0
    })


@openlmis_requisition.route('/api/requisitions/<req_id>', methods=['GET'])
def get_requisition(req_id):
    """Get a specific requisition by ID."""
    requisitions = get_requisitions()
    req = next((r for r in requisitions if r['id'] == req_id), None)
    
    if not req:
        return jsonify({'error': 'Requisition not found'}), 404
    
    return jsonify(req)


@openlmis_requisition.route('/api/requisitions', methods=['POST'])
def create_requisition():
    """
    Initiate a new requisition.
    Required: facilityId, programId, processingPeriodId
    """
    data = request.get_json()
    
    if not all(k in data for k in ['facilityId', 'programId', 'processingPeriodId']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    new_req = {
        'id': str(uuid.uuid4()),
        'facilityId': data['facilityId'],
        'programId': data['programId'],
        'processingPeriodId': data['processingPeriodId'],
        'status': 'INITIATED',
        'emergency': data.get('emergency', False),
        'createdDate': datetime.utcnow().isoformat() + 'Z',
        'modifiedDate': datetime.utcnow().isoformat() + 'Z',
        'requisitionLineItems': data.get('requisitionLineItems', [])
    }
    
    get_requisitions().append(new_req)
    return jsonify(new_req), 201


@openlmis_requisition.route('/api/requisitions/<req_id>/save', methods=['PUT'])
def save_requisition(req_id):
    """Save changes to a requisition."""
    requisitions = get_requisitions()
    req = next((r for r in requisitions if r['id'] == req_id), None)
    
    if not req:
        return jsonify({'error': 'Requisition not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'requisitionLineItems' in data:
        req['requisitionLineItems'] = data['requisitionLineItems']
    
    req['modifiedDate'] = datetime.utcnow().isoformat() + 'Z'
    
    return jsonify(req)


@openlmis_requisition.route('/api/requisitions/<req_id>/submit', methods=['PUT'])
def submit_requisition(req_id):
    """Submit a requisition for approval."""
    requisitions = get_requisitions()
    req = next((r for r in requisitions if r['id'] == req_id), None)
    
    if not req:
        return jsonify({'error': 'Requisition not found'}), 404
    
    if req['status'] != 'INITIATED':
        return jsonify({'error': f"Cannot submit requisition in {req['status']} status"}), 400
    
    req['status'] = 'SUBMITTED'
    req['modifiedDate'] = datetime.utcnow().isoformat() + 'Z'
    
    return jsonify(req)


@openlmis_requisition.route('/api/requisitions/<req_id>/authorize', methods=['PUT'])
def authorize_requisition(req_id):
    """Authorize a submitted requisition."""
    requisitions = get_requisitions()
    req = next((r for r in requisitions if r['id'] == req_id), None)
    
    if not req:
        return jsonify({'error': 'Requisition not found'}), 404
    
    if req['status'] != 'SUBMITTED':
        return jsonify({'error': f"Cannot authorize requisition in {req['status']} status"}), 400
    
    req['status'] = 'AUTHORIZED'
    req['modifiedDate'] = datetime.utcnow().isoformat() + 'Z'
    
    return jsonify(req)


@openlmis_requisition.route('/api/requisitions/<req_id>/approve', methods=['PUT'])
def approve_requisition(req_id):
    """Approve an authorized requisition."""
    requisitions = get_requisitions()
    req = next((r for r in requisitions if r['id'] == req_id), None)
    
    if not req:
        return jsonify({'error': 'Requisition not found'}), 404
    
    if req['status'] != 'AUTHORIZED':
        return jsonify({'error': f"Cannot approve requisition in {req['status']} status"}), 400
    
    req['status'] = 'APPROVED'
    req['modifiedDate'] = datetime.utcnow().isoformat() + 'Z'
    
    return jsonify(req)


@openlmis_requisition.route('/api/requisitions-for-approval', methods=['GET'])
def requisitions_for_approval():
    """Get requisitions pending approval."""
    requisitions = get_requisitions()
    pending = [r for r in requisitions if r['status'] in ['SUBMITTED', 'AUTHORIZED']]
    
    return jsonify({
        'content': pending,
        'totalElements': len(pending)
    })


@openlmis_requisition.route('/api/requisitions-for-convert-to-order', methods=['GET'])
def requisitions_for_convert():
    """Get approved requisitions ready to convert to orders."""
    requisitions = get_requisitions()
    approved = [r for r in requisitions if r['status'] == 'APPROVED']
    
    return jsonify({
        'content': approved,
        'totalElements': len(approved)
    })
