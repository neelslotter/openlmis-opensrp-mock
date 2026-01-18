#!/usr/bin/env python3
"""
OpenLMIS 2 & OpenSRP 2 FHIR Gateway Mock Server

A Flask-based mock server that simulates:
- OpenLMIS 2 backend APIs (auth, requisitions, stock, reference data)
- OpenSRP 2 FHIR Gateway (Patient, Location, Organization, Practitioner)

Usage:
    python app.py [--port PORT] [--host HOST]
    
Default: http://localhost:5000
"""

import argparse
from flask import Flask, jsonify
from flask_cors import CORS

# Import route blueprints
from routes.openlmis_auth import openlmis_auth
from routes.openlmis_requisition import openlmis_requisition
from routes.openlmis_stock import openlmis_stock
from routes.openlmis_reference import openlmis_reference
from routes.opensrp_fhir import opensrp_fhir
from routes.webhooks import webhooks


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(openlmis_auth)
    app.register_blueprint(openlmis_requisition)
    app.register_blueprint(openlmis_stock)
    app.register_blueprint(openlmis_reference)
    app.register_blueprint(opensrp_fhir)
    app.register_blueprint(webhooks)
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'name': 'OpenLMIS & OpenSRP Mock Server',
            'version': '1.0.0',
            'services': {
                'openlmis': {
                    'description': 'OpenLMIS 2 Backend Mock',
                    'endpoints': {
                        'auth': '/api/oauth/token',
                        'users': '/api/users',
                        'requisitions': '/api/requisitions',
                        'stockCards': '/api/stockCards',
                        'facilities': '/api/facilities',
                        'programs': '/api/programs',
                        'orderables': '/api/orderables'
                    }
                },
                'opensrp_fhir': {
                    'description': 'OpenSRP 2 FHIR Gateway Mock',
                    'fhirVersion': '4.0.1',
                    'endpoints': {
                        'metadata': '/fhir/metadata',
                        'patient': '/fhir/Patient',
                        'location': '/fhir/Location',
                        'organization': '/fhir/Organization',
                        'practitioner': '/fhir/Practitioner',
                        'practitionerRole': '/fhir/PractitionerRole'
                    }
                }
            },
            'defaultCredentials': {
                'username': 'administrator',
                'password': 'password'
            }
        })
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'})
    
    # Admin UI endpoint
    @app.route('/admin')
    def admin():
        return app.send_static_file('admin.html')
    
    return app


def main():
    parser = argparse.ArgumentParser(description='OpenLMIS & OpenSRP Mock Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5003, help='Port to listen on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    app = create_app()
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║       OpenLMIS & OpenSRP FHIR Gateway Mock Server            ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://{args.host}:{args.port:<24}       ║
║  Admin Console:     http://{args.host}:{args.port}/admin{' ':<13}       ║
║                                                              ║
║  OpenLMIS Endpoints:                                         ║
║    POST /api/oauth/token     - Get access token              ║
║    GET  /api/requisitions    - List requisitions             ║
║    GET  /api/stockCards      - List stock cards              ║
║    GET  /api/facilities      - List facilities               ║
║                                                              ║
║  OpenSRP FHIR Endpoints:                                     ║
║    GET  /fhir/Patient        - Search patients               ║
║    GET  /fhir/Location       - Search locations              ║
║    GET  /fhir/Organization   - Search organizations          ║
║    GET  /fhir/Practitioner   - Search practitioners          ║
║    GET  /fhir/metadata       - FHIR CapabilityStatement      ║
║                                                              ║
║  Default credentials: administrator / password               ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
