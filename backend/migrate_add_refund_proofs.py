import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from sqlalchemy import text

app = create_app()

def migrate_refund_fields():
    with app.app_context():
        print("="*60)
        print("数据库迁移 - 添加退款相关字段")
        print("="*60)
        
        print("\n【1/3】检查 orders 表结构...")
        print("-"*40)
        
        result = db.session.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]
        print(f"当前列: {columns}")
        
        print("\n【2/3】添加退款相关字段...")
        print("-"*40)
        
        columns_to_add = [
            ('refund_proofs TEXT', 'refund_proofs'),
        ]
        
        added_count = 0
        for column_def, column_name in columns_to_add:
            if column_name not in columns:
                try:
                    db.session.execute(text(f"ALTER TABLE orders ADD COLUMN {column_def}"))
                    db.session.commit()
                    print(f"  ✓ 已添加列: orders.{column_name}")
                    added_count += 1
                except Exception as e:
                    print(f"  ✗ 添加列失败: orders.{column_name} - {e}")
                    db.session.rollback()
            else:
                print(f"  - 列已存在: orders.{column_name}")
        
        print(f"\n【3/3】验证字段...")
        print("-"*40)
        
        result = db.session.execute(text("PRAGMA table_info(orders)"))
        columns = [row[1] for row in result]
        
        all_exist = True
        for _, column_name in columns_to_add:
            if column_name in columns:
                print(f"  ✓ {column_name}: 已存在")
            else:
                print(f"  ✗ {column_name}: 缺失")
                all_exist = False
        
        if all_exist and added_count > 0:
            print(f"\n✓ 成功添加了 {added_count} 个新字段")
        elif all_exist:
            print("\n✓ 所有字段已存在，无需更新")
        else:
            print("\n✗ 部分字段添加失败")
        
        print("\n" + "="*60)
        print("数据库迁移完成！")
        print("="*60)

if __name__ == '__main__':
    migrate_refund_fields()
