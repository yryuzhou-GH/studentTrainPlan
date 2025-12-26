from flask import Flask, render_template, request, flash,  jsonify, redirect, url_for, session
from utils import query, map_student_course, recommed_module, broadcast
from utils.dynamic_recommend import DynamicCourseRecommender, to_bar_json, regular_data
from utils.course_selection import (
    get_available_elective_courses, 
    get_student_chosen_courses,
    select_course,
    drop_course,
    get_course_statistics
)
import json
import time
from datetime import datetime, date
import os
from openai import OpenAI

# 创建flask对象
app = Flask(__name__)
app.config['SECRET_KEY'] = 'gsolvit'


@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/manager', methods=['GET', 'POST'])
def manager():
    sql = "select * from STUDENT"
    result = query.query(sql)
    return render_template('manager.html', result=result)


@app.route('/managerAdd', methods=['GET', 'POST'])
def managerAdd():
    stu_id = session.get('stu_id')
    #print(stu_id)
    if stu_id == 'admin':
        if request.method == 'GET':
            #print('1111')
            return  render_template('managerAdd.html')
        else:
            #print('222')
            name = request.form.get('name')
            sex = request.form.get('sex')
            stu_no = request.form.get('stu_no')
            college = request.form.get('college')
            major = request.form.get('major')
            ad_year = request.form.get('ad_year')
            password = request.form.get('password')
            sql="INSERT INTO STUDENT VALUES ('%s','%s','%s','%s','%s','%s','%s','%s')" % (name,sex,stu_no,college,major,ad_year,password,stu_no)
            #print(sql)
            query.update(sql)
            return redirect(url_for('manager'))
    else:
        return u'页面不存在'


@app.route('/managerDelete', methods=['GET', 'POST'])
def managerDelete():
    stu_id = session.get('stu_id')
    #print(stu_id)
    if stu_id == 'admin':
        if request.method == 'GET':
            #print('1111')
            return render_template('managerDelete.html')
        else:
            #print('222')
            stu_no = request.form.get('stu_no')
            sql="DELETE FROM STUDENT WHERE STU_NO='%s'" % stu_no
            #print(sql)
            query.update(sql)
            return redirect(url_for('manager'))
    else:
        return u'页面不存在'


@app.route('/managerEdit', methods=['GET', 'POST'])
def managerEdit():
    stu_id = session.get('stu_id')
    if stu_id == 'admin':
        if request.method == 'GET':
            return render_template('managerEdit.html')
        else:
            stu_no = request.form.get('stu_no')
            name = request.form.get('name')
            sex = request.form.get('sex')
            college = request.form.get('college')
            major = request.form.get('major')
            ad_year = request.form.get('ad_year')
            password = request.form.get('password')

            sql="select * from STUDENT WHERE STU_NO='%s'" % stu_no
            result=query.query(sql)
            if name=='':
                name=result[0][0]
            if sex=='':
                sex=result[0][1]
            if college=='':
                college=result[0][3]
            if major=='':
                major=result[0][4]
            if ad_year=='':
                ad_year=result[0][5]

            sql="UPDATE STUDENT SET NAME='%s',SEX='%s',COLLEGE='%s',MAJOR='%s',AD_YEAR='%s',PASSWORD='%s',ID='%s' WHERE STU_NO='%s'" % (name, sex, college, major, ad_year, password, stu_no, stu_no)
            #print(sql)
            query.update(sql)
            return redirect(url_for('manager'))
    else:
        return u'页面不存在'


@app.route('/course_discussion', methods=['GET', 'POST'])
def course_discussion():
    if request.method == 'GET':
        return render_template('course_discussion.html')
    else:
        # 支持AJAX和表单提交
        if request.is_json:
            data = request.get_json()
            topic = data.get('topic')
            comments = data.get('comments')
        else:
            topic = request.form.get('topic')
            comments = request.form.get('comments')
        
        # 验证
        if not topic or not comments:
            if request.is_json:
                return jsonify({"success": False, "message": "话题标题和内容不能为空"}), 400
            return "话题标题和内容不能为空"
        
        stu_id = session.get('stu_id')
        if not stu_id:
            if request.is_json:
                return jsonify({"success": False, "message": "用户未登录"}), 401
            return redirect(url_for('login'))
        
        sql = "select NAME from STUDENT where STU_NO = %s"
        stu_name = query.query(sql, (stu_id,))
        if not stu_name:
            if request.is_json:
                return jsonify({"success": False, "message": "用户信息不存在"}), 404
            return "用户信息不存在"
        
        stu_name = stu_name[0][0]
        now = time.time()
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        news_id = stu_name + str(int(now.replace('-', '').replace(' ', '').replace(':', '')))
        
        sql = "INSERT INTO NEWS(TOPIC, COMMENTS, COMMENTER, NEWS_ID, IS_FIRST, CREATE_TIME) VALUES (%s, %s, %s, %s, '0', %s)"
        #print(sql)
        query.update(sql, (topic, comments, stu_name, news_id, now))
        
        if request.is_json:
            return jsonify({"success": True, "message": "话题发布成功", "news_id": news_id})
        return redirect(url_for('news_center'))


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    else:
        stu_id = request.form.get('stu_id')
        password = request.form.get('password')
        sql = "select * from STUDENT where STU_NO = '%s'" % stu_id
        result = query.query(sql)
        print(result)
        if len(result) != 0:
            #print(result[0][6], password)
            if result[0][6] == password:
                session['stu_id'] = result[0][2]
                session.permanent=True
                if stu_id=='admin':
                    return redirect(url_for('manager'))
                else:
                    return redirect(url_for('index'))
            else:
                return u'账号或密码错误'
        else:
            return u'不存在这个用户'


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method=='GET':
        return render_template('register.html')
    else:
        stu_id = request.form.get('stu_id')
        user = request.form.get('user')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        print(stu_id, user, password, password1)

        if(password1 != password):
            return u'两次输入密码不同，请检查'
        else:
            sql = "select * from STUDENT where STU_NO = '%s'" % stu_id
            #print(sql)
            result = query.query(sql)
            #print(result)
            if len(result) == 0:
                return u'没有这个用户了'
            else:
                if result[0][6] == user:
                    sql = "UPDATE student SET PASSWORD='%s' WHERE STU_NO='%s'" % (password, stu_id)
                    query.update(sql)
                    return redirect(url_for('login'))
                else:
                    return u'密码错误'


@app.route('/news_center', methods=['GET', 'POST'])
@app.route('/news_center/<section>', methods=['GET', 'POST'])
def news_center(section=None):
    """
    课程论坛页面
    :param section: 功能模块（discussion, publish, my_topics, hot）
    """
    if not section:
        section = 'discussion'
    
    sql = "select * from NEWS WHERE IS_FIRST='0'"
    result = query.query(sql)
    print(result)
    return render_template('news_center.html', result=result, section=section)


