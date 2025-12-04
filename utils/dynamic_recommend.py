"""
动态课程推荐系统
基于协同过滤算法，根据学生的选课历史、成绩、专业等信息动态推荐课程

主要功能：
1. 基于用户的协同过滤推荐（User-based Collaborative Filtering）
2. 冷启动处理：为新同学根据专业推荐热门课程
3. 动态数据加载：每次推荐都从数据库重新加载最新数据
4. 相似学生推荐：推荐志同道合的朋友

算法特点：
- 使用皮尔逊相关系数计算学生相似度
- 使用余弦相似度计算课程相似度
- 综合考虑成绩(GRADE)和评价(COMMENT)计算评分
- 支持冷启动场景，根据专业推荐热门课程
"""
import numpy as np
from collections import defaultdict
from utils.query import query
import math


class DynamicCourseRecommender:
    """
    动态课程推荐器
    
    该类实现了基于协同过滤的课程推荐系统，能够：
    1. 根据学生的选课历史和相似学生的行为推荐课程
    2. 处理新同学的冷启动问题（根据专业推荐热门课程）
    3. 推荐相似的学生（志同道合的朋友）
    
    属性:
        student_course_matrix: 学生-课程评分矩阵（已废弃，每次重新加载）
        course_student_matrix: 课程-学生矩阵（已废弃）
        student_similarity_cache: 学生相似度缓存，避免重复计算
        course_similarity_cache: 课程相似度缓存，避免重复计算
        last_update_time: 最后更新时间（预留，用于未来优化）
    """
    
    def __init__(self):
        """
        初始化推荐器
        
        初始化缓存字典，用于存储相似度计算结果，提高性能
        """
        self.student_course_matrix = None  # 预留，当前未使用
        self.course_student_matrix = None   # 预留，当前未使用
        self.student_similarity_cache = {}  # 学生相似度缓存 {(id1, id2): similarity}
        self.course_similarity_cache = {}   # 课程相似度缓存 {(id1, id2): similarity}
        self.last_update_time = None         # 预留，用于未来数据更新检测
        
    def _load_student_course_data(self):
        """
        从数据库加载学生-课程数据，构建评分矩阵
        
        该方法每次调用都会重新从数据库加载数据，确保推荐结果基于最新数据。
        这是实现"动态推荐"的关键：推荐结果会随着学生选课和评分的变化而更新。
        
        返回:
            tuple: (id_to_stu_no, id_to_course_no, score_matrix, stu_no_to_id)
                - id_to_stu_no: dict, 矩阵ID到(学生编号, 学生姓名)的映射
                - id_to_course_no: dict, 矩阵ID到(课程编号, 课程名称)的映射
                - score_matrix: numpy.ndarray, 学生-课程评分矩阵，shape=(学生数, 课程数)
                - stu_no_to_id: dict, 学生编号到矩阵ID的映射
        """
        # 步骤1: 获取所有学生信息（排除管理员账号）
        sql = "SELECT STU_NO, NAME, MAJOR, AD_YEAR FROM STUDENT WHERE STU_NO<>'admin'"
        students = query(sql)
        
        # 步骤2: 获取所有课程信息
        # 这里一次性把课程号、课程名、课程类别(必修/专业选修等)、所属专业都查出来
        sql = "SELECT CO_NO, CO_NAME, CLASSIFICATION, MAJOR FROM EDUCATION_PLAN"
        courses = query(sql)
        
        # 步骤3: 构建双向映射关系
        # 学生编号 -> 矩阵ID（用于快速查找）
        stu_no_to_id = {}
        # 矩阵ID -> (学生编号, 学生姓名)（用于结果返回）
        id_to_stu_no = {}
        # 课程编号 -> 矩阵ID（用于快速查找）
        course_no_to_id = {}
        # 矩阵ID -> (课程编号, 课程名称)（用于结果返回）
        id_to_course_no = {}
        
        # 建立学生映射：为每个学生分配一个矩阵索引
        for idx, (stu_no, name, major, ad_year) in enumerate(students):
            stu_no_to_id[stu_no] = idx
            id_to_stu_no[idx] = (stu_no, name)
        
        # 建立课程映射：为每门课程分配一个矩阵索引
        # 保存的信息为 (课程号, 课程名, 课程类别, 所属专业)
        for idx, (co_no, co_name, classification, major) in enumerate(courses):
            course_no_to_id[co_no] = idx
            id_to_course_no[idx] = (co_no, co_name, classification, major)
        
        # 步骤4: 初始化评分矩阵（全零矩阵）
        num_students = len(students)
        num_courses = len(courses)
        score_matrix = np.zeros((num_students, num_courses))
        
        # 步骤5: 从CHOOSE表加载选课和成绩数据，填充评分矩阵
        sql = """
            SELECT c.STU_NO, c.CO_NO, c.GRADE, c.COMMENT, 
                   s.MAJOR, s.AD_YEAR, e.CLASSIFICATION
            FROM CHOOSE c
            JOIN STUDENT s ON c.STU_NO = s.STU_NO
            JOIN EDUCATION_PLAN e ON c.CO_NO = e.CO_NO
            WHERE c.STU_NO <> 'admin'
        """
        choose_data = query(sql)
        
        # 遍历选课记录，计算并填充评分
        for row in choose_data:
            stu_no, co_no, grade, comment, major, ad_year, classification = row
            # 确保学生和课程都在映射中（数据一致性检查）
            if stu_no in stu_no_to_id and co_no in course_no_to_id:
                stu_idx = stu_no_to_id[stu_no]
                course_idx = course_no_to_id[co_no]
                
                # 计算综合评分：综合考虑成绩、评价等因素
                score = self._calculate_score(grade, comment, major, classification)
                score_matrix[stu_idx][course_idx] = score
        
        return (id_to_stu_no, id_to_course_no, score_matrix, stu_no_to_id)
    
    def _calculate_score(self, grade, comment, student_major, course_classification):
        """
        计算学生对课程的评分
        
        评分综合考虑多个因素：
        1. 成绩(GRADE)：反映学生对课程的掌握程度
        2. 评价(COMMENT)：反映学生对课程的满意度（0-5分）
        3. 专业匹配度：预留，当前未使用
        
        参数:
            grade: 课程成绩（数值型，通常0-100）
            comment: 课程评价（整数型，0-5分）
            student_major: 学生专业（预留，用于未来专业匹配度计算）
            course_classification: 课程分类（预留）
        
        返回:
            float: 综合评分，范围0-5分
        """
        score = 0.0
        
        # 因素1: 成绩因素（0-100分转换为0-3分）
        # 成绩越高，说明学生越喜欢或适合这门课程
        if grade is not None:
            try:
                grade_float = float(grade)
                if grade_float >= 90:      # 优秀：3.0分
                    score += 3.0
                elif grade_float >= 80:   # 良好：2.5分
                    score += 2.5
                elif grade_float >= 70:   # 中等：2.0分
                    score += 2.0
                elif grade_float >= 60:    # 及格：1.5分
                    score += 1.5
                else:                     # 不及格：1.0分
                    score += 1.0
            except (ValueError, TypeError):
                # 成绩格式错误，忽略
                pass
        
        # 因素2: 评价因素（COMMENT字段，0-5分转换为0-2分）
        # 学生的主观评价，反映对课程的满意度
        if comment is not None:
            try:
                comment_int = int(comment)
                # 线性映射：0-5分 -> 0-2分
                score += comment_int * 0.4
            except (ValueError, TypeError):
                # 评价格式错误，忽略
                pass
        
        # 因素3: 默认评分（如果没有任何数据）
        # 表示学生选过这门课，但未提供成绩或评价
        if score == 0:
            score = 2.0  # 中等偏好，表示选过但未明确评价
        
        # 限制评分范围在0-5分之间
        return min(score, 5.0)
    
    def _cosine_similarity(self, vec1, vec2):
        """
        计算两个向量的余弦相似度
        
        余弦相似度衡量两个向量的方向相似性，范围[-1, 1]。
        值越接近1，表示两个向量越相似。
        常用于计算课程相似度（基于选课模式）。
        
        公式: cos(θ) = (A·B) / (||A|| * ||B||)
        
        参数:
            vec1: numpy数组，第一个向量
            vec2: numpy数组，第二个向量
        
        返回:
            float: 余弦相似度，范围[-1, 1]
        """
        # 计算向量点积
        dot_product = np.dot(vec1, vec2)
        # 计算向量的L2范数（模长）
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        # 如果任一向量为零向量，相似度为0
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # 返回余弦相似度
        return dot_product / (norm1 * norm2)
    
    def _pearson_correlation(self, vec1, vec2):
        """
        计算两个向量的皮尔逊相关系数
        
        皮尔逊相关系数衡量两个向量的线性相关性，范围[-1, 1]。
        相比余弦相似度，皮尔逊相关系数考虑了向量的均值偏移，
        更适合计算学生相似度（因为不同学生的评分基准可能不同）。
        
        公式: r = Σ((x-μx)(y-μy)) / sqrt(Σ(x-μx)² * Σ(y-μy)²)
        
        参数:
            vec1: numpy数组，第一个向量（通常是学生的选课评分向量）
            vec2: numpy数组，第二个向量
        
        返回:
            float: 皮尔逊相关系数，范围[-1, 1]
        """
        # 步骤1: 找到两个向量都非零的位置（共同评分项）
        # 只考虑学生都选过的课程，忽略未选课程
        mask = (vec1 != 0) & (vec2 != 0)
        common_count = np.sum(mask)
        
        # 如果共同评分项少于2个，无法计算相关性
        if common_count < 2:
            # 如果共同选课数为1，返回一个很小的正数（0.1），表示有轻微相似
            if common_count == 1:
                return 0.1
            return 0.0
        
        # 步骤2: 提取共同评分项
        vec1_masked = vec1[mask]
        vec2_masked = vec2[mask]
        
        # 步骤3: 计算均值（中心化）
        mean1 = np.mean(vec1_masked)
        mean2 = np.mean(vec2_masked)
        
        # 步骤4: 计算协方差（分子）
        numerator = np.sum((vec1_masked - mean1) * (vec2_masked - mean2))
        
        # 步骤5: 计算标准差乘积（分母）
        denominator = np.sqrt(
            np.sum((vec1_masked - mean1) ** 2) * 
            np.sum((vec2_masked - mean2) ** 2)
        )
        
        # 如果分母为0（标准差为0），返回0
        if denominator == 0:
            return 0.0
        
        # 步骤6: 返回皮尔逊相关系数
        return numerator / denominator
    
    def _get_student_similarity(self, student_id1, student_id2, score_matrix):
        """
        计算两个学生的相似度（带缓存）
        
        使用皮尔逊相关系数计算学生相似度，并缓存结果以提高性能。
        相似度越高，说明两个学生的选课偏好越相似。
        
        参数:
            student_id1: int, 第一个学生的矩阵ID
            student_id2: int, 第二个学生的矩阵ID
            score_matrix: numpy.ndarray, 学生-课程评分矩阵
        
        返回:
            float: 学生相似度，范围[-1, 1]，值越大越相似
        """
        # 使用有序的元组作为缓存键（避免重复计算）
        cache_key = (min(student_id1, student_id2), max(student_id1, student_id2))
        
        # 检查缓存，如果已计算过则直接返回
        if cache_key in self.student_similarity_cache:
            return self.student_similarity_cache[cache_key]
        
        # 获取两个学生的评分向量
        vec1 = score_matrix[student_id1]  # 学生1对所有课程的评分
        vec2 = score_matrix[student_id2]  # 学生2对所有课程的评分
        
        # 使用皮尔逊相关系数计算相似度
        # 皮尔逊相关系数考虑了评分基准的差异，更适合学生相似度计算
        similarity = self._pearson_correlation(vec1, vec2)
        
        # 缓存结果，避免重复计算
        self.student_similarity_cache[cache_key] = similarity
        return similarity
    
    def _get_course_similarity(self, course_id1, course_id2, score_matrix):
        """
        计算两个课程的相似度（带缓存）
        
        使用余弦相似度计算课程相似度，并缓存结果以提高性能。
        相似度越高，说明两门课程的选课模式越相似（被相似的学生选择）。
        
        参数:
            course_id1: int, 第一门课程的矩阵ID
            course_id2: int, 第二门课程的矩阵ID
            score_matrix: numpy.ndarray, 学生-课程评分矩阵
        
        返回:
            float: 课程相似度，范围[-1, 1]，值越大越相似
        """
        # 使用有序的元组作为缓存键（避免重复计算）
        cache_key = (min(course_id1, course_id2), max(course_id1, course_id2))
        
        # 检查缓存，如果已计算过则直接返回
        if cache_key in self.course_similarity_cache:
            return self.course_similarity_cache[cache_key]
        
        # 获取两门课程的评分向量（所有学生对该课程的评分）
        vec1 = score_matrix[:, course_id1]  # 所有学生对课程1的评分
        vec2 = score_matrix[:, course_id2]  # 所有学生对课程2的评分
        
        # 使用余弦相似度计算相似度
        # 余弦相似度适合计算课程相似度（基于选课模式）
        similarity = self._cosine_similarity(vec1, vec2)
        
        # 缓存结果，避免重复计算
        self.course_similarity_cache[cache_key] = similarity
        return similarity
    
    def _cold_start_recommend(self, stu_no, student_major, id_to_course_no, score_matrix, unrated_courses, top_n=20):
        """
        冷启动推荐：为新同学推荐该专业下的热门课程
        
        当学生选课历史不足（冷启动问题）时，无法使用协同过滤算法。
        此时采用基于专业的热门课程推荐策略：
        1. 优先推荐学生专业下的热门课程（选课人数多）
        2. 如果专业课程不足，补充其他热门课程
        3. 即使没有选课数据，也会推荐所有可用的专业选修课程
        
        参数:
            stu_no: str, 学生编号
            student_major: str, 学生专业
            id_to_course_no: dict, 课程ID到(课程编号, 课程名称)的映射
            score_matrix: numpy.ndarray, 学生-课程评分矩阵
            unrated_courses: numpy.ndarray, 学生未选过的课程ID列表
            top_n: int, 推荐课程数量，默认20门
        
        返回:
            tuple: (推荐课程列表, 课程映射)
                - 推荐课程列表: list of (course_id, score) 元组，按评分降序排列
                - 课程映射: dict, 课程ID到课程信息的映射
        """
        print(f"检测到冷启动情况，为学生 {stu_no} (专业: {student_major}) 推荐热门课程")
        
        # 步骤1: 查询该专业下的所有课程
        # 注意：也包含通用课程（MAJOR为空或NULL的课程）
        sql = f"""
            SELECT CO_NO, CO_NAME 
            FROM EDUCATION_PLAN 
            WHERE MAJOR = '{student_major}' OR MAJOR = '' OR MAJOR IS NULL
        """
        major_courses = query(sql)
        
        # 步骤2: 构建专业课程编号集合（用于快速判断课程是否属于该专业）
        major_course_nos = {row[0] for row in major_courses} if major_courses else set()
        
        # 步骤3: 筛选所有未选的专业选修课程
        prof_elective_candidates = []
        for course_id in unrated_courses:
            if course_id in id_to_course_no:
                co_no, co_name, classification, major = id_to_course_no[course_id]
                
                # 只考虑"专业选修"类课程（包含"专业选修-XXX"这类前缀）
                if classification and str(classification).startswith("专业选修"):
                    # 统计选过这门课的学生数量（评分矩阵中非零元素的数量）
                    students_count = np.sum(score_matrix[:, course_id] > 0)
                    is_major_course = co_no in major_course_nos
                    
                    prof_elective_candidates.append({
                        'course_id': course_id,
                        'co_no': co_no,
                        'co_name': co_name,
                        'students_count': students_count,
                        'is_major_course': is_major_course
                    })
        
        print(f"调试信息 - 冷启动推荐: 找到 {len(prof_elective_candidates)} 门专业选修候选课程")
        
        # 如果没有找到任何专业选修课程，尝试推荐所有未选课程（放宽限制）
        if not prof_elective_candidates:
            print(f"警告: 未找到专业选修课程，尝试推荐所有未选课程")
            for course_id in unrated_courses:
                if course_id in id_to_course_no:
                    co_no, co_name, classification, major = id_to_course_no[course_id]
                    # 排除必修课程，只推荐选修类课程
                    if classification and ("选修" in str(classification) or "任选" in str(classification)):
                        students_count = np.sum(score_matrix[:, course_id] > 0)
                        is_major_course = co_no in major_course_nos
                        prof_elective_candidates.append({
                            'course_id': course_id,
                            'co_no': co_no,
                            'co_name': co_name,
                            'students_count': students_count,
                            'is_major_course': is_major_course
                        })
        
        # 步骤4: 将课程分为两类：专业课程和其他课程
        major_course_scores = []  # 专业课程列表
        other_course_scores = []  # 其他课程列表
        
        for candidate in prof_elective_candidates:
            # 热度评分 = 选课人数（基础热度）+ 基础分（确保即使没有选课数据也有评分）
            popularity_score = float(candidate['students_count']) + 1.0  # 加1分基础分，避免0分
            
            if candidate['is_major_course']:
                # 专业课程额外加分（+10分），提高专业课程优先级
                popularity_score += 10.0
                major_course_scores.append((candidate['course_id'], popularity_score))
            else:
                # 非专业课程，仅使用基础热度
                other_course_scores.append((candidate['course_id'], popularity_score))
        
        # 步骤5: 分别对两类课程按热度排序（降序）
        major_course_scores.sort(key=lambda x: x[1], reverse=True)
        other_course_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 步骤6: 组合推荐结果
        # 优先推荐专业课程，如果专业课程不足top_n门，则补充其他热门课程
        recommended_courses = major_course_scores[:top_n]
        if len(recommended_courses) < top_n:
            remaining = top_n - len(recommended_courses)
            recommended_courses.extend(other_course_scores[:remaining])
        
        print(f"冷启动推荐完成：找到 {len(prof_elective_candidates)} 门候选课程，专业课程 {len(major_course_scores)} 门，其他课程 {len(other_course_scores)} 门，共推荐 {len(recommended_courses)} 门")
        
        # 如果还是没有推荐结果，至少返回前top_n门专业选修课程（即使没有热度数据）
        if not recommended_courses and prof_elective_candidates:
            print(f"警告: 没有热度数据，直接推荐前 {min(top_n, len(prof_elective_candidates))} 门专业选修课程")
            for i, candidate in enumerate(prof_elective_candidates[:top_n]):
                score = 10.0 if candidate['is_major_course'] else 5.0
                recommended_courses.append((candidate['course_id'], score))
        
        return recommended_courses, id_to_course_no
    
    def _get_student_major(self, stu_no):
        """
        获取学生的专业信息
        
        参数:
            stu_no: str, 学生编号
        
        返回:
            str or None: 学生专业名称，如果查询失败返回None
        """
        sql = f"SELECT MAJOR FROM STUDENT WHERE STU_NO = '{stu_no}'"
        result = query(sql)
        if result and len(result) > 0:
            return result[0][0]
        return None
    
    def _is_cold_start(self, student_vector, min_courses=3):
        """
        判断是否为冷启动情况
        
        冷启动问题：当学生选课历史不足时，无法使用协同过滤算法进行推荐。
        判断标准：如果学生选课数量少于min_courses门，认为是冷启动。
        
        参数:
            student_vector: numpy.ndarray, 学生的选课评分向量（一行）
            min_courses: int, 判断冷启动的最小选课数量，默认3门
        
        返回:
            bool: True表示是冷启动，False表示不是
        """
        # 统计学生已选课程数量（评分向量中非零元素的数量）
        selected_count = np.sum(student_vector > 0)
        return selected_count < min_courses
    
    def recommend_courses(self, stu_no, top_n=20):
        """
        为学生推荐课程
        
        这是推荐系统的核心方法，采用多种策略：
        1. 冷启动推荐：如果学生选课历史不足，使用基于专业的热门课程推荐
        2. 协同过滤推荐：如果数据充足，使用基于用户的协同过滤算法
        3. 热门课程推荐：如果协同过滤失败，回退到热门课程推荐
        
        算法流程（协同过滤）：
        1. 找到与目标学生相似的其他学生
        2. 对于每门未选课程，计算加权平均评分
        3. 权重 = 学生相似度，评分 = 相似学生对课程的评分
        4. 预测评分 = Σ(相似度 × 评分) / Σ|相似度|
        
        参数:
            stu_no: str, 学生编号
            top_n: int, 推荐课程数量，默认20门
        
        返回:
            tuple: (推荐课程列表, 课程映射)
                - 推荐课程列表: list of (course_id, predicted_score) 元组
                - 课程映射: dict, 课程ID到课程信息的映射
        """
        # 步骤1: 重新加载数据（确保数据是最新的，实现动态推荐）
        id_to_stu_no, id_to_course_no, score_matrix, stu_no_to_id = self._load_student_course_data()
        
        # 步骤2: 数据验证
        if stu_no not in stu_no_to_id:
            print(f"警告: 学生 {stu_no} 不在学生列表中")
            return [], id_to_course_no
        
        if len(id_to_course_no) == 0:
            print("警告: 数据库中没有课程数据")
            return [], id_to_course_no
        
        # 步骤3: 获取学生的评分向量
        student_id = stu_no_to_id[stu_no]
        student_vector = score_matrix[student_id]
        
        # 步骤4: 找到未选过的课程（评分为0的课程）
        # 注意：这里只考虑"专业选修"类课程，而不是所有课程
        # 因为学生可能已经选完了所有必修课程，但还有专业选修课程可选
        all_unrated_courses = np.where(student_vector == 0)[0]
        
        # 筛选出未选的专业选修课程
        unrated_prof_elective = []
        for course_id in all_unrated_courses:
            if course_id in id_to_course_no:
                _, _, classification, _ = id_to_course_no[course_id]
                if classification and str(classification).startswith("专业选修"):
                    unrated_prof_elective.append(course_id)
        
        # 如果找不到专业选修课程，再考虑所有未选课程
        if len(unrated_prof_elective) > 0:
            unrated_courses = np.array(unrated_prof_elective)
            print(f"调试信息 - 学生 {stu_no}: 总课程数={len(id_to_course_no)}, 已选课程数={np.sum(student_vector > 0)}, 未选专业选修课程数={len(unrated_courses)}")
        else:
            unrated_courses = all_unrated_courses
            print(f"调试信息 - 学生 {stu_no}: 总课程数={len(id_to_course_no)}, 已选课程数={np.sum(student_vector > 0)}, 未选课程数={len(unrated_courses)} (未找到专业选修课程，使用所有未选课程)")
        
        if len(unrated_courses) == 0:
            print(f"警告: 学生 {stu_no} 已选完所有可推荐课程（专业选修课程），无法推荐")
            return [], id_to_course_no
        
        # 调试：统计未选课程中专业选修课程的数量
        prof_elective_count = 0
        for course_id in unrated_courses:
            if course_id in id_to_course_no:
                _, _, classification, _ = id_to_course_no[course_id]
                if classification and str(classification).startswith("专业选修"):
                    prof_elective_count += 1
        print(f"调试信息 - 未选课程中专业选修课程数量: {prof_elective_count}")
        
        # 步骤5: 检查是否为冷启动情况
        if self._is_cold_start(student_vector, min_courses=3):
            # 获取学生专业
            student_major = self._get_student_major(stu_no)
            if student_major:
                # 使用冷启动推荐（基于专业的热门课程）
                return self._cold_start_recommend(
                    stu_no, student_major, id_to_course_no, score_matrix, 
                    unrated_courses, top_n
                )
            else:
                print(f"警告: 无法获取学生 {stu_no} 的专业信息，使用通用热门课程推荐")
                # 如果没有专业信息，使用通用热门课程推荐
                course_popularity = np.sum(score_matrix > 0, axis=0)
                popular_courses = [(idx, float(course_popularity[idx])) for idx in unrated_courses if course_popularity[idx] > 0]
                popular_courses.sort(key=lambda x: x[1], reverse=True)
                return popular_courses[:top_n], id_to_course_no
        
        # 步骤6: 检查是否有足够的学生进行协同过滤（至少需要2个学生）
        total_students = len(id_to_stu_no)
        if total_students < 2:
            print("警告: 数据库中只有1个学生，使用热门课程推荐")
            # 获取学生专业，优先推荐专业课程
            student_major = self._get_student_major(stu_no)
            if student_major:
                return self._cold_start_recommend(
                    stu_no, student_major, id_to_course_no, score_matrix, 
                    unrated_courses, top_n
                )
            else:
                # 返回热门课程（选课人数最多的课程）
                course_popularity = np.sum(score_matrix > 0, axis=0)
                popular_courses = [(idx, float(course_popularity[idx])) for idx in unrated_courses if course_popularity[idx] > 0]
                popular_courses.sort(key=lambda x: x[1], reverse=True)
                return popular_courses[:top_n], id_to_course_no
        
        # 步骤7: 筛选所有"专业选修"类课程
        prof_elective_courses = []
        for course_id in unrated_courses:
            if course_id in id_to_course_no:
                co_no, co_name, classification, major = id_to_course_no[course_id]
                # 只推荐"专业选修"类课程（包含"专业选修-XXX"这类前缀）
                if classification and str(classification).startswith("专业选修"):
                    prof_elective_courses.append(course_id)
                    print(f"调试信息 - 找到专业选修课程: {co_name} (分类: {classification})")

        print(f"调试信息 - 筛选到的专业选修课程数量: {len(prof_elective_courses)}")

        if not prof_elective_courses:
            # 如果在未选课程中找不到任何"专业选修"课程，则回退到冷启动推荐
            print(f"警告: 学生 {stu_no} 未找到可推荐的专业选修课程，回退到冷启动推荐")
            student_major = self._get_student_major(stu_no)
            if student_major:
                return self._cold_start_recommend(
                    stu_no, student_major, id_to_course_no, score_matrix,
                    unrated_courses, top_n
                )
            else:
                # 如果没有专业信息，尝试推荐所有包含"选修"或"任选"的课程
                print(f"警告: 无法获取学生专业，尝试推荐所有选修类课程")
                elective_courses = []
                for course_id in unrated_courses:
                    if course_id in id_to_course_no:
                        _, _, classification, _ = id_to_course_no[course_id]
                        if classification and ("选修" in str(classification) or "任选" in str(classification)):
                            students_count = np.sum(score_matrix[:, course_id] > 0)
                            elective_courses.append((course_id, float(students_count) + 1.0))
                
                if elective_courses:
                    elective_courses.sort(key=lambda x: x[1], reverse=True)
                    return elective_courses[:top_n], id_to_course_no
                else:
                    # 最后的回退：返回空列表
                    print(f"警告: 无法找到任何可推荐的选修课程")
                    return [], id_to_course_no

        course_scores = []
        for course_id in prof_elective_courses:
            # 找到选过这门课的所有学生
            students_who_took = np.where(score_matrix[:, course_id] > 0)[0]
            
            # 如果没有人选过这门课，给一个默认评分（基于课程基本信息）
            if len(students_who_took) == 0:
                # 给新课程一个基础评分（3.0分），确保它们能被推荐
                course_scores.append((course_id, 3.0))
                continue
            
            # 计算加权平均评分（基于学生相似度）
            weighted_sum = 0.0  # 加权评分总和
            similarity_sum = 0.0  # 相似度总和（用于归一化）
            
            for other_student_id in students_who_took:
                if other_student_id == student_id:
                    continue  # 跳过自己
                
                # 计算与目标学生的相似度
                similarity = self._get_student_similarity(student_id, other_student_id, score_matrix)
                
                if similarity > 0:  # 只考虑正相似度
                    # 获取该学生对课程的评分
                    rating = score_matrix[other_student_id][course_id]
                    # 加权累加：相似度越高，权重越大
                    weighted_sum += similarity * rating
                    similarity_sum += abs(similarity)
            
            # 计算预测评分
            if similarity_sum > 0:
                # 预测评分 = 加权平均
                predicted_score = weighted_sum / similarity_sum
                course_scores.append((course_id, predicted_score))
            else:
                # 如果没有相似学生（相似度都为0或负），使用所有选课学生的平均分
                avg_rating = np.mean(score_matrix[students_who_took, course_id])
                if avg_rating > 0:
                    course_scores.append((course_id, avg_rating))
        
        # 步骤8: 按预测评分排序，取前N个
        course_scores.sort(key=lambda x: x[1], reverse=True)
        top_courses = course_scores[:top_n]
        
        # 步骤9: 如果协同过滤失败（没有推荐结果），回退到冷启动推荐
        if len(top_courses) == 0:
            print(f"警告: 无法为学生 {stu_no} 生成协同过滤推荐，切换到冷启动推荐")
            # 如果协同过滤失败，使用冷启动推荐
            student_major = self._get_student_major(stu_no)
            if student_major:
                return self._cold_start_recommend(
                    stu_no, student_major, id_to_course_no, score_matrix, 
                    unrated_courses, top_n
                )
            else:
                # 使用通用热门课程推荐
                course_popularity = np.sum(score_matrix > 0, axis=0)
                popular_courses = [(idx, float(course_popularity[idx])) for idx in unrated_courses if course_popularity[idx] > 0]
                popular_courses.sort(key=lambda x: x[1], reverse=True)
                return popular_courses[:top_n], id_to_course_no
        
        print(f"调试信息 - 协同过滤推荐成功，返回 {len(top_courses)} 门课程")
        return top_courses, id_to_course_no
    
    def recommend_similar_students(self, stu_no, top_n=20):
        """
        推荐相似的学生（志同道合的朋友）
        
        使用基于用户的协同过滤算法，通过计算选课偏好的相似度来推荐相似学生。
        相似度越高，说明两个学生的选课偏好越相似，可能是志同道合的朋友。
        
        参数:
            stu_no: str, 学生编号
            top_n: int, 推荐学生数量，默认20人
        
        返回:
            tuple: (推荐学生列表, 学生映射)
                - 推荐学生列表: list of (student_id, similarity) 元组，按相似度降序排列
                - 学生映射: dict, 学生ID到学生信息的映射
        """
        # 重新加载数据（确保使用最新数据）
        id_to_stu_no, id_to_course_no, score_matrix, stu_no_to_id = self._load_student_course_data()
        
        if stu_no not in stu_no_to_id:
            return [], id_to_stu_no
        
        # 获取目标学生的ID和评分向量
        student_id = stu_no_to_id[stu_no]
        student_vector = score_matrix[student_id]
        
        # 计算与所有其他学生的相似度
        student_similarities = []
        for other_student_id in range(len(id_to_stu_no)):
            if other_student_id == student_id:
                continue  # 跳过自己
            
            # 计算相似度（使用皮尔逊相关系数）
            similarity = self._get_student_similarity(student_id, other_student_id, score_matrix)
            
            # 只保留正相似度（相似度 > 0）
            if similarity > 0:
                student_similarities.append((other_student_id, similarity))
        
        print(f"调试信息 - 相似学生推荐: 找到 {len(student_similarities)} 个正相似度的学生")
        
        # 如果没有找到正相似度的学生，使用备选策略
        if len(student_similarities) == 0:
            print("警告: 没有找到正相似度的学生，使用备选策略（基于共同选课数量和评分相似度）")
            # 备选策略：综合考虑共同选课数量和评分相似度
            for other_student_id in range(len(id_to_stu_no)):
                if other_student_id == student_id:
                    continue
                
                other_student_vector = score_matrix[other_student_id]
                # 计算共同选课数量
                common_courses = np.sum((student_vector > 0) & (other_student_vector > 0))
                
                if common_courses > 0:
                    # 计算共同选课比例（基础相似度）
                    max_common = min(np.sum(student_vector > 0), np.sum(other_student_vector > 0))
                    if max_common > 0:
                        common_ratio = float(common_courses) / max_common
                        
                        # 计算共同选课的平均评分差异（评分相似度）
                        # 如果评分差异小，说明选课偏好相似
                        common_mask = (student_vector > 0) & (other_student_vector > 0)
                        if np.sum(common_mask) > 0:
                            common_scores_stu = student_vector[common_mask]
                            common_scores_other = other_student_vector[common_mask]
                            # 计算平均绝对误差（MAE），然后转换为相似度
                            mae = np.mean(np.abs(common_scores_stu - common_scores_other))
                            # MAE越小，相似度越高；将MAE映射到0-1（假设最大MAE为5）
                            score_similarity = max(0, 1.0 - mae / 5.0)
                        else:
                            score_similarity = 0.5  # 默认值
                        
                        # 综合相似度 = 共同选课比例 * 0.6 + 评分相似度 * 0.4
                        # 这样即使所有学生都选了所有课程，也能根据评分差异区分
                        similarity_score = common_ratio * 0.6 + score_similarity * 0.4
                        student_similarities.append((other_student_id, similarity_score))
                        
                        print(f"调试 - 学生{other_student_id}: 共同选课比例={common_ratio:.3f}, 评分相似度={score_similarity:.3f}, 综合相似度={similarity_score:.3f}")
        
        # 按相似度排序（降序），取前N个
        student_similarities.sort(key=lambda x: x[1], reverse=True)
        top_students = student_similarities[:top_n]
        
        print(f"调试信息 - 相似学生推荐: 最终返回 {len(top_students)} 个学生")
        
        return top_students, id_to_stu_no
    
    def get_recommendations(self, stu_no, top_n_courses=20, top_n_students=20):
        """
        获取推荐结果（课程和相似学生）
        
        这是推荐系统的主入口方法，返回课程推荐和相似学生推荐。
        返回格式与原有接口兼容，可以直接替换原有的推荐系统。
        
        参数:
            stu_no: str, 学生编号
            top_n_courses: int, 推荐课程数量，默认20门
            top_n_students: int, 推荐相似学生数量，默认20人
        
        返回:
            tuple: (课程推荐列表, 学生推荐列表, 课程ID映射, 学生ID映射)
                - 课程推荐列表: list of (course_id, score) 元组
                - 学生推荐列表: list of (student_id, similarity) 元组
                - 课程ID映射: dict, 课程ID到课程名称的映射
                - 学生ID映射: dict, 学生ID到学生名称的映射
        """
        # 清空缓存，确保使用最新数据（每次调用都重新计算）
        self.student_similarity_cache = {}
        self.course_similarity_cache = {}
        
        # 推荐课程（使用协同过滤或冷启动推荐）
        top_courses, id_to_course_no = self.recommend_courses(stu_no, top_n_courses)
        
        # 推荐相似学生（使用协同过滤）
        top_students, id_to_stu_no = self.recommend_similar_students(stu_no, top_n_students)
        
        # 转换为原有格式（保持接口兼容性）
        course_list = [(course_id, score) for course_id, score in top_courses]
        student_list = [(stu_id, similarity) for stu_id, similarity in top_students]
        
        # 构建ID到名称的映射（兼容原有格式）
        # 原有格式：{id: name}，这里从(id, name)元组中提取name
        # 注意：只包含推荐结果中的ID，确保映射完整
        id2course = {}
        for course_id, _ in top_courses:
            if course_id in id_to_course_no:
                id2course[course_id] = id_to_course_no[course_id][1]
        
        id2student = {}
        for stu_id, _ in top_students:
            if stu_id in id_to_stu_no:
                id2student[stu_id] = id_to_stu_no[stu_id][1]
        
        # 如果映射为空，至少包含所有可能的ID（用于调试）
        if not id2course and id_to_course_no:
            id2course = {idx: id_to_course_no[idx][1] for idx in id_to_course_no.keys()}
        if not id2student and id_to_stu_no:
            id2student = {idx: id_to_stu_no[idx][1] for idx in id_to_stu_no.keys()}
        
        print(f"ID映射 - 课程映射数量: {len(id2course)}, 学生映射数量: {len(id2student)}")
        print(f"课程列表: {course_list[:3] if course_list else '无'}")
        print(f"学生列表: {student_list[:3] if student_list else '无'}")
        
        return course_list, student_list, id2course, id2student


