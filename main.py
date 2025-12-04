from flask import Flask, render_template, request, flash,  jsonify, redirect, url_for, session
from utils import query, map_student_course, recommed_module
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
        topic = request.form.get('topic')
        comments = request.form.get('comments')
        #commenter = request.form.get('commenter')
        # print(len(topic))
        # print('course_discussion')
        # print(topic, commenter, comments)
        stu_id = session.get('stu_id')
        sql = "select NAME from STUDENT where STU_NO = '%s'" % stu_id
        stu_name = query.query(sql)
        stu_name = stu_name[0][0]
        now = time.time()
        now = time.strftime('%Y-%m-%d', time.localtime(now))
        now = str(now)
        news_id = stu_name + now
        sql = "INSERT INTO NEWS(TOPIC, COMMENTS, COMMENTER, NEWS_ID, IS_FIRST) VALUES ('%s', '%s', '%s', '%s', '0')" % (topic, comments, stu_name, news_id)
        print(sql)
        query.update(sql)
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
def news_center():
    sql = "select * from NEWS WHERE IS_FIRST='0'"
    result = query.query(sql)
    print(result)
    return render_template('news_center.html', result=result)


@app.route('/detail/<question>', methods=['GET', 'POST'])
def detail(question):
    print(question)
    #question=str(question)
    if request.method=='GET':
        sql="SELECT TOPIC, COMMENTS, COMMENTER, CREATE_TIME FROM NEWS WHERE NEWS_ID='%s' AND IS_FIRST='0'" % question
        title=query.query(sql)
        #print(title)
        title=title[0]
        sql="SELECT * FROM NEWS WHERE IS_FIRST='%s'" % question
        result=query.query(sql)
        return render_template('detail.html', title=title, result=result)
    else:
        comments = request.form.get('comments')
        stu_id = session.get('stu_id')
        sql = "select NAME from STUDENT where STU_NO = '%s'" % stu_id
        stu_name = query.query(sql)
        stu_name = stu_name[0][0]
        now = time.time()
        now = time.strftime('%Y-%m-%d', time.localtime(now))
        now = str(now)
        news_id = stu_name + now
        sql = "INSERT INTO NEWS(TOPIC, COMMENTS, COMMENTER, NEWS_ID, IS_FIRST) VALUES ('回复', '%s', '%s', '%s', '%s')" % (comments, stu_name, news_id,question)
        print(sql)
        query.update(sql)

        sql = "SELECT TOPIC, COMMENTS, COMMENTER, CREATE_TIME FROM NEWS WHERE NEWS_ID='%s' AND IS_FIRST='0'" % question
        title = query.query(sql)
        # print(title)
        title = title[0]
        sql = "SELECT * FROM NEWS WHERE IS_FIRST='%s'" % question
        result = query.query(sql)
        return render_template('detail.html', title=title, result=result)


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
def personal_information():
    """
    功能(个人中心界面): 根据"stu_id"从数据库中得到学生基本信息，用于个人中心信息显示
    :return:
    """
    stu_no = session.get('stu_id')
    print(stu_no + ' is stu_no')
    sql = "SELECT * FROM student WHERE STU_NO = '%s'" % stu_no
    result = query.query(sql)
    return render_template('personal_information.html', result=result)


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

    #train_plan['name'] = "数据转换成功"
    print('反馈回来的数据是：')
    print(train_plan)
    data = train_plan['children']
    array_finish = [0]*120
    #print(array_finish)
    for data_children in data:
        data_children = data_children['children']
        #print(data_children)
        for data_children_child_1 in data_children:
            #print('data_children_child', data_children_child)
            data_children_child_1 = data_children_child_1['children']
            for data_children_child in data_children_child_1:
                name = data_children_child['children'][0]['name']
                color = data_children_child['children'][0]['itemStyle']['borderColor']
                #print(name, color)
                sql = "select CO_100 from education_plan WHERE CO_NAME='%s'" % name
                co_100 = query.query(sql)
                co_100 = co_100[0][0]

                if color == 'red':
                    array_finish[int(co_100)] = 0
                else:
                    array_finish[int(co_100)] = 1
    finish_co = ''
    for i in range(1, 119):
        if array_finish[i] == 1:
            finish_co += '1'
        else:
            finish_co += '0'
    print(finish_co)
    #print(array_finish)

    stu_id = session.get('stu_id')
    query.updateDatabase(stu_id, train_plan)
    query.updateScore(stu_id, scores)

    """功能2："""
    train_plan_str = json.dumps(train_plan)
    train_plan_str = train_plan_str.replace("yellow", "green")
    train_plan = json.loads(train_plan_str)
    return jsonify(train_plan)


@app.route('/api/deepseek_chat', methods=['POST'])
def deepseek_chat():
    user_message = request.json.get("message", "")

    if not user_message:
        return jsonify({"error": "消息不能为空"}), 400

    # 读取 DeepSeek API KEY（你必须提前设置环境变量）
    api_key = os.environ.get('DEEPSEEK_API_KEY')
    if not api_key:
        return jsonify({"error": "未检测到 DEEPSEEK_API_KEY"}), 500

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )

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

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    
    return render_template('course_selection.html', 
                         available_courses=available_courses,
                         chosen_courses=chosen_courses)


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


if __name__ == '__main__':
    app.run("0.0.0.0", debug=True)

