#!/usr/bin/env python3
"""
创建基础数据表的迁移脚本
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.config import Config


def migrate():
    app = create_app(Config)
    
    with app.app_context():
        from app.models import ActivityType, SystemConfig, Category, Specialty
        
        print("Creating activity_types table...")
        db.create_all()
        
        print("Initializing default data...")
        
        default_craft_types = ['编织', '陶艺', '刺绣', '皮具', '木艺', '纸艺', '花艺', '烘焙', '其他']
        for i, craft_type in enumerate(default_craft_types):
            existing = Category.query.filter_by(name=craft_type).first()
            if not existing:
                cat = Category(
                    name=craft_type,
                    icon='',
                    description=f'{craft_type}手工分类',
                    sort=i,
                    status='active'
                )
                db.session.add(cat)
        
        default_activity_types = [
            ('线下体验', '线下手工体验活动', 0),
            ('线上课程', '线上教学课程', 1),
            ('讲座', '知识分享讲座', 2),
            ('工作坊', '手工制作工作坊', 3),
            ('手工市集', '手工产品市集', 4),
            ('其他', '其他类型活动', 5)
        ]
        
        for name, desc, sort in default_activity_types:
            existing = ActivityType.query.filter_by(name=name).first()
            if not existing:
                at = ActivityType(
                    name=name,
                    description=desc,
                    sort=sort,
                    status='active'
                )
                db.session.add(at)
        
        if not Specialty.query.first():
            print("\nInitializing specialties...")
            specialties_data = [
                {'name': '棒针编织', 'icon': '🧶', 'category': '编织', 'sort_order': 1, 'is_active': True},
                {'name': '钩针编织', 'icon': '🧶', 'category': '编织', 'sort_order': 2, 'is_active': True},
                {'name': '编织', 'icon': '🧶', 'category': '编织', 'sort_order': 3, 'is_active': True},
                {'name': '陶艺', 'icon': '🏺', 'category': '陶艺', 'sort_order': 10, 'is_active': True},
                {'name': '拉坯', 'icon': '🏺', 'category': '陶艺', 'sort_order': 11, 'is_active': True},
                {'name': '釉上彩', 'icon': '🎨', 'category': '陶艺', 'sort_order': 12, 'is_active': True},
                {'name': '皮革工艺', 'icon': '👜', 'category': '皮革', 'sort_order': 20, 'is_active': True},
                {'name': '刺绣', 'icon': '🧵', 'category': '布艺', 'sort_order': 30, 'is_active': True},
                {'name': '纸艺', 'icon': '📄', 'category': '纸艺', 'sort_order': 40, 'is_active': True},
                {'name': '珠串', 'icon': '💎', 'category': '珠串', 'sort_order': 50, 'is_active': True},
                {'name': '木艺', 'icon': '🪵', 'category': '木艺', 'sort_order': 60, 'is_active': True},
                {'name': '布艺', 'icon': '🧵', 'category': '布艺', 'sort_order': 31, 'is_active': True},
                {'name': '手工皂', 'icon': '🧼', 'category': '手工', 'sort_order': 70, 'is_active': True},
                {'name': '蜡烛', 'icon': '🕯️', 'category': '手工', 'sort_order': 71, 'is_active': True},
                {'name': '押花', 'icon': '🌸', 'category': '手工', 'sort_order': 72, 'is_active': True},
                {'name': '热缩片', 'icon': '🔬', 'category': '手工', 'sort_order': 73, 'is_active': True},
                {'name': '滴胶', 'icon': '💧', 'category': '手工', 'sort_order': 74, 'is_active': True},
                {'name': '黏土', 'icon': '🟠', 'category': '手工', 'sort_order': 75, 'is_active': True}
            ]
            
            for data in specialties_data:
                existing = Specialty.query.filter_by(name=data['name']).first()
                if not existing:
                    specialty = Specialty(**data)
                    db.session.add(specialty)
            
            print(f"Initialized {len(specialties_data)} specialties")
        
        default_configs = [
            ('site_name', '手作爱好者平台', '网站名称', 'general'),
            ('site_description', '分享手工艺术，连接创作者与爱好者', '网站描述', 'general'),
            ('contact_phone', '400-123-4567', '联系电话', 'contact'),
            ('contact_email', 'contact@handmade.com', '联系邮箱', 'contact'),
            ('miniprogram_appid', '', '小程序AppID', 'miniprogram'),
            ('order_auto_cancel_hours', '24', '订单自动取消时间(小时)', 'order'),
            ('review_auto_complete_days', '7', '评价自动完成时间(天)', 'order'),
        ]
        
        for key, value, desc, group in default_configs:
            existing = SystemConfig.query.filter_by(key=key).first()
            if not existing:
                config = SystemConfig(
                    key=key,
                    value=value,
                    description=desc,
                    group=group
                )
                db.session.add(config)
        
        db.session.commit()
        print("Migration completed successfully!")


if __name__ == '__main__':
    migrate()
