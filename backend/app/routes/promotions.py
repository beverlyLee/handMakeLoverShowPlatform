from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.response_code import ResponseCode
from app.common.auth import login_required
from app.models import Coupon, UserCoupon
from app.database import db
from datetime import datetime

promotion_bp = Blueprint('promotion', __name__)


def get_current_user():
    user_dict = g.get('current_user', {})
    user_id = user_dict.get('user_id')
    return user_dict, user_id


@promotion_bp.route('/coupons', methods=['GET'])
@login_required
def get_coupon_list():
    user_dict, user_id = get_current_user()
    
    status = request.args.get('status', 'available')
    order_amount = request.args.get('order_amount', type=float)
    
    now = datetime.utcnow()
    
    if status == 'available':
        coupons = Coupon.query.filter(
            Coupon.status == 'active',
            Coupon.start_time <= now,
            Coupon.end_time >= now,
            Coupon.used_quantity < Coupon.total_quantity
        ).all()
    elif status == 'my':
        user_coupons = UserCoupon.query.filter_by(user_id=user_id).all()
        coupons = [uc.coupon for uc in user_coupons if uc.coupon]
    else:
        coupons = Coupon.query.filter_by(status='active').all()
    
    result = []
    for coupon in coupons:
        coupon_dict = coupon.to_dict()
        
        if order_amount:
            can_apply, reason = coupon.can_apply(order_amount)
            coupon_dict['can_apply'] = can_apply
            coupon_dict['apply_reason'] = reason
            if can_apply:
                coupon_dict['calculated_discount'] = coupon.calculate_discount(order_amount)
        
        user_coupon = UserCoupon.query.filter_by(
            user_id=user_id,
            coupon_id=coupon.id,
            status='unused'
        ).first()
        coupon_dict['is_received'] = user_coupon is not None
        
        result.append(coupon_dict)
    
    return jsonify(success({
        'coupons': result,
        'total': len(result)
    }))


@promotion_bp.route('/coupons/<int:coupon_id>', methods=['GET'])
@login_required
def get_coupon_detail(coupon_id):
    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='优惠券不存在')), 404
    
    user_dict, user_id = get_current_user()
    user_coupon = UserCoupon.query.filter_by(
        user_id=user_id,
        coupon_id=coupon_id,
        status='unused'
    ).first()
    
    coupon_dict = coupon.to_dict()
    coupon_dict['is_received'] = user_coupon is not None
    
    return jsonify(success(coupon_dict))


@promotion_bp.route('/coupons/<int:coupon_id>/receive', methods=['POST'])
@login_required
def receive_coupon(coupon_id):
    user_dict, user_id = get_current_user()
    
    coupon = Coupon.query.get(coupon_id)
    if not coupon:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='优惠券不存在')), 404
    
    if not coupon.is_valid:
        return jsonify(error(code=ResponseCode.BUSINESS_ERROR, msg='优惠券不可领取')), 400
    
    existing = UserCoupon.query.filter_by(
        user_id=user_id,
        coupon_id=coupon_id
    ).first()
    
    if existing:
        if existing.status == 'unused':
            return jsonify(error(code=ResponseCode.BUSINESS_ERROR, msg='您已领取过该优惠券')), 400
        elif existing.status == 'used':
            return jsonify(error(code=ResponseCode.BUSINESS_ERROR, msg='您已使用过该优惠券')), 400
    
    received_count = UserCoupon.query.filter_by(
        user_id=user_id,
        coupon_id=coupon_id
    ).count()
    
    if coupon.limit_per_user > 0 and received_count >= coupon.limit_per_user:
        return jsonify(error(code=ResponseCode.BUSINESS_ERROR, msg='超出领取限制')), 400
    
    if coupon.used_quantity >= coupon.total_quantity:
        return jsonify(error(code=ResponseCode.BUSINESS_ERROR, msg='优惠券已领完')), 400
    
    user_coupon = UserCoupon(
        user_id=user_id,
        coupon_id=coupon_id,
        status='unused'
    )
    
    coupon.used_quantity += 1
    
    db.session.add(user_coupon)
    db.session.commit()
    
    return jsonify(success({
        'user_coupon_id': user_coupon.id,
        'message': '领取成功'
    }))


@promotion_bp.route('/my-coupons', methods=['GET'])
@login_required
def get_my_coupons():
    user_dict, user_id = get_current_user()
    
    status = request.args.get('status', 'all')
    order_amount = request.args.get('order_amount', type=float)
    
    query = UserCoupon.query.filter_by(user_id=user_id)
    
    if status == 'available':
        query = query.filter(UserCoupon.status == 'unused')
    elif status == 'used':
        query = query.filter(UserCoupon.status == 'used')
    elif status == 'expired':
        query = query.filter(UserCoupon.status == 'expired')
    
    user_coupons = query.order_by(UserCoupon.created_at.desc()).all()
    
    result = []
    for uc in user_coupons:
        uc_dict = uc.to_dict()
        
        if uc.coupon:
            if order_amount and uc.status == 'unused':
                can_apply, reason = uc.coupon.can_apply(order_amount)
                uc_dict['coupon']['can_apply'] = can_apply
                uc_dict['coupon']['apply_reason'] = reason
                if can_apply:
                    uc_dict['coupon']['calculated_discount'] = uc.coupon.calculate_discount(order_amount)
        
        result.append(uc_dict)
    
    return jsonify(success({
        'coupons': result,
        'total': len(result)
    }))


@promotion_bp.route('/my-coupons/<int:user_coupon_id>', methods=['GET'])
@login_required
def get_my_coupon_detail(user_coupon_id):
    user_dict, user_id = get_current_user()
    
    user_coupon = UserCoupon.query.filter_by(
        id=user_coupon_id,
        user_id=user_id
    ).first()
    
    if not user_coupon:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='优惠券不存在')), 404
    
    return jsonify(success(user_coupon.to_dict(include_coupon=True)))


@promotion_bp.route('/coupons/calculate', methods=['POST'])
@login_required
def calculate_discount():
    user_dict, user_id = get_current_user()
    data = request.get_json()
    
    if not data or 'order_amount' not in data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='订单金额不能为空')), 400
    
    order_amount = data.get('order_amount', 0)
    user_coupon_id = data.get('user_coupon_id')
    coupon_id = data.get('coupon_id')
    
    user_coupon = None
    
    if user_coupon_id:
        user_coupon = UserCoupon.query.filter_by(
            id=user_coupon_id,
            user_id=user_id,
            status='unused'
        ).first()
    elif coupon_id:
        user_coupon = UserCoupon.query.filter_by(
            user_id=user_id,
            coupon_id=coupon_id,
            status='unused'
        ).first()
    
    if not user_coupon or not user_coupon.coupon:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='优惠券不存在或已使用')), 404
    
    coupon = user_coupon.coupon
    can_apply, reason = coupon.can_apply(order_amount)
    
    if not can_apply:
        return jsonify(error(code=ResponseCode.BUSINESS_ERROR, msg=reason)), 400
    
    discount_amount = coupon.calculate_discount(order_amount)
    pay_amount = max(order_amount - discount_amount, 0)
    
    return jsonify(success({
        'order_amount': order_amount,
        'discount_amount': discount_amount,
        'pay_amount': pay_amount,
        'coupon_info': {
            'id': coupon.id,
            'name': coupon.name,
            'type': coupon.type,
            'type_name': coupon.type_name,
            'value': coupon.value,
            'discount': coupon.discount,
            'min_amount': coupon.min_amount
        }
    }))
