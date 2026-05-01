from datetime import datetime
from flask import Blueprint, jsonify, request, g
from app.utils.response import success, error
from app.common.auth import login_required
from app.common.response_code import ResponseCode
from app.database import db
from app.models import Activity, ActivityRegistration, TeacherProfile, User, CRAFT_TYPES, ACTIVITY_TYPES, ActivityType, Category

activity_bp = Blueprint('activities', __name__)


def get_current_teacher_profile():
    user_id = g.get('user_id')
    if not user_id:
        return None
    profile = TeacherProfile.query.filter_by(user_id=user_id).first()
    return profile


def parse_datetime(datetime_str):
    if not datetime_str:
        return None
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d'
    ]
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    return None


@activity_bp.route('/types', methods=['GET'])
def get_activity_types():
    craft_types_db = Category.query.filter_by(status='active').order_by(Category.sort.asc()).all()
    activity_types_db = ActivityType.query.filter_by(status='active').order_by(ActivityType.sort.asc()).all()
    
    craft_types = []
    activity_types = []
    
    if craft_types_db and len(craft_types_db) > 0:
        craft_types = [c.name for c in craft_types_db]
    else:
        craft_types = CRAFT_TYPES
    
    if activity_types_db and len(activity_types_db) > 0:
        activity_types = [a.name for a in activity_types_db]
    else:
        activity_types = ACTIVITY_TYPES
    
    return jsonify(success(data={
        'craft_types': craft_types,
        'activity_types': activity_types
    }))


@activity_bp.route('/latest', methods=['GET'])
def get_latest_activities():
    limit = request.args.get('limit', 3, type=int)
    
    activities = Activity.query.filter_by(
        status='active'
    ).order_by(
        Activity.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for activity in activities:
        activity_dict = activity.to_dict(include_teacher=True)
        result.append(activity_dict)
    
    return jsonify(success(data=result))


@activity_bp.route('', methods=['GET'])
def get_activities():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    craft_type = request.args.get('craft_type', None, type=str)
    activity_type = request.args.get('activity_type', None, type=str)
    teacher_id = request.args.get('teacher_id', None, type=int)
    status = request.args.get('status', 'active', type=str)
    keyword = request.args.get('keyword', None, type=str)
    city = request.args.get('city', None, type=str)
    
    query = Activity.query
    
    if status:
        query = query.filter(Activity.status == status)
    
    if craft_type and craft_type != '全部':
        query = query.filter(Activity.craft_type == craft_type)
    
    if activity_type and activity_type != '全部':
        query = query.filter(Activity.activity_type == activity_type)
    
    if teacher_id:
        query = query.filter(Activity.teacher_id == teacher_id)
    
    if keyword:
        query = query.filter(
            db.or_(
                Activity.title.contains(keyword),
                Activity.description.contains(keyword)
            )
        )
    
    if city:
        query = query.filter(Activity.city == city)
    
    query = query.order_by(Activity.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    activities = []
    for activity in pagination.items:
        activity_dict = activity.to_dict(include_teacher=True)
        activities.append(activity_dict)
    
    return jsonify(success(data={
        'list': activities,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    }))


@activity_bp.route('/<int:activity_id>', methods=['GET'])
def get_activity_detail(activity_id):
    activity = Activity.query.get(activity_id)
    
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在')), 404
    
    activity.view_count = (activity.view_count or 0) + 1
    db.session.commit()
    
    activity_dict = activity.to_dict(include_teacher=True)
    
    user_id = g.get('user_id')
    if user_id:
        registration = ActivityRegistration.query.filter_by(
            activity_id=activity_id,
            user_id=user_id
        ).first()
        activity_dict['is_registered'] = registration is not None
        if registration:
            activity_dict['registration_status'] = registration.status
    else:
        activity_dict['is_registered'] = False
    
    return jsonify(success(data=activity_dict))


@activity_bp.route('', methods=['POST'])
@login_required
def create_activity():
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    if 'title' not in data or not data.get('title'):
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='活动标题不能为空')), 400
    
    activity = Activity(
        teacher_id=teacher_profile.id,
        title=data.get('title'),
        description=data.get('description', ''),
        craft_type=data.get('craft_type', '其他'),
        activity_type=data.get('activity_type', '其他'),
        start_time=parse_datetime(data.get('start_time')),
        end_time=parse_datetime(data.get('end_time')),
        registration_start_time=parse_datetime(data.get('registration_start_time')),
        registration_deadline=parse_datetime(data.get('registration_deadline')),
        location=data.get('location'),
        address=data.get('address'),
        city=data.get('city'),
        price=float(data.get('price', 0)),
        original_price=float(data.get('original_price', 0)) if data.get('original_price') else float(data.get('price', 0)),
        max_participants=int(data.get('max_participants', 999)),
        current_participants=0,
        status=data.get('status', 'active')
    )
    
    images = data.get('images')
    if images and isinstance(images, list):
        activity.images = images
        if len(images) > 0:
            activity.cover_image = images[0]
    
    if data.get('cover_image'):
        activity.cover_image = data.get('cover_image')
    
    if data.get('tags'):
        activity.tags = data.get('tags')
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify(success(data=activity.to_dict(), msg='活动创建成功'))


