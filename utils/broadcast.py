import time

from flask import url_for


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
        
        # 1. 写入公告表
        sql = "INSERT INTO announcement(topic, content, time_str) VALUES (%s, %s, %s)"
        ann_id = query_module.insert(sql, (topic, contents, time_str))  # 返回公告ID

        # 2. 写入可见性表
        vis_sql = """
            INSERT INTO announcement_visibility(announcement_id, target_type, target_id)
            VALUES (%s, %s, %s)
        """
        
        for s in selected_students:
            query_module.insert(vis_sql, (ann_id, 'student', s))
            
        for c in selected_colleges:
            query_module.insert(vis_sql, (ann_id, 'college', c))
            
        for m in selected_majors:
            query_module.insert(vis_sql, (ann_id, 'major', m))
            
        return {'status': 'redirect', 'url':url_for('manager'), 'message': '公告发布成功'}
    
    
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
