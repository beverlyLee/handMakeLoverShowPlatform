from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True)

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'name': 'Handicraft Mini Program API',
            'version': '1.0.0',
            'status': 'running',
            'message': '欢迎使用手作爱好者展示平台后端API',
            'endpoints': {
                'health_check': 'GET /api/health',
                'api_info': 'GET /api/info',
                'auth': '/api/auth',
                'products': '/api/products',
                'orders': '/api/orders',
                'users': '/api/users',
                'messages': '/api/messages',
                'reviews': '/api/reviews',
                'cart': '/api/cart',
                'favorites': '/api/favorites',
                'search': '/api/search',
                'role_switch': '/api/role-switch'
            }
        })

    from app.routes import main_bp, auth_bp, product_bp, order_bp, user_bp, message_bp, review_bp, cart_bp, favorite_bp, search_bp, role_switch_bp

    app.register_blueprint(main_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(message_bp, url_prefix='/api/messages')
    app.register_blueprint(review_bp, url_prefix='/api/reviews')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(favorite_bp, url_prefix='/api/favorites')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(role_switch_bp, url_prefix='/api/role-switch')

    return app
