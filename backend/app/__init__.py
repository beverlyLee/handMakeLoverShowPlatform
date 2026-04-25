from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config
from app.extensions import db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True)
    
    db.init_app(app)
    
    with app.app_context():
        from app.models import User, Address
        db.create_all()
        
        if not User.query.first():
            from datetime import datetime
            test_user = User(
                openid='oTestOpenid123456',
                username='handmade_lover',
                nickname='手作爱好者',
                avatar='https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20crafts%20lover%20avatar&image_size=square',
                phone='138****8888',
                email='handmade@example.com',
                gender=1,
                role='customer',
                bio='热爱手作，喜欢制作各种手工制品',
                session_key='mock_session_key_test_code_1'
            )
            db.session.add(test_user)
            db.session.commit()
            
            default_address = Address(
                user_id=test_user.id,
                name='张三',
                phone='138****8888',
                province='广东省',
                city='深圳市',
                district='南山区',
                detail='科技园南区A栋1001室',
                is_default=True
            )
            db.session.add(default_address)
            
            second_address = Address(
                user_id=test_user.id,
                name='李四',
                phone='139****9999',
                province='广东省',
                city='广州市',
                district='天河区',
                detail='体育西路天河城B座2002室',
                is_default=False
            )
            db.session.add(second_address)
            db.session.commit()

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
                'search': '/api/search'
            }
        })

    from app.routes import main_bp, auth_bp, product_bp, order_bp, user_bp, message_bp, review_bp, cart_bp, favorite_bp, search_bp

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

    return app
