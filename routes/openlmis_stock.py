"""
OpenLMIS Stock Management Mock Routes
"""
import json
import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify

openlmis_stock = Blueprint('openlmis_stock', __name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_stock_data():
    with open(os.path.join(DATA_DIR, 'stock.json'), 'r') as f:
        return json.load(f)

# In-memory store
stock_data = None

def get_stock_data():
    global stock_data
    if stock_data is None:
        stock_data = load_stock_data()
    return stock_data


@openlmis_stock.route('/api/stockCards', methods=['GET'])
def get_stock_cards():
    """
    Get stock cards.
    Query params: facilityId, programId, orderableId
    """
    data = get_stock_data()
    cards = data['stockCards']
    
    facility_id = request.args.get('facilityId')
    program_id = request.args.get('programId')
    orderable_id = request.args.get('orderableId')
    
    filtered = cards
    
    if facility_id:
        filtered = [c for c in filtered if c['facilityId'] == facility_id]
    if program_id:
        filtered = [c for c in filtered if c['programId'] == program_id]
    if orderable_id:
        filtered = [c for c in filtered if c['orderableId'] == orderable_id]
    
    return jsonify({
        'content': filtered,
        'totalElements': len(filtered)
    })


@openlmis_stock.route('/api/stockCards/<card_id>', methods=['GET'])
def get_stock_card(card_id):
    """Get a specific stock card."""
    data = get_stock_data()
    card = next((c for c in data['stockCards'] if c['id'] == card_id), None)
    
    if not card:
        return jsonify({'error': 'Stock card not found'}), 404
    
    return jsonify(card)


@openlmis_stock.route('/api/stockCardSummaries', methods=['GET'])
def get_stock_summaries():
    """
    Get stock card summaries (aggregated view).
    """
    data = get_stock_data()
    cards = data['stockCards']
    
    facility_id = request.args.get('facilityId')
    program_id = request.args.get('programId')
    
    filtered = cards
    if facility_id:
        filtered = [c for c in filtered if c['facilityId'] == facility_id]
    if program_id:
        filtered = [c for c in filtered if c['programId'] == program_id]
    
    summaries = [
        {
            'stockCard': {'id': c['id']},
            'orderable': {'id': c['orderableId']},
            'stockOnHand': c['stockOnHand']
        }
        for c in filtered
    ]
    
    return jsonify({
        'content': summaries,
        'totalElements': len(summaries)
    })


@openlmis_stock.route('/api/stockEvents', methods=['POST'])
def create_stock_event():
    """
    Record a stock event (receive, issue, adjustment).
    """
    event_data = request.get_json()
    
    if not event_data:
        return jsonify({'error': 'Request body required'}), 400
    
    data = get_stock_data()
    
    # Process each line item in the event
    line_items = event_data.get('lineItems', [])
    
    for item in line_items:
        orderable_id = item.get('orderableId')
        quantity = item.get('quantity', 0)
        reason_id = item.get('reasonId')
        
        # Find matching stock card
        card = next(
            (c for c in data['stockCards'] if c['orderableId'] == orderable_id),
            None
        )
        
        if card:
            # Add line item to card
            new_line = {
                'id': str(uuid.uuid4()),
                'occurredDate': item.get('occurredDate', datetime.utcnow().strftime('%Y-%m-%d')),
                'quantity': quantity,
                'reason': reason_id or 'ADJUSTMENT',
                'source': item.get('sourceId'),
                'destination': item.get('destinationId')
            }
            card['lineItems'].append(new_line)
            card['stockOnHand'] += quantity
    
    return jsonify({
        'id': str(uuid.uuid4()),
        'status': 'PROCESSED',
        'lineItems': len(line_items)
    }), 201


@openlmis_stock.route('/api/validSources', methods=['GET'])
def get_valid_sources():
    """Get valid stock sources for a facility/program."""
    data = get_stock_data()
    return jsonify({
        'content': data['validSources'],
        'totalElements': len(data['validSources'])
    })


@openlmis_stock.route('/api/validDestinations', methods=['GET'])
def get_valid_destinations():
    """Get valid destinations for stock issues."""
    data = get_stock_data()
    return jsonify({
        'content': data['validDestinations'],
        'totalElements': len(data['validDestinations'])
    })


@openlmis_stock.route('/api/stockCardLineItemReasons', methods=['GET'])
def get_line_item_reasons():
    """Get stock adjustment reasons."""
    reasons = [
        {'id': 'reason-receive', 'name': 'Receipt', 'reasonType': 'CREDIT'},
        {'id': 'reason-issue', 'name': 'Issue', 'reasonType': 'DEBIT'},
        {'id': 'reason-adjustment-pos', 'name': 'Positive Adjustment', 'reasonType': 'CREDIT'},
        {'id': 'reason-adjustment-neg', 'name': 'Negative Adjustment', 'reasonType': 'DEBIT'},
        {'id': 'reason-expired', 'name': 'Expired', 'reasonType': 'DEBIT'},
        {'id': 'reason-damaged', 'name': 'Damaged', 'reasonType': 'DEBIT'}
    ]
    return jsonify({
        'content': reasons,
        'totalElements': len(reasons)
    })
