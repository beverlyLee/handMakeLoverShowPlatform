from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.products import product_bp
from app.routes.orders import order_bp
from app.routes.users import user_bp
from app.routes.messages import message_bp
from app.routes.reviews import review_bp
from app.routes.cart import cart_bp
from app.routes.favorites import favorite_bp
from app.routes.search import search_bp
from app.routes.specialties import specialty_bp
from app.routes.promotions import promotion_bp
from app.routes.upload import upload_bp
from app.routes.activities import activity_bp

__all__ = [
    'main_bp', 'auth_bp', 'product_bp', 'order_bp', 'user_bp',
    'message_bp', 'review_bp', 'cart_bp', 'favorite_bp', 'search_bp',
    'specialty_bp', 'promotion_bp', 'upload_bp', 'activity_bp'
]