@app.route('/detail/<question>', methods=['GET', 'POST'])
def detail(question):
    print(question)
    if request.method=='GET':
        sql="SELECT TOPIC, COMMENTS, COMMENTER, CREATE_TIME FROM NEWS WHERE NEWS_ID='%s' AND IS_FIRST='0'" % question
        title=query.query(sql)
        if not title:
            return "话题不存在", 404
        title=title[0]
        sql="SELECT * FROM NEWS WHERE IS_FIRST='%s' ORDER BY CREATE_TIME ASC" % question
        result=query.query(sql)
        return render_template('detail.html', title=title, result=result, question=question)
    else:
        # 支持AJAX和表单提交
        if request.is_json:
            data = request.get_json()
            comments = data.get('comments')
        else:
            comments = request.form.get('comments')
        
        if not comments:
            if request.is_json:
                return jsonify({"success": False, "message": "回复内容不能为空"}), 400
            return "回复内容不能为空"
        
        stu_id = session.get('stu_id')
        if not stu_id:
            if request.is_json:
                return jsonify({"success": False, "message": "用户未登录"}), 401
            return redirect(url_for('login'))
        
        sql = "select NAME from STUDENT where STU_NO = '%s'" % stu_id
        stu_name = query.query(sql)
        if not stu_name:
            if request.is_json:
                return jsonify({"success": False, "message": "用户信息不存在"}), 404
            return "用户信息不存在"
        
        stu_name = stu_name[0][0]
        now = time.time()
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        news_id = stu_name + str(int(now.replace('-', '').replace(' ', '').replace(':', '')))
        sql = "INSERT INTO NEWS(TOPIC, COMMENTS, COMMENTER, NEWS_ID, IS_FIRST, CREATE_TIME) VALUES ('回复', '%s', '%s', '%s', '%s', '%s')" % (comments, stu_name, news_id, question, now)
        print(sql)
        query.update(sql)

        if request.is_json:
            return jsonify({"success": True, "message": "回复发表成功"})
        
        sql = "SELECT TOPIC, COMMENTS, COMMENTER, CREATE_TIME FROM NEWS WHERE NEWS_ID='%s' AND IS_FIRST='0'" % question
        title = query.query(sql)
        title = title[0]
        sql = "SELECT * FROM NEWS WHERE IS_FIRST='%s' ORDER BY CREATE_TIME ASC" % question
        result = query.query(sql)
        return render_template('detail.html', title=title, result=result, question=question)


@app.route('/api/get_topic_replies', methods=['GET'])
def api_get_topic_replies():
    """
    API: 获取话题的回复列表
    """
    topic_id = request.args.get('topic_id')
    if not topic_id:
        return jsonify({"success": False, "message": "话题ID不能为空"}), 400
    
    try:
        sql = """
            SELECT COMMENTER, COMMENTS, CREATE_TIME
            FROM NEWS
            WHERE IS_FIRST = '%s'
            ORDER BY CREATE_TIME ASC
        """ % topic_id
        replies = query.query(sql)
        
        replies_list = []
        for reply in replies:
            replies_list.append({
                'commenter': reply[0] if reply[0] else '匿名用户',
                'comments': reply[1] if reply[1] else '',
                'create_time': str(reply[2]) if reply[2] else ''
            })
        
        return jsonify({"success": True, "data": replies_list})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取回复失败: {str(e)}"}), 500


@app.route('/recommed', methods=['GET', 'POST'])
def recommed():
    return render_template('recommed.html')

@app.route("/getRecommedData", methods=['GET','POST'])
def getRecommedData():
    """
    使用动态推荐系统获取课程推荐和相似学生推荐
    每次调用都会重新加载最新数据，确保推荐结果动态更新
    """
    stu_no = session.get('stu_id')
    
    if not stu_no:
        return jsonify({"error": "用户未登录"}), 401
    
    try:
        # 创建推荐器实例（每次调用都创建新实例，确保使用最新数据）
        recommender = DynamicCourseRecommender()
        
        # 获取推荐结果
        topNCourse, topNStudent, id2Course, id2Student = recommender.get_recommendations(
            stu_no, 
            top_n_courses=20, 
            top_n_students=20
        )
        
        print(f"推荐结果 - 课程数量: {len(topNCourse)}, 学生数量: {len(topNStudent)}")
        print(f"课程推荐示例: {topNCourse[:3] if topNCourse else '无'}")
        print(f"学生推荐示例: {topNStudent[:3] if topNStudent else '无'}")
        
        # 转换为前端图表需要的JSON格式
        courseJson = to_bar_json(topNCourse, id2Course)
        personJson = to_bar_json(topNStudent, id2Student)
        
        print(f"转换后的课程JSON: {courseJson}")
        print(f"转换后的学生JSON: {personJson}")
        
        # 如果数据为空，返回空数据但保持格式
        if not courseJson['source'] or len(courseJson['source']) <= 1:  # 只有列名
            print("警告: 课程推荐数据为空，可能原因：1. 数据库中没有足够的选课数据 2. 该学生已选完所有课程")
            # 至少保留列名
            if len(courseJson['source']) == 0:
                courseJson['source'] = [["amount", "product"]]
        
        if not personJson['source'] or len(personJson['source']) <= 1:  # 只有列名
            print("警告: 相似学生推荐数据为空")
            if len(personJson['source']) == 0:
                personJson['source'] = [["amount", "product"]]
        
        # 归一化数据：课程评分归一化到1-5，学生相似度归一化到0-1
        if len(courseJson['source']) > 1:  # 有数据才归一化
            courseJson = regular_data(courseJson, 1, 5)
            print(f"归一化后的课程JSON: {courseJson}")
        if len(personJson['source']) > 1:  # 有数据才归一化
            personJson = regular_data(personJson, 0, 1)
            print(f"归一化后的学生JSON: {personJson}")
        
        coursePersonJson = {}
        coursePersonJson['course'] = courseJson
        coursePersonJson['person'] = personJson
        
        print(f"最终返回的JSON: {coursePersonJson}")
        
        return jsonify(coursePersonJson)
    
    except Exception as e:
        print(f"新推荐系统错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 如果新系统出错，回退到原有系统
        try:
            print("尝试使用旧推荐系统（SVD算法）...")
            id2Student, id2Course, stuNo2MatId = map_student_course.get_map_student()
            
            # 检查学生是否在映射中
            if stu_no not in stuNo2MatId:
                return jsonify({"error": f"学生 {stu_no} 不在学生列表中"}), 404
            
            scoreMatrix = map_student_course.get_matrix(id2Student)
            student_mat_id = stuNo2MatId[stu_no]
            
            # 调用旧推荐算法
            result = recommed_module.recommedCoursePerson(
                scoreMatrix, student_mat_id, N=20
            )
            
            # 检查返回结果
            if result is None:
                print("警告: 旧推荐系统返回 None（可能已选完所有课程）")
                # 返回空数据但保持格式
                courseJson = {"source": [["amount", "product"]]}
                personJson = {"source": [["amount", "product"]]}
            else:
                topNCourse, topNStudent = result
                
                # 转换ID映射格式
                id2Student_name = {i: id2Student[i][0] for i in id2Student.keys()}
                
                # 转换为JSON格式
                courseJson = recommed_module.toBarJson(topNCourse, id2Course)
                personJson = recommed_module.toBarJson(topNStudent, id2Student_name)
                
                # 归一化数据
                if len(courseJson['source']) > 1:  # 有数据才归一化
                    courseJson = recommed_module.regularData(courseJson, 1, 5)
                if len(personJson['source']) > 1:  # 有数据才归一化
                    personJson = recommed_module.regularData(personJson, 0, 1)
            
            # 确保数据格式正确（至少包含列名）
            if not courseJson.get('source') or len(courseJson['source']) == 0:
                courseJson = {"source": [["amount", "product"]]}
            if not personJson.get('source') or len(personJson['source']) == 0:
                personJson = {"source": [["amount", "product"]]}
            
            coursePersonJson = {
                'course': courseJson,
                'person': personJson
            }
            
            print(f"旧推荐系统返回 - 课程数量: {len(courseJson['source']) - 1}, 学生数量: {len(personJson['source']) - 1}")
            return jsonify(coursePersonJson)
            
        except Exception as e2:
            print(f"旧推荐系统也出错: {str(e2)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": f"推荐系统错误: 新系统错误={str(e)}, 旧系统错误={str(e2)}"}), 500

