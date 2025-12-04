"""
选课功能模块
提供专业选修课程的选课功能
"""

from utils.query import query, update


def get_available_elective_courses(stu_no):
    """
    获取学生可选的专业选修课程列表（未选过的课程）
    
    参数:
        stu_no: str, 学生编号
    
    返回:
        list: 可选课程列表，每个元素为 (CO_NO, CO_NAME, CLASSIFICATION, CREDITS, TEACHER, ...)
    """
    # 查询所有专业选修课程（包括各种子类型）
    sql = """
        SELECT CO_NO, CO_NAME, CLASSIFICATION, CREDITS, TEACHER, TOTAL_HR, 
               START_TIME, END_TIME, CLASS_TIME, MAX_STUDENTS, COLLEGE
        FROM EDUCATION_PLAN
        WHERE CLASSIFICATION LIKE '专业选修%' 
           OR CLASSIFICATION = '专业选修'
        ORDER BY CO_NO
    """
    all_elective_courses = query(sql)
    
    # 查询学生已选的课程
    sql_chosen = f"SELECT CO_NO FROM CHOOSE WHERE STU_NO = '{stu_no}'"
    chosen_courses = query(sql_chosen)
    chosen_course_nos = {row[0] for row in chosen_courses} if chosen_courses else set()
    
    # 筛选出未选的课程
    available_courses = []
    for course in all_elective_courses:
        co_no = course[0]
        if co_no not in chosen_course_nos:
            available_courses.append(course)
    
    return available_courses


def get_student_chosen_courses(stu_no):
    """
    获取学生已选的专业选修课程列表
    
    参数:
        stu_no: str, 学生编号
    
    返回:
        list: 已选课程列表，每个元素为 (CO_NO, CO_NAME, GRADE, COMMENT, ...)
    """
    sql = f"""
        SELECT c.CO_NO, e.CO_NAME, e.CLASSIFICATION, c.GRADE, c.COMMENT,
               e.CREDITS, e.TEACHER, e.COLLEGE
        FROM CHOOSE c
        JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
        WHERE c.STU_NO = '{stu_no}'
          AND (e.CLASSIFICATION LIKE '专业选修%' OR e.CLASSIFICATION = '专业选修')
        ORDER BY c.CO_NO
    """
    return query(sql)


def select_course(stu_no, co_no, ad_year='2016', major='计算机科学与技术'):
    """
    学生选课功能
    
    参数:
        stu_no: str, 学生编号
        co_no: str, 课程编号
        ad_year: str, 入学年份，默认'2016'
        major: str, 专业，默认'计算机科学与技术'
    
    返回:
        tuple: (success: bool, message: str)
    """
    # 检查课程是否存在
    sql_check = f"SELECT CO_NO, CO_NAME, MAX_STUDENTS FROM EDUCATION_PLAN WHERE CO_NO = '{co_no}'"
    course_info = query(sql_check)
    
    if not course_info:
        return False, "课程不存在"
    
    course_name = course_info[0][1]
    max_students = course_info[0][2]
    
    # 检查是否已经选过该课程
    sql_check_chosen = f"""
        SELECT CO_NO 
        FROM CHOOSE 
        WHERE STU_NO = '{stu_no}' AND CO_NO = '{co_no}'
    """
    already_chosen = query(sql_check_chosen)
    
    if already_chosen:
        return False, f"您已经选过课程《{course_name}》了"
    
    # 检查课程容量（如果设置了最大学生数）
    if max_students and max_students > 0:
        sql_count = f"""
            SELECT COUNT(*) 
            FROM CHOOSE 
            WHERE CO_NO = '{co_no}'
        """
        current_count = query(sql_count)
        if current_count and current_count[0][0] >= max_students:
            return False, f"课程《{course_name}》已满员（{max_students}人）"
    
    # 插入选课记录（初始成绩和评价为空）
    sql_insert = f"""
        INSERT INTO CHOOSE (AD_YEAR, MAJOR, STU_NO, CO_NO, GRADE, COMMENT)
        VALUES ('{ad_year}', '{major}', '{stu_no}', '{co_no}', NULL, NULL)
    """
    
    try:
        # 使用 update 方法插入选课记录
        update(sql_insert)
        return True, f"成功选择课程《{course_name}》"
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()  # 打印详细错误信息到控制台
        return False, f"选课失败：{error_msg}"


def drop_course(stu_no, co_no):
    """
    学生退课功能
    
    参数:
        stu_no: str, 学生编号
        co_no: str, 课程编号
    
    返回:
        tuple: (success: bool, message: str)
    """
    # 检查是否选过该课程
    sql_check = f"""
        SELECT CO_NO 
        FROM CHOOSE 
        WHERE STU_NO = '{stu_no}' AND CO_NO = '{co_no}'
    """
    chosen = query(sql_check)
    
    if not chosen:
        return False, "您未选择该课程"
    
    # 获取课程名称
    sql_course = f"SELECT CO_NAME FROM EDUCATION_PLAN WHERE CO_NO = '{co_no}'"
    course_info = query(sql_course)
    course_name = course_info[0][0] if course_info else "未知课程"
    
    # 删除选课记录
    sql_delete = f"""
        DELETE FROM CHOOSE 
        WHERE STU_NO = '{stu_no}' AND CO_NO = '{co_no}'
    """
    
    try:
        # 使用 update 方法删除选课记录
        update(sql_delete)
        return True, f"成功退选课程《{course_name}》"
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()  # 打印详细错误信息到控制台
        return False, f"退课失败：{error_msg}"


def get_course_statistics():
    """
    获取课程统计信息（每门专业选修课程的选课人数）
    
    返回:
        list: 课程统计列表，每个元素为 (CO_NO, CO_NAME, STUDENT_COUNT)
    """
    sql = """
        SELECT e.CO_NO, e.CO_NAME, COUNT(c.STU_NO) as STUDENT_COUNT
        FROM EDUCATION_PLAN e
        LEFT JOIN CHOOSE c ON e.CO_NO = c.CO_NO
        WHERE e.CLASSIFICATION LIKE '专业选修%' 
           OR e.CLASSIFICATION = '专业选修'
        GROUP BY e.CO_NO, e.CO_NAME
        ORDER BY STUDENT_COUNT DESC, e.CO_NO
    """
    return query(sql)

