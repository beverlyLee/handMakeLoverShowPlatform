import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from app.utils.response import success, error
from app.common.auth import login_required

upload_bp = Blueprint('upload', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_upload_folder():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    upload_folder = os.path.join(project_root, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder

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
        upload_folder = get_upload_folder()
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:8]
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        new_filename = f'{timestamp}_{random_str}.{file_ext}'
        
        date_folder = datetime.now().strftime('%Y-%m')
        date_folder_path = os.path.join(upload_folder, date_folder)
        if not os.path.exists(date_folder_path):
            os.makedirs(date_folder_path)
        
        file_path = os.path.join(date_folder_path, new_filename)
        file.save(file_path)
        
        file_url = f'/uploads/{date_folder}/{new_filename}'
        
        return jsonify(success(data={
            'url': file_url,
            'filename': new_filename,
            'original_filename': file.filename
        }, msg='上传成功'))
        
    except Exception as e:
        current_app.logger.error(f'文件上传失败: {str(e)}')
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
    upload_folder = get_upload_folder()
    date_folder = datetime.now().strftime('%Y-%m')
    date_folder_path = os.path.join(upload_folder, date_folder)
    if not os.path.exists(date_folder_path):
        os.makedirs(date_folder_path)
    
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
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            random_str = uuid.uuid4().hex[:8]
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            new_filename = f'{timestamp}_{random_str}.{file_ext}'
            
            file_path = os.path.join(date_folder_path, new_filename)
            file.save(file_path)
            
            file_url = f'/uploads/{date_folder}/{new_filename}'
            
            upload_results.append({
                'filename': file.filename,
                'success': True,
                'url': file_url,
                'new_filename': new_filename
            })
        except Exception as e:
            current_app.logger.error(f'文件上传失败: {str(e)}')
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

@upload_bp.route('/<path:filename>')
def serve_image(filename):
    upload_folder = get_upload_folder()
    try:
        return send_from_directory(upload_folder, filename)
    except Exception as e:
        current_app.logger.error(f'文件读取失败: {str(e)}')
        return jsonify(error(msg='文件不存在')), 404