def to_bar_json(data, dict2id):
    """
    将推荐结果转换为前端图表需要的JSON格式
    
    该函数将推荐结果转换为ECharts图表库需要的dataset格式。
    ECharts的dataset要求第一行是列名，后续行是数据。
    
    参数:
        data: list, 推荐结果列表，格式为 [(id, score), ...]
        dict2id: dict, ID到名称的映射，格式为 {id: name}
    
    返回:
        dict: ECharts dataset格式的数据
            格式: {"source": [["amount", "product"], [score, name], ...]}
            - 第一行: 列名 ["amount", "product"]
            - 后续行: 数据 [score, name]
    
    示例:
        >>> data = [(0, 4.5), (1, 3.2)]
        >>> dict2id = {0: "课程A", 1: "课程B"}
        >>> result = to_bar_json(data, dict2id)
        >>> result
        {"source": [["amount", "product"], [4.5, "课程A"], [3.2, "课程B"]]}
    """
    json_data = {"source": []}
    # 添加列名（ECharts dataset必需的第一行）
    # "amount" 表示数值（评分/相似度），"product" 表示名称（课程名/学生名）
    json_data['source'].append(["amount", "product"])
    
    # 遍历推荐结果，转换为数据行
    for each in data:
        course_or_student_id = each[0]  # ID
        score_or_similarity = each[1]   # 评分或相似度
        
        # 如果ID在映射中，添加数据行
        if course_or_student_id in dict2id:
            unit = [score_or_similarity, dict2id[course_or_student_id]]
            json_data['source'].append(unit)
    
    return json_data


