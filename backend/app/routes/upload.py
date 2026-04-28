import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, send_from_directory, current_app
from werkzeug.utils import secure_filename
from io import BytesIO
from app.utils.response import success, error
from app.common.auth import login_required
from app.models import Image
from app.database import db
from flask import g

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

CONTENT_TYPES = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp'
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_content_type(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpeg'
    return CONTENT_TYPES.get(ext, 'image/jpeg')

def save_image_to_db(file, original_filename, user_id=None):
    file_data = file.read()
    file_size = len(file_data)
    
    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = uuid.uuid4().hex[:8]
    new_filename = f'{timestamp}_{random_str}.{file_ext}'
    
    image_uuid = str(uuid.uuid4())
    
    image = Image(
        uuid=image_uuid,
        filename=new_filename,
        original_filename=original_filename,
        content_type=get_content_type(original_filename),
        data=file_data,
        size=file_size,
        user_id=user_id,
        is_public=True
    )
    
    db.session.add(image)
    db.session.commit()
    
    return image

@upload_bp.route('/image', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify(error(msg='没有找到文件')), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify(error(msg='没有选择文件')), 400
    
    if not allowed_file(file.filename):
        return jsonify(error(msg=f'不支持的文件类型，支持的类型: {", ".join(ALLOWED_EXTENSIONS)}')), 400
    
    try:
        user_id = g.get('user_id')
        
        image = save_image_to_db(file, file.filename, user_id)
        
        return jsonify(success(data={
            'url': f'/api/images/{image.uuid}',
            'filename': image.filename,
            'original_filename': image.original_filename,
            'uuid': image.uuid
        }, msg='上传成功'))
        
    except Exception as e:
        current_app.logger.error(f'文件上传失败: {str(e)}')
        db.session.rollback()
        return jsonify(error(msg=f'上传失败: {str(e)}')), 500

@upload_bp.route('/images', methods=['POST'])
@login_required
def upload_images():
    if 'files' not in request.files:
        return jsonify(error(msg='没有找到文件')), 400
    
    files = request.files.getlist('files')
    
    if not files:
        return jsonify(error(msg='没有选择文件')), 400
    
    upload_results = []
    user_id = g.get('user_id')
    
    for file in files:
        if file.filename == '':
            continue
        
        if not allowed_file(file.filename):
            upload_results.append({
                'filename': file.filename,
                'success': False,
                'error': '不支持的文件类型'
            })
            continue
        
        try:
            image = save_image_to_db(file, file.filename, user_id)
            
            upload_results.append({
                'filename': file.filename,
                'success': True,
                'url': f'/api/images/{image.uuid}',
                'new_filename': image.filename,
                'uuid': image.uuid
            })
        except Exception as e:
            current_app.logger.error(f'文件上传失败: {str(e)}')
            db.session.rollback()
            upload_results.append({
                'filename': file.filename,
                'success': False,
                'error': str(e)
            })
    
    success_count = sum(1 for r in upload_results if r['success'])
    error_count = len(upload_results) - success_count
    
    return jsonify(success(data={
        'total': len(upload_results),
        'success': success_count,
        'error': error_count,
        'results': upload_results
    }, msg=f'上传完成，成功 {success_count} 个，失败 {error_count} 个'))

@upload_bp.route('/<image_uuid>', methods=['GET'])
def get_image_by_uuid_route(image_uuid):
    return get_image(image_uuid)

def get_upload_folder():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    upload_folder = os.path.join(project_root, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

@upload_bp.route('/<path:filename>')
def serve_image(filename):
    if '-' in filename and len(filename) >= 36:
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, filename):
            return get_image(filename)
    
    upload_folder = get_upload_folder()
    try:
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        current_app.logger.error(f'文件读取失败: {str(e)}')
        return jsonify(error(msg='文件不存在')), 404

image_bp = Blueprint('images', __name__)

@image_bp.route('/<image_uuid>', methods=['GET'])
def get_image(image_uuid):
    try:
        image = Image.query.filter_by(uuid=image_uuid).first()
        
        if not image:
            current_app.logger.warning(f'图片不存在: {image_uuid}')
            return jsonify(error(msg='图片不存在')), 404
        
        if_none_match = request.headers.get('If-None-Match')
        if_modified_since = request.headers.get('If-Modified-Since')
        
        etag = f'"{image.uuid}"'
        
        if if_none_match == etag:
            current_app.logger.info(f'图片未修改，返回 304: {image_uuid}')
            return '', 304
        
        if if_modified_since and image.updated_at:
            try:
                if_modified_time = datetime.strptime(if_modified_since, '%a, %d %b %Y %H:%M:%S GMT')
                if image.updated_at <= if_modified_time:
                    current_app.logger.info(f'图片未修改，返回 304: {image_uuid}')
                    return '', 304
            except Exception as e:
                current_app.logger.warning(f'解析 If-Modified-Since 失败: {e}')
        
        current_app.logger.info(f'读取图片: {image_uuid}, 大小: {image.size}, 类型: {image.content_type}')
        
        if not image.data:
            current_app.logger.error(f'图片数据为空: {image_uuid}')
            return jsonify(error(msg='图片数据为空')), 500
        
        try:
            image_bytes = bytes(image.data) if not isinstance(image.data, bytes) else image.data
            image_data = BytesIO(image_bytes)
            image_data.seek(0)
        except Exception as e:
            current_app.logger.error(f'处理图片数据失败: {image_uuid}, 错误: {str(e)}')
            return jsonify(error(msg='图片数据处理失败')), 500
        
        try:
            response = send_file(
                image_data,
                mimetype=image.content_type,
                as_attachment=False,
                download_name=image.filename
            )
        except TypeError:
            response = send_file(
                image_data,
                mimetype=image.content_type,
                as_attachment=False,
                attachment_filename=image.filename
            )
        
        response.headers['Cache-Control'] = 'public, max-age=604800'
        response.headers['ETag'] = etag
        if image.updated_at:
            response.headers['Last-Modified'] = image.updated_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        return response
        
    except Exception as e:
        current_app.logger.error(f'图片读取失败: {image_uuid}, 错误: {str(e)}')
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify(error(msg='图片读取失败')), 500
