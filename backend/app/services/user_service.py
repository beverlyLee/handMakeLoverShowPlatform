from datetime import datetime
from app.database import db
from app.models import User, Address, TeacherProfile

class UserService:
    
    @staticmethod
    def get_user_by_id(user_id):
        user = User.query.get(user_id)
        if user:
            return user.to_dict()
        return None
    
    @staticmethod
    def get_user_by_openid(openid):
        user = User.query.filter_by(openid=openid).first()
        if user:
            return user.to_dict()
        return None
    
    @staticmethod
    def create_user(openid, session_key, nickname=None, avatar=None, unionid=None):
        user = User(
            openid=openid,
            unionid=unionid,
            session_key=session_key,
            username=f'wx_{openid[-8:]}' if len(openid) >= 8 else f'wx_{openid}',
            nickname=nickname or '微信用户',
            avatar=avatar or 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=default%20user%20avatar&image_size=square',
            roles=['customer'],
            current_role='customer'
        )
        
        db.session.add(user)
        db.session.commit()
        
        return user.to_dict()
    
    @staticmethod
    def update_user(user_id, **kwargs):
        user = User.query.get(user_id)
        if not user:
            return None
        
        allowed_fields = ['nickname', 'avatar', 'phone', 'email', 'gender', 'bio', 'session_key', 'current_role']
        for field in kwargs:
            if field in allowed_fields:
                setattr(user, field, kwargs[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return user.to_dict()
    
    @staticmethod
    def add_role(user_id, role):
        user = User.query.get(user_id)
        if not user:
            return None
        
        roles = user.roles
        if role not in roles:
            roles.append(role)
            user.roles = roles
            db.session.commit()
        
        return user.to_dict()
    
    @staticmethod
    def switch_role(user_id, target_role):
        user = User.query.get(user_id)
        if not user:
            return None, '用户不存在'
        
        if target_role not in ['customer', 'teacher']:
            return None, '无效的角色类型'
        
        if target_role not in user.roles:
            return None, f'您没有 {target_role} 身份'
        
        original_role = user.current_role
        
        if original_role != target_role:
            user.current_role = target_role
            user.updated_at = datetime.utcnow()
            db.session.commit()
        
        return user.to_dict(), None, original_role
    
    @staticmethod
    def get_user_public_info(user_dict):
        if not user_dict:
            return None
        
        public_info = {
            'id': user_dict.get('id'),
            'username': user_dict.get('username'),
            'nickname': user_dict.get('nickname'),
            'avatar': user_dict.get('avatar'),
            'phone': user_dict.get('phone'),
            'email': user_dict.get('email'),
            'gender': user_dict.get('gender'),
            'role': user_dict.get('current_role'),
            'roles': user_dict.get('roles'),
            'current_role': user_dict.get('current_role'),
            'bio': user_dict.get('bio'),
            'teacher_info': user_dict.get('teacher_info'),
            'create_time': user_dict.get('create_time')
        }
        
        return public_info
    
    @staticmethod
    def get_addresses_by_user(user_id):
        addresses = Address.query.filter_by(user_id=user_id).order_by(Address.is_default.desc(), Address.created_at.desc()).all()
        return [addr.to_dict() for addr in addresses]
    
    @staticmethod
    def get_address_by_id(address_id, user_id=None):
        query = Address.query.filter_by(id=address_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        address = query.first()
        if address:
            return address.to_dict()
        return None
    
    @staticmethod
    def create_address(user_id, data):
        is_default = data.get('is_default', False)
        
        if is_default:
            Address.query.filter_by(user_id=user_id, is_default=True).update({'is_default': False})
        
        address = Address(
            user_id=user_id,
            name=data.get('name'),
            phone=data.get('phone'),
            province=data.get('province'),
            city=data.get('city'),
            district=data.get('district'),
            detail=data.get('detail'),
            is_default=is_default
        )
        
        db.session.add(address)
        db.session.commit()
        
        return address.to_dict()
    
    @staticmethod
    def update_address(address_id, user_id, data):
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not address:
            return None
        
        is_default = data.get('is_default', False)
        
        if is_default and not address.is_default:
            Address.query.filter(
                Address.user_id == user_id,
                Address.id != address_id,
                Address.is_default == True
            ).update({'is_default': False})
        
        allowed_fields = ['name', 'phone', 'province', 'city', 'district', 'detail', 'is_default']
        for field in data:
            if field in allowed_fields:
                setattr(address, field, data[field])
        
        address.updated_at = datetime.utcnow()
        db.session.commit()
        
        return address.to_dict()
    
    @staticmethod
    def delete_address(address_id, user_id):
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not address:
            return False
        
        db.session.delete(address)
        db.session.commit()
        
        return True
    
    @staticmethod
    def set_default_address(address_id, user_id):
        address = Address.query.filter_by(id=address_id, user_id=user_id).first()
        if not address:
            return False
        
        Address.query.filter(
            Address.user_id == user_id,
            Address.id != address_id
        ).update({'is_default': False})
        
        address.is_default = True
        address.updated_at = datetime.utcnow()
        db.session.commit()
        
        return True
    
    @staticmethod
    def get_teacher_profile(user_id):
        profile = TeacherProfile.query.filter_by(user_id=user_id).first()
        if profile:
            return profile.to_dict()
        return None
    
    @staticmethod
    def create_teacher_profile(user_id, data):
        teacher_id = f'T{datetime.now().strftime("%Y%m%d%H%M%S")}'
        
        profile = TeacherProfile(
            user_id=user_id,
            teacher_id=teacher_id,
            real_name=data.get('real_name'),
            id_card=data.get('id_card'),
            phone=data.get('phone'),
            intro=data.get('intro', ''),
            experience_years=data.get('experience_years', 0)
        )
        
        if data.get('specialties'):
            profile.specialties = data.get('specialties')
        
        if data.get('work_photos'):
            profile.work_photos = data.get('work_photos')
        
        db.session.add(profile)
        
        user = User.query.get(user_id)
        if user and 'teacher' not in user.roles:
            roles = user.roles
            roles.append('teacher')
            user.roles = roles
        
        db.session.commit()
        
        return profile.to_dict()
    
    @staticmethod
    def verify_teacher_identity(user_id, data):
        return UserService.create_teacher_profile(user_id, data)
    
    @staticmethod
    def update_teacher_profile(user_id, data):
        profile = TeacherProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return None
        
        allowed_fields = [
            'real_name', 'id_card', 'phone', 'intro', 'bio',
            'experience_years', 'student_count',
            'studio_name', 'studio_address'
        ]
        
        for field in data:
            if field in allowed_fields:
                setattr(profile, field, data[field])
        
        if data.get('specialties'):
            profile.specialties = data['specialties']
        if data.get('studio_images'):
            profile.studio_images = data['studio_images']
        if data.get('work_photos'):
            profile.work_photos = data['work_photos']
        if data.get('certifications'):
            profile.certifications = data['certifications']
        
        profile.updated_at = datetime.utcnow()
        db.session.commit()
        
        return profile.to_dict()