def regular_data(data, a, b):
    """
    将列表的值归一化到指定范围[a, b]之间
    
    该函数用于将推荐结果的评分或相似度归一化到指定范围，
    以便在前端图表中更好地展示（例如：课程评分归一化到1-5，学生相似度归一化到0-1）。
    
    注意：第一行是列名，需要跳过，只处理数据行。
    
    参数:
        data: dict, 包含"source"键的字典，格式为 {"source": [[列名], [数据行], ...]}
        a: float, 归一化后的最小值
        b: float, 归一化后的最大值
    
    返回:
        dict: 归一化后的数据（原地修改）
    
    算法:
        线性归一化公式: new_value = a + (b - a) * (value - min) / (max - min)
    
    示例:
        >>> data = {"source": [["amount", "product"], [10, "A"], [20, "B"], [30, "C"]]}
        >>> regular_data(data, 1, 5)
        >>> data["source"]
        [["amount", "product"], [1.0, "A"], [3.0, "B"], [5.0, "C"]]
    """
    # 数据验证：如果没有数据或只有列名，直接返回
    if not data['source'] or len(data['source']) <= 1:
        return data
    
    # 跳过第一行列名，只处理数据行
    data_rows = data['source'][1:]
    if not data_rows:
        return data
    
    # 步骤1: 提取数值（每行的第一个元素是数值）
    data_num = []
    for row in data_rows:
        try:
            val = float(row[0])
            data_num.append(val)
        except (ValueError, TypeError):
            # 如果转换失败，跳过该行
            continue
    
    # 如果没有有效数值，直接返回
    if not data_num:
        return data
    
    # 步骤2: 找到最大值和最小值
    max_val, min_val = max(data_num), min(data_num)
    
    # 步骤3: 特殊情况处理：如果所有值相同，设置为中间值
    if max_val == min_val:
        mid_value = (a + b) / 2
        for row in data_rows:
            try:
                float(row[0])  # 确认是数字
                row[0] = mid_value
            except (ValueError, TypeError):
                continue
        return data
    
    # 步骤4: 计算归一化系数
    # k = (b - a) / (max - min)，用于线性映射
    k = (b - a) / (max_val - min_val)
    
    # 步骤5: 计算归一化后的值
    data_rg = [a + k * (i - min_val) for i in data_num]
    
    # 步骤6: 更新数据行的值
    rg_idx = 0
    for row in data_rows:
        try:
            float(row[0])  # 确认是数字
            row[0] = data_rg[rg_idx]
            rg_idx += 1
        except (ValueError, TypeError):
            # 如果转换失败，跳过该行
            continue
    
    return data