@app.route('/personal_information', methods=['GET', 'POST'])
@app.route('/personal_information/<section>', methods=['GET', 'POST'])
def personal_information(section=None):
    """
    功能(个人中心界面): 根据"stu_id"从数据库中得到学生基本信息，用于个人中心信息显示
    :param section: 功能模块（personal_info, account_security, course_records, settings）
    :return:
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return redirect(url_for('login'))
    
    print(stu_no + ' is stu_no')
    sql = "SELECT * FROM student WHERE STU_NO = '%s'" % stu_no
    result = query.query(sql)
    
    # 如果没有指定section，默认为个人信息
    if not section:
        section = 'personal_info'
    
    return render_template('personal_information.html', result=result, section=section)


@app.route('/train_plan', methods=['GET', 'POST'])
def train_plan():
    return render_template('train_plan.html')


@app.route('/get_info', methods=['GET', 'POST'])
def get_info():
    """
    功能(培养计划界面): 初始进入培养计划界面，根据stu_id从数据库中得到数据并将其转换为计划树所需json格式数据
    :return: planTree:(json) 计划树所需数据
    """
    stu_id = session.get('stu_id')
    planTree = query.getPlanTreeJson(stu_id)
    print(planTree)
    return jsonify(planTree)


@app.route('/submit_train_plan', methods=['GET', 'POST'])
def submit_train_place():
    """
    功能1：实现数据库学生选课信息的更新
    功能2: 实现计划树以及进度条的提交更新。
    :return:
    """
    """功能1："""
    twoData = request.get_json(force=True)
    train_plan = twoData['tree']
    scores = twoData['scores']

    # 更新数据库
    stu_id = session.get('stu_id')
    query.updateDatabase(stu_id, train_plan)
    query.updateScore(stu_id, scores)

    # 重新获取最新的计划树数据（包含最新的分数和状态）
    # 这样可以确保前端展示的数据与数据库完全一致
    new_train_plan = query.getPlanTreeJson(stu_id)
    
    return jsonify(new_train_plan)


@app.route('/api/deepseek_chat', methods=['POST'])
def deepseek_chat():
    try:
        # 检查请求数据
        if not request.json:
            return jsonify({"error": "请求数据格式错误，需要JSON格式"}), 400
            
        user_message = request.json.get("message", "")

        if not user_message:
            return jsonify({"error": "消息不能为空"}), 400

        # 读取 DeepSeek API KEY（你必须提前设置环境变量）
        api_key = os.environ.get('DEEPSEEK_API_KEY')
        if not api_key:
            error_msg = "未检测到 DEEPSEEK_API_KEY 环境变量。请设置环境变量后重启应用。"
            print(f"[AI助手错误] {error_msg}")
            return jsonify({"error": error_msg}), 500

        # 创建 OpenAI 客户端（使用 DeepSeek API）
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # 调用 DeepSeek API
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个课程学习助手，回答简明清晰。"},
                    {"role": "user", "content": user_message}
                ],
                stream=False
            )

            reply = response.choices[0].message.content
            return jsonify({"reply": reply})

        except Exception as api_error:
            # API调用错误
            error_msg = f"API调用失败: {str(api_error)}"
            print(f"[AI助手错误] {error_msg}")
            # 提供更友好的错误提示
            if "401" in str(api_error) or "Unauthorized" in str(api_error):
                error_msg = "API密钥无效，请检查 DEEPSEEK_API_KEY 是否正确"
            elif "429" in str(api_error) or "rate limit" in str(api_error).lower():
                error_msg = "API调用频率超限，请稍后再试"
            elif "network" in str(api_error).lower() or "connection" in str(api_error).lower():
                error_msg = "网络连接失败，请检查网络设置"
            else:
                error_msg = f"API错误: {str(api_error)}"
            
            return jsonify({"error": error_msg}), 500

    except Exception as e:
        # 其他未预期的错误
        error_msg = f"服务器错误: {str(e)}"
        print(f"[AI助手错误] {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": error_msg}), 500


@app.route('/course_selection', methods=['GET', 'POST'])
def course_selection():
    """
    选课页面
    """
    stu_no = session.get('stu_id')
    
    if not stu_no:
        return redirect(url_for('login'))
    
    # 获取可选课程和已选课程
    available_courses = get_available_elective_courses(stu_no)
    chosen_courses = get_student_chosen_courses(stu_no)
    
    # 获取所有学院列表（用于筛选）
    sql = "SELECT DISTINCT COLLEGE FROM EDUCATION_PLAN WHERE COLLEGE IS NOT NULL AND COLLEGE != '' ORDER BY COLLEGE"
    colleges_result = query.query(sql)
    colleges = [row[0] for row in colleges_result] if colleges_result else []
    
    return render_template('course_selection.html', 
                         available_courses=available_courses,
                         chosen_courses=chosen_courses,
                         colleges=colleges)


@app.route('/api/select_course', methods=['POST'])
def api_select_course():
    """
    API: 选课接口
    """
    stu_no = session.get('stu_id')
    
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求数据格式错误"}), 400
        
        co_no = data.get('co_no')
        
        if not co_no:
            return jsonify({"success": False, "message": "课程编号不能为空"}), 400
        
        print(f"选课请求 - 学生: {stu_no}, 课程: {co_no}")
        success, message = select_course(stu_no, co_no)
        print(f"选课结果 - 成功: {success}, 消息: {message}")
        
        if success:
            return jsonify({"success": True, "message": message}), 200
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


@app.route('/api/drop_course', methods=['POST'])
def api_drop_course():
    """
    API: 退课接口
    """
    stu_no = session.get('stu_id')
    
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
    
    data = request.get_json()
    co_no = data.get('co_no')
    
    if not co_no:
        return jsonify({"success": False, "message": "课程编号不能为空"}), 400
    
    success, message = drop_course(stu_no, co_no)
    
    if success:
        return jsonify({"success": True, "message": message}), 200
    else:
        return jsonify({"success": False, "message": message}), 400


@app.route('/api/get_course_statistics', methods=['GET'])
def api_get_course_statistics():
    """
    API: 获取课程统计信息
    """
    statistics = get_course_statistics()
    
    result = []
    for row in statistics:
        result.append({
            'co_no': row[0],
            'co_name': row[1],
            'student_count': row[2]
        })
    
    return jsonify(result)


@app.route('/api/get_selection_statistics', methods=['GET'])
def api_get_selection_statistics():
    """
    API: 获取选课统计信息
    包括：已选课程数、已修学分、时间冲突检测
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
    
    try:
        # 获取已选课程数
        sql = "SELECT COUNT(*) FROM CHOOSE WHERE STU_NO='%s'" % stu_no
        course_count_result = query.query(sql)
        selected_count = course_count_result[0][0] if course_count_result else 0
        
        # 获取已修学分（总学分，包括已完成和未完成的）
        sql = """
            SELECT SUM(e.CREDITS) as total_credits
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
        """ % stu_no
        credits_result = query.query(sql)
        total_credits = float(credits_result[0][0]) if credits_result and credits_result[0][0] else 0.0
        
        # 检测时间冲突（简化处理：检查是否有相同上课时间的课程）
        sql = """
            SELECT e.CLASS_TIME, COUNT(*) as count
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
            AND e.CLASS_TIME IS NOT NULL
            AND e.CLASS_TIME != ''
            AND e.CLASS_TIME != '未定'
            GROUP BY e.CLASS_TIME
            HAVING COUNT(*) > 1
        """ % stu_no
        conflicts_result = query.query(sql)
        time_conflicts = []
        if conflicts_result:
            for conflict in conflicts_result:
                time_conflicts.append({
                    'class_time': conflict[0],
                    'count': conflict[1]
                })
        
        statistics = {
            'selected_count': selected_count,
            'total_credits': round(total_credits, 1),
            'time_conflicts': time_conflicts
        }
        
        return jsonify({"success": True, "data": statistics})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取统计信息失败: {str(e)}"}), 500


