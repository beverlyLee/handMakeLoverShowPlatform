from flask import Blueprint, jsonify, request

product_bp = Blueprint('products', __name__)

@product_bp.route('/', methods=['GET'])
def get_products():
    return jsonify({
        'message': 'Get products endpoint - to be implemented'
    })

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    return jsonify({
        'message': f'Get product {product_id} endpoint - to be implemented'
    })

@product_bp.route('/', methods=['POST'])
def create_product():
    return jsonify({
        'message': 'Create product endpoint - to be implemented'
    })

@product_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    return jsonify({
        'message': f'Update product {product_id} endpoint - to be implemented'
    })

@product_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    return jsonify({
        'message': f'Delete product {product_id} endpoint - to be implemented'
    })
