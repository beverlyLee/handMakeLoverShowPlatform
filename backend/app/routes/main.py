from flask import Blueprint, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Handicraft API is running'
    })

@main_bp.route('/info', methods=['GET'])
def api_info():
    return jsonify({
        'version': '1.0.0',
        'description': 'Handicraft Mini Program Backend API',
        'endpoints': {
            'auth': '/api/auth',
            'products': '/api/products',
            'orders': '/api/orders',
            'users': '/api/users',
            'messages': '/api/messages',
            'reviews': '/api/reviews',
            'cart': '/api/cart',
            'favorites': '/api/favorites',
            'search': '/api/search'
        }
    })