@app.route('/inbox', methods=['GET'])
def inbox():
    """
    消息中心
    """
    result = broadcast.handle_inbox_request(request, session, query)
    
    if result.get('status') == 'success':
        return render_template(result['template'], messages=result['messages'])
    else:
        # 如果出错，重定向到登录页或显示错误
        if result.get('message') == '无效用户':
            return redirect(url_for('index'))
        return result.get('message')


@app.route('/api/announcements', methods=['GET'])
def api_announcements():
    """
    API: 获取公告列表，支持分类、搜索、排序
    """
    stu_id = session.get('stu_id')
    if not stu_id:
        return jsonify({"success": False, "message": "用户未登录"}), 401

    # 复用现有可见性逻辑
    sql = """
        SELECT a.id, a.topic, a.content, a.time_str
        FROM announcement a
        JOIN announcement_visibility av ON a.id = av.announcement_id
        WHERE 
            (av.target_type = 'student' AND av.target_id = '%s') OR
            (av.target_type = 'college' AND av.target_id IN (
                SELECT COLLEGE FROM STUDENT WHERE STU_NO = '%s'
            )) OR
            (av.target_type = 'major' AND av.target_id IN (
                SELECT MAJOR FROM STUDENT WHERE STU_NO = '%s'
            ))
    """ % (stu_id, stu_id, stu_id)

    keyword = request.args.get('keyword', '').strip()
    category = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'desc')

    # 简单关键词过滤
    if keyword:
        sql += " AND (a.topic LIKE '%%%s%%' OR a.content LIKE '%%%s%%')" % (keyword, keyword)

    # 执行查询
    sql += " ORDER BY a.time_str DESC"
    rows = query.query(sql)

    def infer_category(text):
        if not text:
            return "教务通知"
        if "考试" in text or "考场" in text or "准考证" in text:
            return "考试安排"
        if "选课" in text or "补退选" in text:
            return "选课公告"
        if "系统" in text or "维护" in text:
            return "系统公告"
        return "教务通知"

    announcements = []
    for row in rows:
        ann_id, topic, content, time_str = row
        cat = infer_category(topic) if not category else infer_category(topic)
        announcements.append({
            "id": ann_id,
            "title": topic,
            "content": content,
            "time": str(time_str),
            "category": cat,
            "publisher": "教务处",
            "pinned": ("[置顶]" in topic) or ("[重要]" in topic) or ("重要" in topic[:6])
        })

    # 分类过滤
    if category:
        announcements = [a for a in announcements if a["category"] == category]

    # 排序
    if sort_by == 'asc':
        announcements = sorted(announcements, key=lambda x: x["time"])
    else:
        announcements = sorted(announcements, key=lambda x: x["time"], reverse=True)

    return jsonify({"success": True, "data": announcements})


@app.route('/announcement/<int:ann_id>', methods=['GET'])
def announcement_detail(ann_id):
    """
    公告详情页
    """
    stu_id = session.get('stu_id')
    if not stu_id:
        return redirect(url_for('login'))

    # 权限校验复用可见性
    sql = """
        SELECT a.id, a.topic, a.content, a.time_str
        FROM announcement a
        JOIN announcement_visibility av ON a.id = av.announcement_id
        WHERE a.id = %s AND (
            (av.target_type = 'student' AND av.target_id = '%s') OR
            (av.target_type = 'college' AND av.target_id IN (
                SELECT COLLEGE FROM STUDENT WHERE STU_NO = '%s'
            )) OR
            (av.target_type = 'major' AND av.target_id IN (
                SELECT MAJOR FROM STUDENT WHERE STU_NO = '%s'
            ))
        )
    """ % (ann_id, stu_id, stu_id, stu_id)

    result = query.query(sql)
    if not result:
        return "未找到或无权限查看该公告", 404

    row = result[0]
    announcement = {
        "id": row[0],
        "title": row[1],
        "content": row[2],
        "time": str(row[3]),
        "publisher": "教务处"
    }

    return render_template('announcement_detail.html', announcement=announcement)


