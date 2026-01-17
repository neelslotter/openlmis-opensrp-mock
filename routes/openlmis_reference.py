"""
OpenLMIS Reference Data Mock Routes
"""
import json
import os
from flask import Blueprint, request, jsonify

openlmis_reference = Blueprint('openlmis_reference', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_reference_data():
    with open(os.path.join(DATA_DIR, 'reference.json'), 'r') as f:
        return json.load(f)


@openlmis_reference.route('/api/facilities', methods=['GET'])
def list_facilities():
    """List all facilities."""
    data = load_reference_data()
    facilities = data['facilities']
    
    # Optional filtering
    active = request.args.get('active')
    zone_id = request.args.get('zoneId')
    
    filtered = facilities
    if active is not None:
        active_bool = active.lower() == 'true'
        filtered = [f for f in filtered if f['active'] == active_bool]
    if zone_id:
        filtered = [f for f in filtered if f['geographicZone']['id'] == zone_id]
    
    return jsonify({
        'content': filtered,
        'totalElements': len(filtered)
    })


@openlmis_reference.route('/api/facilities/<facility_id>', methods=['GET'])
def get_facility(facility_id):
    """Get a specific facility."""
    data = load_reference_data()
    facility = next((f for f in data['facilities'] if f['id'] == facility_id), None)
    
    if not facility:
        return jsonify({'error': 'Facility not found'}), 404
    
    return jsonify(facility)


@openlmis_reference.route('/api/programs', methods=['GET'])
def list_programs():
    """List all programs."""
    data = load_reference_data()
    programs = data['programs']
    
    active = request.args.get('active')
    if active is not None:
        active_bool = active.lower() == 'true'
        programs = [p for p in programs if p['active'] == active_bool]
    
    return jsonify({
        'content': programs,
        'totalElements': len(programs)
    })


@openlmis_reference.route('/api/programs/<program_id>', methods=['GET'])
def get_program(program_id):
    """Get a specific program."""
    data = load_reference_data()
    program = next((p for p in data['programs'] if p['id'] == program_id), None)
    
    if not program:
        return jsonify({'error': 'Program not found'}), 404
    
    return jsonify(program)


@openlmis_reference.route('/api/orderables', methods=['GET'])
def list_orderables():
    """List all orderables (products)."""
    data = load_reference_data()
    orderables = data['orderables']
    
    # Search by code
    code = request.args.get('code')
    if code:
        orderables = [o for o in orderables if code.lower() in o['productCode'].lower()]
    
    return jsonify({
        'content': orderables,
        'totalElements': len(orderables)
    })


@openlmis_reference.route('/api/orderables/<orderable_id>', methods=['GET'])
def get_orderable(orderable_id):
    """Get a specific orderable."""
    data = load_reference_data()
    orderable = next((o for o in data['orderables'] if o['id'] == orderable_id), None)
    
    if not orderable:
        return jsonify({'error': 'Orderable not found'}), 404
    
    return jsonify(orderable)


@openlmis_reference.route('/api/processingPeriods', methods=['GET'])
def list_processing_periods():
    """List processing periods."""
    data = load_reference_data()
    periods = data['processingPeriods']
    
    return jsonify({
        'content': periods,
        'totalElements': len(periods)
    })


@openlmis_reference.route('/api/processingPeriods/<period_id>', methods=['GET'])
def get_processing_period(period_id):
    """Get a specific processing period."""
    data = load_reference_data()
    period = next((p for p in data['processingPeriods'] if p['id'] == period_id), None)
    
    if not period:
        return jsonify({'error': 'Processing period not found'}), 404
    
    return jsonify(period)


@openlmis_reference.route('/api/geographicZones', methods=['GET'])
def list_geographic_zones():
    """List geographic zones (extracted from facilities)."""
    data = load_reference_data()
    zones = {}
    for facility in data['facilities']:
        zone = facility.get('geographicZone', {})
        if zone.get('id'):
            zones[zone['id']] = zone
    
    zone_list = list(zones.values())
    return jsonify({
        'content': zone_list,
        'totalElements': len(zone_list)
    })


@openlmis_reference.route('/api/facilityTypes', methods=['GET'])
def list_facility_types():
    """List facility types."""
    data = load_reference_data()
    types = {}
    for facility in data['facilities']:
        ftype = facility.get('type', {})
        if ftype.get('id'):
            types[ftype['id']] = ftype
    
    type_list = list(types.values())
    return jsonify({
        'content': type_list,
        'totalElements': len(type_list)
    })
