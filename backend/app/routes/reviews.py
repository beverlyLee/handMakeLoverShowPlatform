from flask import Blueprint, jsonify, request

review_bp = Blueprint('reviews', __name__)

@review_bp.route('/', methods=['GET'])
def get_reviews():
    return jsonify({
        'message': 'Get reviews endpoint - to be implemented'
    })

@review_bp.route('/', methods=['POST'])
def create_review():
    return jsonify({
        'message': 'Create review endpoint - to be implemented'
    })

@review_bp.route('/<int:review_id>', methods=['GET'])
def get_review(review_id):
    return jsonify({
        'message': f'Get review {review_id} endpoint - to be implemented'
    })

@review_bp.route('/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    return jsonify({
        'message': f'Update review {review_id} endpoint - to be implemented'
    })

@review_bp.route('/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    return jsonify({
        'message': f'Delete review {review_id} endpoint - to be implemented'
    })

@review_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_reviews(product_id):
    return jsonify({
        'message': f'Get product {product_id} reviews endpoint - to be implemented'
    })