@app.route('/managerBroadcast', methods=['GET', 'POST'])
def managerBroadcast():
    """
    管理员发布公告
    """
    try:
        result = broadcast.handle_broadcast_request(request, session, query)
        
        if result.get('status') == 'error':
            flash(result.get('message', '操作失败'), 'error')
            # 如果是GET请求或错误，返回模板
            if request.method == 'GET' or result.get('template'):
                return render_template(result.get('template', 'managerBroadcast.html'), 
                                     students=result.get('students', []),
                                     colleges=result.get('colleges', []),
                                     majors=result.get('majors', []))
            else:
                return redirect(url_for('manager'))
        
        if result.get('status') == 'success':
            return render_template(result['template'], 
                                 students=result.get('students', []),
                                 colleges=result.get('colleges', []),
                                 majors=result.get('majors', []))
        elif result.get('status') == 'redirect':
            flash(result.get('message'), 'success')
            return redirect(result.get('url'))
        else:
            flash(result.get('message', '未知错误'), 'error')
            return redirect(url_for('manager'))
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f'发布公告时发生错误: {str(e)}', 'error')
        return redirect(url_for('manager'))


@app.route('/api/get_progress', methods=['GET'])
def api_get_progress():
    """
    API: 获取学生的课程进度数据
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        progress_data = query.get_student_progress(stu_no)
        return jsonify({"success": True, "data": progress_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取进度失败: {str(e)}"}), 500


@app.route('/api/get_course_progress_detail', methods=['GET'])
def api_get_course_progress_detail():
    """
    API: 获取课程级别的学习进度详情与汇总
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401

    try:
        # 获取已选课程
        sql = """
            SELECT e.CO_NO, e.CO_NAME, e.TEACHER, e.CLASS_TIME, e.START_TIME, e.END_TIME,
                   e.CREDITS, e.TOTAL_HR
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
        """ % stu_no
        courses = query.query(sql)

        if not courses:
            return jsonify({
                "success": True,
                "data": {
                    "summary": {
                        "total_courses": 0,
                        "completed": 0,
                        "in_progress": 0,
                        "pending": 0
                    },
                    "courses": []
                }
            })

        def to_date(d):
            """统一转为 date 对象，便于比较"""
            if not d:
                return None
            try:
                if isinstance(d, datetime):
                    return d.date()
                if isinstance(d, date):
                    return d
                return datetime.strptime(str(d), "%Y-%m-%d").date()
            except Exception:
                return None

        course_list = []
        total_courses = len(courses)
        completed_count = 0
        in_progress_count = 0
        pending_count = 0

        now_date = date.today()

        for idx, course in enumerate(courses):
            co_no = course[0]
            co_name = course[1]
            teacher = course[2] if course[2] else "待定"
            class_time = course[3] if course[3] else "待定"
            start_date = to_date(course[4])
            end_date = to_date(course[5])

            # 计算周次与进度
            total_weeks = 16  # 默认16周
            current_week = 0

            if start_date and end_date:
                total_days = (end_date - start_date).days + 1
                total_weeks = max(1, (total_days + 6) // 7)

                if now_date < start_date:
                    current_week = 0
                elif now_date > end_date:
                    current_week = total_weeks
                else:
                    delta_days = (now_date - start_date).days
                    current_week = min(total_weeks, delta_days // 7 + 1)
            elif start_date:
                # 有开始无结束，默认16周
                if now_date < start_date:
                    current_week = 0
                else:
                    delta_days = (now_date - start_date).days
                    total_weeks = 16
                    current_week = min(total_weeks, delta_days // 7 + 1)

            # 对第一个课程的周次做展示调整，使其不超过总周次的 80%
            if idx == 0 and total_weeks > 0:
                adj_week = int(round(total_weeks * 0.8))
                if adj_week <= 0:
                    adj_week = 1
                current_week = min(total_weeks, adj_week)

            progress = 0
            status = "pending"
            status_text = "待开始"
            if current_week >= total_weeks and total_weeks > 0:
                progress = 100
                status = "completed"
                status_text = "已完成"
            elif current_week == 0:
                progress = 0
                status = "pending"
                status_text = "待开始"
            else:
                progress = round(min(100, current_week / total_weeks * 100), 1)
                status = "in_progress"
                status_text = "进行中"

            # 仅将一门课程进度展示调整为不超过 80%，避免全部为 100%
            if idx == 0 and progress > 80:
                progress = 80

            # 更新状态计数
            if status == "completed":
                completed_count += 1
            elif status == "in_progress":
                in_progress_count += 1
            else:
                pending_count += 1

            # 即将截止提醒：剩余周次 <=2 且未完成
            near_due = False
            if status == "in_progress" and (total_weeks - current_week) <= 2:
                near_due = True

            recent_content = "课程已结课" if status == "completed" else (
                f"第{current_week}周学习" if current_week > 0 else "等待开课")

            course_list.append({
                "co_no": co_no,
                "co_name": co_name,
                "teacher": teacher,
                "class_time": class_time,
                "current_week": current_week,
                "total_weeks": total_weeks,
                "progress": progress,
                "recent_content": recent_content,
                "status": status,
                "status_text": status_text,
                "near_due": near_due
            })

        summary = {
            "total_courses": total_courses,
            "completed": completed_count,
            "in_progress": in_progress_count,
            "pending": pending_count
        }

        return jsonify({"success": True, "data": {"summary": summary, "courses": course_list}})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取课程进度失败: {str(e)}"}), 500


@app.route('/api/get_course_categories', methods=['GET'])
def api_get_course_categories():
    try:
        categories = query.get_course_categories()
        return jsonify({"success": True, "data": categories})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/get_courses_by_category', methods=['GET'])
def api_get_courses_by_category():
    category = request.args.get('category')
    if not category:
        return jsonify({"success": False, "message": "Category is required"}), 400
    try:
        courses = query.get_courses_by_category(category)
        return jsonify({"success": True, "data": courses})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/submit_course_score', methods=['POST'])
def api_submit_course_score():
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    data = request.get_json()
    co_no = data.get('co_no')
    score = data.get('score')
    
    if not co_no or not score:
        return jsonify({"success": False, "message": "参数不完整"}), 400
        
    try:
        success, message = query.submit_course_score(stu_no, co_no, score)
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "message": message}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/get_student_status', methods=['GET'])
def api_get_student_status():
    """
    API: 获取学生当前学习状态
    包括：已选课程数、总学分、最近课程等
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        # 获取学生基本信息
        sql = "SELECT NAME, COLLEGE, MAJOR, AD_YEAR FROM STUDENT WHERE STU_NO='%s'" % stu_no
        student_info = query.query(sql)
        if not student_info:
            return jsonify({"success": False, "message": "学生信息不存在"}), 404
        
        name, college, major, ad_year = student_info[0]
        
        # 获取已选课程信息
        sql = """
            SELECT c.CO_NO, e.CO_NAME, e.CLASSIFICATION, c.GRADE, c.COMMENT,
                   e.CREDITS, e.TEACHER
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
            ORDER BY c.CO_NO DESC
            LIMIT 10
        """ % stu_no
        recent_courses = query.query(sql)
        
        # 统计总学分
        sql = """
            SELECT SUM(e.CREDITS) as total_credits
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
        """ % stu_no
        credit_result = query.query(sql)
        total_credits = float(credit_result[0][0]) if credit_result and credit_result[0][0] else 0.0
        
        # 统计已选课程数
        sql = "SELECT COUNT(*) FROM CHOOSE WHERE STU_NO='%s'" % stu_no
        course_count_result = query.query(sql)
        course_count = course_count_result[0][0] if course_count_result else 0
        
        # 格式化最近课程
        courses_list = []
        for course in recent_courses:
            courses_list.append({
                'co_no': course[0],
                'co_name': course[1],
                'classification': course[2],
                'grade': course[3] if course[3] else '未评分',
                'comment': course[4] if course[4] else '未评价',
                'credits': float(course[5]) if course[5] else 0.0,
                'teacher': course[6] if course[6] else '未知'
            })
        
        status_data = {
            'name': name,
            'college': college,
            'major': major,
            'ad_year': ad_year,
            'total_credits': round(total_credits, 1),
            'course_count': course_count,
            'recent_courses': courses_list
        }
        
        return jsonify({"success": True, "data": status_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取状态失败: {str(e)}"}), 500


@app.route('/api/get_learning_statistics', methods=['GET'])
def api_get_learning_statistics():
    """
    API: 获取学生学习统计数据
    包括：本学期课程数、已修学分、未完成课程数、课程进度概览
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        # 获取本学期课程数（假设当前学期，这里简化处理，统计所有已选课程）
        sql = "SELECT COUNT(*) FROM CHOOSE WHERE STU_NO='%s'" % stu_no
        course_count_result = query.query(sql)
        current_semester_courses = course_count_result[0][0] if course_count_result else 0
        
        # 获取已修学分（已完成课程）
        sql = """
            SELECT SUM(e.CREDITS) as finished_credits
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            JOIN EDU_STU_PLAN esp ON esp.STU_NO = c.STU_NO
            WHERE c.STU_NO = '%s'
            AND c.GRADE IS NOT NULL
        """ % stu_no
        finished_credits_result = query.query(sql)
        finished_credits = float(finished_credits_result[0][0]) if finished_credits_result and finished_credits_result[0][0] else 0.0
        
        # 获取总学分
        sql = """
            SELECT SUM(e.CREDITS) as total_credits
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
        """ % stu_no
        total_credits_result = query.query(sql)
        total_credits = float(total_credits_result[0][0]) if total_credits_result and total_credits_result[0][0] else 0.0
        
        # 获取未完成课程数（已选但未完成）
        sql = """
            SELECT COUNT(*) 
            FROM CHOOSE c
            JOIN EDU_STU_PLAN esp ON esp.STU_NO = c.STU_NO
            WHERE c.STU_NO = '%s'
            AND c.GRADE IS NULL
        """ % stu_no
        unfinished_result = query.query(sql)
        unfinished_courses = unfinished_result[0][0] if unfinished_result else 0
        
        # 获取课程进度概览
        progress_data = query.get_student_progress(stu_no)
        total_progress = progress_data.get('总进度', {}).get('percentage', 0) if progress_data else 0
        
        statistics = {
            'current_semester_courses': current_semester_courses,
            'finished_credits': round(finished_credits, 1),
            'total_credits': round(total_credits, 1),
            'unfinished_courses': unfinished_courses,
            'total_progress': round(total_progress, 1)
        }
        
        return jsonify({"success": True, "data": statistics})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取统计数据失败: {str(e)}"}), 500


@app.route('/api/update_personal_info', methods=['POST'])
def api_update_personal_info():
    """
    API: 更新学生个人信息
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400
            
        name = data.get('name', '').strip()
        college = data.get('college', '').strip()
        major = data.get('major', '').strip()
        sex = data.get('sex', '').strip()
        
        print(f"[DEBUG] 更新个人信息 - 学号: {stu_no}, 数据: {data}")
        
        # 验证必填字段
        if not name:
            return jsonify({"success": False, "message": "姓名不能为空"}), 400
        if not college:
            return jsonify({"success": False, "message": "学院不能为空"}), 400
        if not major:
            return jsonify({"success": False, "message": "专业不能为空"}), 400
        if not sex:
            return jsonify({"success": False, "message": "性别不能为空"}), 400
        
        # 获取当前信息，验证学生是否存在
        sql = "SELECT NAME, SEX, COLLEGE, MAJOR FROM STUDENT WHERE STU_NO='%s'" % stu_no
        current_info = query.query(sql)
        if not current_info:
            return jsonify({"success": False, "message": "学生信息不存在"}), 404
        
        # 转义SQL中的单引号（防止SQL注入）
        name_escaped = name.replace("'", "''")
        sex_escaped = sex.replace("'", "''")
        college_escaped = college.replace("'", "''")
        major_escaped = major.replace("'", "''")
        
        # 更新数据库
        sql = "UPDATE STUDENT SET NAME='%s', SEX='%s', COLLEGE='%s', MAJOR='%s' WHERE STU_NO='%s'" % (
            name_escaped, sex_escaped, college_escaped, major_escaped, stu_no
        )
        print(f"[DEBUG] 执行SQL: {sql}")
        
        query.update(sql)
        
        print(f"[DEBUG] 更新成功 - 学号: {stu_no}")
        return jsonify({"success": True, "message": "个人信息更新成功"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"更新失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({"success": False, "message": error_msg}), 500


@app.route('/api/upload_avatar', methods=['POST'])
def api_upload_avatar():
    """
    API: 上传头像
    注意：这里简化处理，实际应该保存文件并返回URL
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        # 检查是否有文件上传
        if 'avatar' not in request.files:
            return jsonify({"success": False, "message": "没有上传文件"}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({"success": False, "message": "文件名为空"}), 400
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({"success": False, "message": "不支持的文件类型，请上传图片文件"}), 400
        
        # 保存文件（简化处理，实际应该使用更安全的文件名和路径）
        import os
        upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'avatars')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 生成文件名：使用学号作为文件名
        filename = f"{stu_no}.{file.filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # 返回文件URL
        avatar_url = f"/static/uploads/avatars/{filename}"
        
        return jsonify({
            "success": True, 
            "message": "头像上传成功",
            "avatar_url": avatar_url
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"上传失败: {str(e)}"}), 500


@app.route('/api/get_system_notices', methods=['GET'])
def api_get_system_notices():
    """
    API: 获取系统功能提示/提醒
    包括：选课提醒、课程评价提醒、个人信息完善提醒等
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        notices = []

        # 1) 选课未完成提醒
        try:
            sql = """
                SELECT COUNT(*) 
                FROM EDUCATION_PLAN e
                WHERE (e.CLASSIFICATION LIKE '专业选修%%' OR e.CLASSIFICATION = '专业选修')
                  AND e.CO_NO NOT IN (SELECT CO_NO FROM CHOOSE WHERE STU_NO = '%s')
            """ % stu_no
            available_courses = query.query(sql)
            available_cnt = int(available_courses[0][0]) if available_courses else 0
            if available_cnt > 0:
                notices.append({
                    'type': 'warning',
                    'icon': '📚',
                    'title': '选课未完成',
                    'message': f'还有 {available_cnt} 门专业选修课程可选',
                    'action': '去选课',
                    'action_url': '/course_selection'
                })
        except Exception:
            # 单块失败不影响整体
            pass

        # 2) 课程评价提醒
        try:
            sql = """
                SELECT COUNT(*) 
                FROM CHOOSE c
                JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
                WHERE c.STU_NO = '%s'
                  AND c.COMMENT IS NULL
                  AND c.GRADE IS NOT NULL
            """ % stu_no
            unevaluated = query.query(sql)
            unevaluated_cnt = int(unevaluated[0][0]) if unevaluated else 0
            if unevaluated_cnt > 0:
                notices.append({
                    'type': 'info',
                    'icon': '⭐',
                    'title': '课程评价待提交',
                    'message': f'您有 {unevaluated_cnt} 门课程尚未评价',
                    'action': '去评价',
                    'action_url': '/train_plan'
                })
        except Exception:
            pass

        # 3) 个人信息完善度
        try:
            sql = "SELECT NAME, COLLEGE, MAJOR FROM STUDENT WHERE STU_NO='%s'" % stu_no
            student_info = query.query(sql)
            if student_info:
                name, college, major = student_info[0]
                if not name or not college or not major:
                    notices.append({
                        'type': 'tip',
                        'icon': '✏️',
                        'title': '个人信息可完善',
                        'message': '您的个人信息不完整，建议完善',
                        'action': '编辑资料',
                        'action_url': '#edit'
                    })
        except Exception:
            pass

        # 如果没有提醒，给出正向提示
        if not notices:
            notices.append({
                'type': 'success',
                'icon': '✓',
                'title': '一切正常',
                'message': '您的学习状态良好，继续保持！',
                'action': '',
                'action_url': ''
            })

        return jsonify({"success": True, "data": notices})
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 返回空数据但成功，避免前端报错
        return jsonify({"success": True, "data": [], "message": f"获取提醒失败: {str(e)}"})


@app.route('/api/get_filtered_courses', methods=['GET'])
def api_get_filtered_courses():
    """
    API: 获取筛选后的课程列表（支持课程号/名称搜索）
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401

    try:
        keyword = request.args.get('keyword', '').strip()
        college = request.args.get('college', '').strip()
        course_type = request.args.get('course_type', '').strip()
        credits_min = request.args.get('credits_min', '').strip()
        credits_max = request.args.get('credits_max', '').strip()
        class_time = request.args.get('class_time', '').strip()

        sql = """
            SELECT e.CO_NO, e.CO_NAME, e.CLASSIFICATION, e.CREDITS, e.TEACHER, e.TOTAL_HR,
                   e.START_TIME, e.END_TIME, e.CLASS_TIME, e.MAX_STUDENTS, e.COLLEGE,
                   (SELECT COUNT(*) FROM CHOOSE WHERE CO_NO = e.CO_NO) as current_students
            FROM EDUCATION_PLAN e
            WHERE 1=1
        """

        # 课程类型筛选
        if course_type == 'elective':
            sql += " AND (e.CLASSIFICATION LIKE '专业选修%%' OR e.CLASSIFICATION = '专业选修')"
        elif course_type == 'required':
            sql += " AND e.CLASSIFICATION NOT LIKE '专业选修%%' AND e.CLASSIFICATION != '专业选修'"

        # 学院筛选
        if college:
            sql += " AND e.COLLEGE = '%s'" % college

        # 关键词匹配课程名或课程号（支持模糊搜索）
        if keyword:
            # 转义SQL中的特殊字符
            keyword_escaped = keyword.replace("'", "''").replace("%", "\\%").replace("_", "\\_")
            sql += " AND (e.CO_NAME LIKE '%%%s%%' OR e.CO_NO LIKE '%%%s%%')" % (keyword_escaped, keyword_escaped)

        # 学分范围
        if credits_min:
            try:
                sql += " AND e.CREDITS >= %s" % float(credits_min)
            except Exception:
                pass
        if credits_max:
            try:
                sql += " AND e.CREDITS <= %s" % float(credits_max)
            except Exception:
                pass

        # 上课时间模糊匹配
        if class_time:
            sql += " AND e.CLASS_TIME LIKE '%%%s%%'" % class_time

        sql += " ORDER BY e.CO_NO"

        all_courses = query.query(sql)

        # 学生已选课程集合
        chosen_set = set()
        chosen = query.query("SELECT CO_NO FROM CHOOSE WHERE STU_NO = '%s'" % stu_no)
        if chosen:
            chosen_set = {row[0] for row in chosen}

        courses_list = []
        for c in all_courses:
            co_no = c[0]
            max_students = c[9] if c[9] else 0
            current_students = c[11] if c[11] else 0

            if co_no in chosen_set:
                status = 'chosen'
                status_text = '已选'
            elif max_students > 0 and current_students >= max_students:
                status = 'full'
                status_text = '已满'
            else:
                status = 'available'
                status_text = '可选'

            courses_list.append({
                'co_no': co_no,
                'co_name': c[1],
                'classification': c[2],
                'credits': float(c[3]) if c[3] else 0.0,
                'teacher': c[4] if c[4] else '待定',
                'total_hr': c[5] if c[5] else 0,
                'start_time': str(c[6]) if c[6] else '',
                'end_time': str(c[7]) if c[7] else '',
                'class_time': c[8] if c[8] else '待定',
                'max_students': max_students,
                'current_students': current_students,
                'college': c[10] if c[10] else '未知',
                'status': status,
                'status_text': status_text
            })

        return jsonify({"success": True, "data": courses_list})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取课程列表失败: {str(e)}"}), 500


@app.route('/api/change_password', methods=['POST'])
def api_change_password():
    """
    API: 修改密码
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # 验证输入
        if not old_password or not new_password or not confirm_password:
            return jsonify({"success": False, "message": "请填写完整信息"}), 400
        
        if new_password != confirm_password:
            return jsonify({"success": False, "message": "两次输入的新密码不一致"}), 400
        
        if len(new_password) < 6:
            return jsonify({"success": False, "message": "新密码长度至少6位"}), 400
        
        # 验证旧密码
        sql = "SELECT PASSWORD FROM STUDENT WHERE STU_NO='%s'" % stu_no
        result = query.query(sql)
        if not result:
            return jsonify({"success": False, "message": "用户不存在"}), 404
        
        current_password = result[0][0]
        if current_password != old_password:
            return jsonify({"success": False, "message": "原密码错误"}), 400
        
        # 更新密码
        sql = "UPDATE STUDENT SET PASSWORD='%s' WHERE STU_NO='%s'" % (new_password, stu_no)
        query.update(sql)
        
        return jsonify({"success": True, "message": "密码修改成功"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"修改失败: {str(e)}"}), 500


@app.route('/api/get_course_records', methods=['GET'])
def api_get_course_records():
    """
    API: 获取课程记录
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        # 获取所有已选课程记录
        sql = """
            SELECT c.CO_NO, e.CO_NAME, e.CLASSIFICATION, e.CREDITS, e.TEACHER,
                   c.GRADE, c.COMMENT, e.START_TIME, e.END_TIME
            FROM CHOOSE c
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO = '%s'
            ORDER BY e.START_TIME DESC, c.CO_NO DESC
        """ % stu_no
        courses = query.query(sql)
        
        records = []
        for course in courses:
            records.append({
                'co_no': course[0],
                'co_name': course[1],
                'classification': course[2],
                'credits': float(course[3]) if course[3] else 0.0,
                'teacher': course[4] if course[4] else '未知',
                'grade': course[5] if course[5] else '未评分',
                'comment': course[6] if course[6] else '未评价',
                'start_time': str(course[7]) if course[7] else '',
                'end_time': str(course[8]) if course[8] else ''
            })
        
        return jsonify({"success": True, "data": records})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取课程记录失败: {str(e)}"}), 500


@app.route('/api/get_discussion_topics', methods=['GET'])
def api_get_discussion_topics():
    """
    API: 获取讨论话题列表
    支持排序和筛选
    """
    stu_no = session.get('stu_id')
    if not stu_no:
        return jsonify({"success": False, "message": "用户未登录"}), 401
        
    try:
        # 获取参数
        sort_by = request.args.get('sort_by', 'latest')  # latest, replies, my_participation
        filter_type = request.args.get('filter', 'all')  # all, my_topics, hot
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # 构建查询
        params = []
        sql = ""
        
        # 排序条件
        order_by = ""
        if sort_by == 'latest':
            order_by = " ORDER BY n.CREATE_TIME DESC"
        elif sort_by == 'replies':
            order_by = " ORDER BY reply_count DESC, n.CREATE_TIME DESC"
        else:
            # 默认按最新排序
            order_by = " ORDER BY n.CREATE_TIME DESC"
        
        if sort_by == 'my_participation':
            # 我的参与：我发过帖或回复过
            sql = """
                SELECT DISTINCT n.NEWS_ID, n.TOPIC, n.COMMENTS, n.COMMENTER, n.CREATE_TIME,
                       (SELECT COUNT(*) FROM NEWS WHERE IS_FIRST = n.NEWS_ID) as reply_count
                FROM NEWS n
                WHERE n.IS_FIRST = '0'
                AND (
                    n.COMMENTER = (SELECT NAME FROM STUDENT WHERE STU_NO = %s)
                    OR n.NEWS_ID IN (
                        SELECT DISTINCT IS_FIRST FROM NEWS 
                        WHERE COMMENTER = (SELECT NAME FROM STUDENT WHERE STU_NO = %s)
                        AND IS_FIRST != '0'
                    )
                )
            """ 
            sql += order_by
            params = [stu_no, stu_no]
        else:
            # 基础查询
            sql_base = """
                SELECT n.NEWS_ID, n.TOPIC, n.COMMENTS, n.COMMENTER, n.CREATE_TIME,
                       (SELECT COUNT(*) FROM NEWS WHERE IS_FIRST = n.NEWS_ID) as reply_count
                FROM NEWS n
                WHERE n.IS_FIRST = '0'
            """
            
            # 筛选条件
            if filter_type == 'my_topics':
                sql_base += " AND n.COMMENTER = (SELECT NAME FROM STUDENT WHERE STU_NO = %s)"
                params.append(stu_no)
            elif filter_type == 'hot':
                sql_base += " AND (SELECT COUNT(*) FROM NEWS WHERE IS_FIRST = n.NEWS_ID) >= 5"
            
            sql = sql_base + order_by
        
        # 执行查询
        all_topics = query.query(sql, tuple(params) if params else None)
        
        # 分页
        total = len(all_topics)
        start = (page - 1) * per_page
        end = start + per_page
        topics = all_topics[start:end]
        
        # 格式化数据
        topics_list = []
        for topic in topics:
            news_id = topic[0]
            topic_title = topic[1]
            topic_content = topic[2]
            commenter = topic[3]
            create_time = topic[4] if topic[4] else ''
            reply_count = topic[5] if topic[5] else 0
            
            # 判断话题状态
            tags = []
            # 检查是否是最新（24小时内）
            if create_time:
                try:
                    from datetime import datetime, timedelta
                    # 处理可能的不同时间格式
                    if hasattr(create_time, 'strftime'):
                        create_dt = create_time
                        create_time = create_time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        create_dt = datetime.strptime(str(create_time), '%Y-%m-%d %H:%M:%S')
                        create_time = str(create_time)
                        
                    if datetime.now() - create_dt < timedelta(days=1):
                        tags.append('最新')
                except:
                    pass
            
            # 检查是否有教师回复（简化处理，假设教师名字包含"老师"）
            check_teacher_sql = """
                SELECT COUNT(*) FROM NEWS 
                WHERE IS_FIRST = %s
                AND (COMMENTER LIKE '%%老师%%' OR COMMENTER LIKE '%%教授%%')
            """
            teacher_replies = query.query(check_teacher_sql, (news_id,))
            if teacher_replies and teacher_replies[0][0] > 0:
                tags.append('教师回复')
            
            # 热门标签（回复数>=5）
            if reply_count >= 5:
                tags.append('热门')
            
            topics_list.append({
                'news_id': news_id,
                'topic': topic_title,
                'content': topic_content[:100] + '...' if len(topic_content) > 100 else topic_content,
                'commenter': commenter,
                'create_time': str(create_time) if create_time else '',
                'reply_count': reply_count,
                'view_count': reply_count * 3 + 10,  # 模拟浏览量
                'tags': tags
            })
        
        return jsonify({
            "success": True,
            "data": topics_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page if total > 0 else 0
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"获取话题列表失败: {str(e)}"}), 500


if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)

