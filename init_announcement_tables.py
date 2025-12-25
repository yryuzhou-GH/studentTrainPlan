#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化公告表脚本
用于创建 announcement 和 announcement_visibility 表
"""

import pymysql
from config import config

def init_announcement_tables():
    """初始化公告相关表"""
    try:
        # 连接数据库
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password=config['MYSQL_PASSWORD'],
            database=config['DATABASE_NAME'],
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        print("开始创建公告表...")
        
        # 删除已存在的表（如果存在）
        cursor.execute("DROP TABLE IF EXISTS announcement_visibility")
        cursor.execute("DROP TABLE IF EXISTS announcement")
        print("已删除旧表（如果存在）")
        
        # 创建公告表
        create_announcement_sql = """
        CREATE TABLE announcement (
            id INT AUTO_INCREMENT PRIMARY KEY,
            topic VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            time_str DATETIME NOT NULL
        )ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_announcement_sql)
        print("✓ 创建 announcement 表成功")
        
        # 创建公告可见性表
        create_visibility_sql = """
        CREATE TABLE announcement_visibility (
            id INT AUTO_INCREMENT PRIMARY KEY,
            announcement_id INT NOT NULL,
            target_type ENUM('student', 'college', 'major') NOT NULL,
            target_id VARCHAR(255) NOT NULL,
            FOREIGN KEY (announcement_id) REFERENCES announcement(id)
                ON DELETE CASCADE
        )ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_visibility_sql)
        print("✓ 创建 announcement_visibility 表成功")
        
        conn.commit()
        print("\n✅ 所有表创建成功！")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("公告表初始化脚本")
    print("=" * 50)
    print(f"数据库: {config['DATABASE_NAME']}")
    print(f"用户: root")
    print("=" * 50)
    
    success = init_announcement_tables()
    
    if success:
        print("\n🎉 初始化完成！现在可以使用管理员发布公告功能了。")
    else:
        print("\n⚠️  初始化失败，请检查错误信息并重试。")
    
    exit(0 if success else 1)

