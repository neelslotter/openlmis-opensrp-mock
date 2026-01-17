"""
Webhook Receiver and Event Management Routes

Provides endpoints for:
- Receiving webhooks from OpenLMIS and OpenSRP
- Listing received events
- Simulating events for testing
"""
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

webhooks = Blueprint('webhooks', __name__)

# In-memory event store
events_store = []
MAX_EVENTS = 100  # Keep last 100 events


def add_event(source, event_type, payload):
    """Add an event to the store."""
    event = {
        'id': str(uuid.uuid4()),
        'source': source,
        'type': event_type,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'payload': payload
    }
    events_store.insert(0, event)  # Add to front
    
    # Trim to max size
    while len(events_store) > MAX_EVENTS:
        events_store.pop()
    
    return event


# ==================== EVENT LISTING ====================

@webhooks.route('/api/events', methods=['GET'])
def list_events():
    """List all received events."""
    source = request.args.get('source')
    event_type = request.args.get('type')
    limit = request.args.get('limit', 50, type=int)
    
    filtered = events_store
    
    if source:
        filtered = [e for e in filtered if e['source'] == source]
    if event_type:
        filtered = [e for e in filtered if e['type'] == event_type]
    
    return jsonify({
        'events': filtered[:limit],
        'total': len(filtered)
    })


@webhooks.route('/api/events', methods=['DELETE'])
def clear_events():
    """Clear all events."""
    events_store.clear()
    return jsonify({'message': 'All events cleared'})


# ==================== OPENLMIS WEBHOOKS ====================

@webhooks.route('/webhooks/openlmis', methods=['POST'])
def openlmis_webhook():
    """
    Receive webhooks from OpenLMIS.
    Expected event types:
    - requisition.statusChange
    - stockCard.update
    - order.created
    - order.fulfilled
    """
    data = request.get_json() or {}
    
    event_type = data.get('type', 'unknown')
    
    event = add_event(
        source='openlmis',
        event_type=event_type,
        payload=data
    )
    
    return jsonify({
        'received': True,
        'eventId': event['id'],
        'timestamp': event['timestamp']
    }), 201


@webhooks.route('/webhooks/openlmis/requisitions', methods=['POST'])
def openlmis_requisition_webhook():
    """Webhook specifically for requisition events."""
    data = request.get_json() or {}
    
    event = add_event(
        source='openlmis',
        event_type='requisition.' + data.get('action', 'update'),
        payload=data
    )
    
    return jsonify({
        'received': True,
        'eventId': event['id']
    }), 201


@webhooks.route('/webhooks/openlmis/stock', methods=['POST'])
def openlmis_stock_webhook():
    """Webhook specifically for stock events."""
    data = request.get_json() or {}
    
    event = add_event(
        source='openlmis',
        event_type='stock.' + data.get('action', 'update'),
        payload=data
    )
    
    return jsonify({
        'received': True,
        'eventId': event['id']
    }), 201


# ==================== OPENSRP WEBHOOKS ====================

@webhooks.route('/webhooks/opensrp', methods=['POST'])
def opensrp_webhook():
    """
    Receive webhooks from OpenSRP/FHIR Gateway.
    Expected event types:
    - patient.created
    - patient.updated
    - encounter.created
    - task.completed
    - questionnaire.submitted
    """
    data = request.get_json() or {}
    
    # FHIR events may come as Bundles
    resource_type = data.get('resourceType', 'unknown')
    event_type = data.get('type', resource_type.lower())
    
    event = add_event(
        source='opensrp',
        event_type=event_type,
        payload=data
    )
    
    return jsonify({
        'received': True,
        'eventId': event['id'],
        'timestamp': event['timestamp']
    }), 201


@webhooks.route('/webhooks/opensrp/patient', methods=['POST'])
def opensrp_patient_webhook():
    """Webhook for patient events."""
    data = request.get_json() or {}
    
    action = 'updated' if data.get('id') else 'created'
    
    event = add_event(
        source='opensrp',
        event_type=f'patient.{action}',
        payload=data
    )
    
    return jsonify({
        'received': True,
        'eventId': event['id']
    }), 201