@activity_bp.route('/<int:activity_id>', methods=['PUT'])
@login_required
def update_activity(activity_id):
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    activity = Activity.query.filter_by(id=activity_id, teacher_id=teacher_profile.id).first()
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在或无权编辑')), 404
    
    data = request.get_json()
    if not data:
        return jsonify(error(code=ResponseCode.PARAM_MISSING, msg='请求数据不能为空')), 400
    
    allowed_fields = [
        'title', 'description', 'craft_type', 'activity_type',
        'location', 'address', 'city', 'price', 'original_price',
        'max_participants', 'status', 'cover_image'
    ]
    
    for field in data:
        if field in allowed_fields:
            if field in ['price', 'original_price']:
                setattr(activity, field, float(data[field]))
            elif field in ['max_participants']:
                setattr(activity, field, int(data[field]))
            else:
                setattr(activity, field, data[field])
    
    if data.get('start_time'):
        activity.start_time = parse_datetime(data.get('start_time'))
    if data.get('end_time'):
        activity.end_time = parse_datetime(data.get('end_time'))
    if data.get('registration_start_time'):
        activity.registration_start_time = parse_datetime(data.get('registration_start_time'))
    if data.get('registration_deadline'):
        activity.registration_deadline = parse_datetime(data.get('registration_deadline'))
    
    images = data.get('images')
    if images and isinstance(images, list):
        activity.images = images
        if len(images) > 0 and not data.get('cover_image'):
            activity.cover_image = images[0]
    
    if data.get('tags'):
        activity.tags = data.get('tags')
    
    db.session.commit()
    
    return jsonify(success(data=activity.to_dict(), msg='活动更新成功'))


@activity_bp.route('/<int:activity_id>', methods=['DELETE'])
@login_required
def delete_activity(activity_id):
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    activity = Activity.query.filter_by(id=activity_id, teacher_id=teacher_profile.id).first()
    if not activity:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在或无权删除')), 404
    
    activity.status = 'inactive'
    db.session.commit()
    
    return jsonify(success(msg='活动已删除'))


@activity_bp.route('/<int:activity_id>/register', methods=['POST'])
@login_required
def register_activity(activity_id):
    user_id = g.get('user_id')
    
    activity = Activity.query.get(activity_id)
    if not activity or activity.status != 'active':
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='活动不存在或已结束')), 404
    
    if not activity.is_registration_open:
        return jsonify(error(code=ResponseCode.OPERATION_FAILED, msg='活动报名已截止或名额已满')), 400
    
    existing_registration = ActivityRegistration.query.filter_by(
        activity_id=activity_id,
        user_id=user_id
    ).first()
    
    if existing_registration:
        return jsonify(error(code=ResponseCode.DATA_EXISTS, msg='您已报名该活动')), 400
    
    data = request.get_json() or {}
    
    registration = ActivityRegistration(
        activity_id=activity_id,
        user_id=user_id,
        name=data.get('name'),
        phone=data.get('phone'),
        remark=data.get('remark'),
        status='confirmed'
    )
    
    db.session.add(registration)
    
    activity.current_participants = (activity.current_participants or 0) + 1
    activity.registration_count = (activity.registration_count or 0) + 1
    
    db.session.commit()
    
    return jsonify(success(data=registration.to_dict(), msg='报名成功'))


@activity_bp.route('/<int:activity_id>/register', methods=['DELETE'])
@login_required
def cancel_registration(activity_id):
    user_id = g.get('user_id')
    
    registration = ActivityRegistration.query.filter_by(
        activity_id=activity_id,
        user_id=user_id
    ).first()
    
    if not registration:
        return jsonify(error(code=ResponseCode.DATA_NOT_FOUND, msg='您未报名该活动')), 404
    
    activity = Activity.query.get(activity_id)
    if activity:
        activity.current_participants = max(0, (activity.current_participants or 0) - 1)
    
    db.session.delete(registration)
    db.session.commit()
    
    return jsonify(success(msg='已取消报名'))


@activity_bp.route('/my', methods=['GET'])
@login_required
def get_my_activities():
    teacher_profile = get_current_teacher_profile()
    if not teacher_profile:
        return jsonify(error(code=ResponseCode.PERMISSION_DENIED, msg='您不是手作老师身份')), 403
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    status = request.args.get('status', None, type=str)
    
    query = Activity.query.filter_by(teacher_id=teacher_profile.id)
    
    if status:
        query = query.filter(Activity.status == status)
    
    query = query.order_by(Activity.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    activities = [activity.to_dict() for activity in pagination.items]
    
    return jsonify(success(data={
        'list': activities,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next
    }))


@activity_bp.route('/my-registrations', methods=['GET'])
@login_required
def get_my_registrations():
    user_id = g.get('user_id')
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    
    query = ActivityRegistration.query.filter_by(
        user_id=user_id
    ).order_by(ActivityRegistration.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=size, error_out=False)
    
    registrations = []
    for reg in pagination.items:
        reg_dict = reg.to_dict()
        if reg.activity:
            reg_dict['activity'] = reg.activity.to_dict(include_teacher=True)
        registrations.append(reg_dict)
    
    return jsonify(success(data={
        'list': registrations,
        'total': pagination.total,
        'page': page,
        'size': size,
        'total_pages': pagination.pages,
        'has_next': pagination.has_next
    }))
