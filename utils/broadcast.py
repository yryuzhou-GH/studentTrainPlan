import time
import pymysql
from flask import url_for
from config import config


def _check_and_create_tables(query_module):
    """
    检查并创建公告相关表（如果不存在）
    """
    try:
        # 检查表是否存在
        check_sql = "SHOW TABLES LIKE 'announcement'"
        result = query_module.query(check_sql)
        
        if not result:
            # 表不存在，创建表
            print("[公告系统] 检测到表不存在，正在自动创建...")
            
            # 创建公告表
            create_announcement_sql = """
            CREATE TABLE IF NOT EXISTS announcement (
                id INT AUTO_INCREMENT PRIMARY KEY,
                topic VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                time_str DATETIME NOT NULL
            )ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            query_module.update(create_announcement_sql)
            
            # 创建公告可见性表
            create_visibility_sql = """
            CREATE TABLE IF NOT EXISTS announcement_visibility (
                id INT AUTO_INCREMENT PRIMARY KEY,
                announcement_id INT NOT NULL,
                target_type ENUM('student', 'college', 'major') NOT NULL,
                target_id VARCHAR(255) NOT NULL,
                FOREIGN KEY (announcement_id) REFERENCES announcement(id)
                    ON DELETE CASCADE
            )ENGINE=INNODB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            query_module.update(create_visibility_sql)
            
            print("[公告系统] 表创建成功！")
            return True
        return True
    except Exception as e:
        print(f"[公告系统] 检查表时出错: {str(e)}")
        return False


def handle_broadcast_request(request, session, query_module):
    """
    处理管理员广播请求
    
    Args:
        request: Flask请求对象
        session: Flask会话对象
        query_module: 数据库查询模块
        
    Returns:
        dict: 包含处理结果的信息
    """
    stu_id = session.get('stu_id')
    if stu_id != 'admin':
        return {'status': 'error', 'message': '权限不足'}
    
    # 检查并创建表（如果不存在）
    _check_and_create_tables(query_module)
    
    if request.method == 'GET':
        students = query_module.query("SELECT STU_NO, NAME FROM STUDENT WHERE STU_NO != 'admin'")
        colleges=query_module.query("SELECT DISTINCT COLLEGE FROM STUDENT")
        majors=query_module.query("SELECT DISTINCT MAJOR FROM STUDENT")
        
        return {'status': 'success', 'template': 'managerBroadcast.html', 'students': students,'colleges':colleges,'majors':majors}
    elif request.method == 'POST':
        # 获取数据
        topic = request.form.get('topic')
        contents = request.form.get('contents')
        selected_students = request.form.getlist('students')
        selected_colleges=request.form.getlist('colleges')
        selected_majors=request.form.getlist('majors')
        
        # 获取时间
        now = time.time()
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        
        # 验证必填字段
        if not topic or not contents:
            return {'status': 'error', 'message': '标题和内容不能为空'}
        
        try:
            # 1. 写入公告表
            sql = "INSERT INTO announcement(topic, content, time_str) VALUES (%s, %s, %s)"
            ann_id = query_module.insert(sql, (topic, contents, time_str))  # 返回公告ID

            # 2. 写入可见性表
            vis_sql = """
                INSERT INTO announcement_visibility(announcement_id, target_type, target_id)
                VALUES (%s, %s, %s)
            """
            
            # 如果没有选择任何目标，则对所有学生可见（可选：可以添加一个"全部"选项）
            if not selected_students and not selected_colleges and not selected_majors:
                # 如果没有选择任何目标，可以选择不插入可见性记录，或者插入一个特殊的"all"记录
                # 这里我们选择对所有学生可见（通过不设置可见性限制）
                # 但为了兼容现有查询逻辑，我们添加一个特殊的可见性记录
                query_module.insert(vis_sql, (ann_id, 'college', 'ALL'))
            else:
                for s in selected_students:
                    if s:  # 确保不为空
                        query_module.insert(vis_sql, (ann_id, 'student', s))
                        
                for c in selected_colleges:
                    if c:  # 确保不为空
                        query_module.insert(vis_sql, (ann_id, 'college', c))
                        
                for m in selected_majors:
                    if m:  # 确保不为空
                        query_module.insert(vis_sql, (ann_id, 'major', m))
            
            return {'status': 'redirect', 'url':url_for('manager'), 'message': '公告发布成功'}
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"发布公告失败: {str(e)}"
            # 检查是否是表不存在错误
            if "doesn't exist" in str(e) or "Table" in str(e):
                error_msg = "数据库表不存在，请运行 init_announcement_tables.py 初始化表"
            return {'status': 'error', 'message': error_msg}
    
    
#251201，新增消息中心功能
def handle_inbox_request(request,session,query_module):
    """
    处理消息中心请求
    输入：
    request: Flask请求对象
    session: Flask会话对象
    query_module: 数据库查询模块
    
    返回：
    dict: 包含处理结果的信息
    """
    stu_id=session.get('stu_id')
    
    if not stu_id:
        return {'status': 'error', 'message': '无效用户'}
    
    sql="""
        SELECT a.id, a.topic, a.content, a.time_str
        FROM announcement a
        JOIN announcement_visibility av ON a.id = av.announcement_id
        WHERE 
            (av.target_type = 'student' AND av.target_id = %s) OR
            (av.target_type = 'college' AND av.target_id IN (
                SELECT COLLEGE FROM STUDENT WHERE STU_NO = %s
            )) OR
            (av.target_type = 'major' AND av.target_id IN (
                SELECT MAJOR FROM STUDENT WHERE STU_NO = %s
            ))
        ORDER BY a.time_str DESC
    """%(stu_id,stu_id,stu_id)
    
    messages=query_module.query(sql)
    
    formatted_messages=[]
    for msg in messages:
        formatted_messages.append({
            'id':msg[0],
            'topic':msg[1],
            'content':msg[2],
            'time_str':msg[3],
        })
        
    return {'status':'success','template':'inbox.html','messages':formatted_messages}