@webhooks.route('/webhooks/opensrp/encounter', methods=['POST'])
def opensrp_encounter_webhook():
    """Webhook for encounter/visit events."""
    data = request.get_json() or {}
    
    event = add_event(
        source='opensrp',
        event_type='encounter.created',
        payload=data
    )
    
    return jsonify({
        'received': True,
        'eventId': event['id']
    }), 201


# ==================== EVENT SIMULATION ====================

@webhooks.route('/api/events/simulate', methods=['POST'])
def simulate_event():
    """
    Simulate an event for testing purposes.
    Body: { source: 'openlmis'|'opensrp', type: string, payload: object }
    """
    data = request.get_json() or {}
    
    source = data.get('source', 'openlmis')
    event_type = data.get('type', 'test.event')
    payload = data.get('payload', {})
    
    event = add_event(
        source=source,
        event_type=event_type,
        payload=payload
    )
    
    return jsonify({
        'simulated': True,
        'event': event
    }), 201


@webhooks.route('/api/events/simulate/openlmis/requisition', methods=['POST'])
def simulate_requisition_event():
    """Simulate an OpenLMIS requisition status change event."""
    data = request.get_json() or {}
    
    payload = {
        'requisitionId': data.get('requisitionId', 'req-001-uuid-mock'),
        'previousStatus': data.get('previousStatus', 'INITIATED'),
        'newStatus': data.get('newStatus', 'SUBMITTED'),
        'facilityId': data.get('facilityId', 'fac-001'),
        'programId': data.get('programId', 'prog-essential-meds'),
        'userId': data.get('userId', 'user-001'),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    event = add_event(
        source='openlmis',
        event_type='requisition.statusChange',
        payload=payload
    )
    
    return jsonify({
        'simulated': True,
        'event': event
    }), 201


@webhooks.route('/api/events/simulate/openlmis/stock', methods=['POST'])
def simulate_stock_event():
    """Simulate an OpenLMIS stock update event."""
    data = request.get_json() or {}
    
    payload = {
        'stockCardId': data.get('stockCardId', 'stock-card-001'),
        'facilityId': data.get('facilityId', 'fac-001'),
        'orderableId': data.get('orderableId', 'orderable-paracetamol'),
        'quantity': data.get('quantity', 100),
        'reason': data.get('reason', 'RECEIVE'),
        'stockOnHand': data.get('stockOnHand', 170),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    event = add_event(
        source='openlmis',
        event_type='stock.updated',
        payload=payload
    )
    
    return jsonify({
        'simulated': True,
        'event': event
    }), 201


@webhooks.route('/api/events/simulate/opensrp/patient', methods=['POST'])
def simulate_patient_event():
    """Simulate an OpenSRP patient event."""
    data = request.get_json() or {}
    
    action = data.get('action', 'created')
    
    payload = {
        'resourceType': 'Patient',
        'id': data.get('patientId', 'patient-new-001'),
        'name': [{'family': data.get('family', 'Test'), 'given': [data.get('given', 'Patient')]}],
        'gender': data.get('gender', 'male'),
        'birthDate': data.get('birthDate', '1990-01-01'),
        'meta': {
            'lastUpdated': datetime.utcnow().isoformat() + 'Z'
        }
    }
    
    event = add_event(
        source='opensrp',
        event_type=f'patient.{action}',
        payload=payload
    )
    
    return jsonify({
        'simulated': True,
        'event': event
    }), 201


@webhooks.route('/api/events/simulate/opensrp/encounter', methods=['POST'])
def simulate_encounter_event():
    """Simulate an OpenSRP encounter/visit event."""
    data = request.get_json() or {}
    
    payload = {
        'resourceType': 'Encounter',
        'id': data.get('encounterId', f'encounter-{uuid.uuid4().hex[:8]}'),
        'status': 'finished',
        'class': {'code': 'AMB', 'display': 'ambulatory'},
        'subject': {'reference': f"Patient/{data.get('patientId', 'patient-001')}"},
        'period': {
            'start': datetime.utcnow().isoformat() + 'Z',
            'end': datetime.utcnow().isoformat() + 'Z'
        },
        'serviceProvider': {'reference': f"Organization/{data.get('organizationId', 'org-001')}"}
    }
    
    event = add_event(
        source='opensrp',
        event_type='encounter.created',
        payload=payload
    )
    
    return jsonify({
        'simulated': True,
        'event': event
    }), 201
