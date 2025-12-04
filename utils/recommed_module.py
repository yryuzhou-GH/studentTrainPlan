# 相似性度量函数， 输入列向量, 归一化 0-1
from numpy import *
import numpy as np
from numpy import linalg as la

def getSigK(Sigma, k):
    '''
    输入：
        Sigma： 输入的奇异值向量
        k: 取前几个奇异值
    输出：(k,k)的矩阵
    '''
    eyeK = np.eye(k)
    return mat(eyeK * Sigma[:k])
def reBuild(U, Sigma, VT, k):
    '''
    使用前k个特征值重构数据
    '''
    Sigk = getSigK(Sigma, k)
    # 左行右列
    return mat(np.dot(np.dot(U[:,:k], Sigk), VT[: k,:]))

def ecludSim(inA,inB):
    return 1.0/(1.0 + la.norm(inA - inB))

def cosSim(inA, inB):
    '''
    基于余弦相似性度量
    '''
    sim = float(inA.T* inB) / (la.norm(inA) * la.norm(inB))
    return 0.5 + 0.5 * sim

def svdMethod(svdData, dataMat, simMeas, user, item):
    '''
    输入：
        见recommend函数
    输出：
        Score(double): user对item的评分
    算法流程：
        1. for item_other in allItem
        2. if haveBeenScore(item_other)
        3.    compute_Simliar_Score(item, item_other)
        4. return Score
    '''
    N = shape(dataMat)[1]
    simTotal = 0.0
    ratSimTotal = 0.0
    U, Sigma, I_t = svdData
    k = 0
    while sum(Sigma[:k]) < sum(Sigma) * 0.9:
        k = k+ 1
    SigK = getSigK(Sigma, k)
    itemFeature = dataMat.T * U[:,:k] * SigK.I
    for j in range(N):
        if dataMat[user,j] == 0 or j == item:
            continue
        sim = simMeas(itemFeature[item,:].T, itemFeature[j,:].T)
        # print("the similarity between {} and {} is {}".format(j,item, sim))
        ratSim = dataMat[user, j] * sim
        simTotal += sim
        ratSimTotal += ratSim
    if simTotal == 0:
        return 0
    return ratSimTotal / simTotal

def recommedCoursePerson(dataMat, user, N=7, simMeas=ecludSim, estMethod=svdMethod):
    '''
    输入：
        dataMat(mat)(M,N): 评分矩阵.
        use(int): 想推荐的用户id.
        N(int): 为用户推荐的未评分的商品个数
        simMeas(double): 两个特征向量的相似度评价函数
        estMethod(double)：推荐核心方法，计算商品对于用户的分数的函数
    输出：
        N * (item, 评分)： N个商品以及其的评分
    算法流程：
        1. 找到所有未评分的商品
        2. 若没有未评分商品，退出
        3. 遍历未评分商品.
        4. 计算用户可能对该商品的评分
        5. 排序取前N个输出.
    '''
    print(user)
    dataMat = mat(dataMat)
    unRatedItems = nonzero(dataMat[user,:].A == 0)[1]
    if len(unRatedItems) == 0:
        print("没有未评分商品")
        return None
    U, Sigma, I_t = la.svd(dataMat)
    item_and_score = []
    for item in unRatedItems:
        score = estMethod([U, Sigma, I_t], dataMat, simMeas, user, item)
        item_and_score.append((item, score))

    k = 0
    while sum(Sigma[:k]) < sum(Sigma) * 0.9:
        k = k+ 1
    SigK = getSigK(Sigma, k)
    userFeature  = dataMat * I_t[:,:k] * SigK.I
    recomedUserVec = userFeature[user,:]
    user_and_score = []
    for idx, each in enumerate(userFeature):
        if user != idx:
            user_and_score.append((idx, cosSim(recomedUserVec.T, each.T)))
    recommedCourse = sorted(item_and_score, key=lambda k: k[1], reverse=True)[:min(N, len(item_and_score))]
    recommedPerson = sorted(user_and_score, key=lambda k: k[1], reverse=True)[:min(N, len(user_and_score))]
    print(recommedCourse)
    print(recommedPerson)
    return recommedCourse, recommedPerson


def toBarJson(data, dict2id):
    """
    将推荐结果转换为前端图表需要的JSON格式（兼容新系统格式）
    
    :param data: [(0, 5.0), (1, 5.0), (2, 5.0)] - (id, score) 元组列表
    :param dict2id: {0: "课程名", 1: "课程名"} - ID到名称的映射
    :return: {
        "source": [
            ["amount", "product"],  # 列名行（ECharts dataset必需）
            [2.3, "计算机视觉"],
            [1.1, "自然语言处理"],
            ...
        ]
     }
    """
    jsonData = {"source": []}
    # 添加列名行（ECharts dataset格式要求）
    jsonData['source'].append(["amount", "product"])
    
    # 添加数据行
    for each in data:
        item_id = each[0]  # ID
        score = each[1]    # 评分或相似度
        if item_id in dict2id:
            unit = [score, dict2id[item_id]]
            jsonData['source'].append(unit)
    return jsonData

def regularData(data, a, b):
    """
    功能：将列表的值归一化到[a,b]之间
    注意：第一行是列名 ["amount", "product"]，需要跳过
    """
    # 检查数据是否为空或只有列名
    if not data['source'] or len(data['source']) <= 1:
        return data
    
    # 跳过第一行列名，只处理数据行
    data_rows = data['source'][1:]
    if not data_rows:
        return data
    
    # 提取数值（每行的第一个元素）
    dataNum = []
    for row in data_rows:
        try:
            val = float(row[0])
            dataNum.append(val)
        except (ValueError, TypeError):
            continue
    
    if not dataNum:
        return data
    
    # 计算最大值和最小值
    Max, Min = max(dataNum), min(dataNum)
    
    # 如果所有值相同，设置为中间值
    if Max == Min:
        mid_value = (a + b) / 2
        for row in data_rows:
            try:
                float(row[0])  # 确认是数字
                row[0] = mid_value
            except (ValueError, TypeError):
                continue
        return data
    
    # 计算归一化系数
    k = (b - a) / (Max - Min)
    
    # 归一化
    dataRg = [a + k * (i - Min) for i in dataNum]
    
    # 更新数据行的值
    rg_idx = 0
    for row in data_rows:
        try:
            float(row[0])  # 确认是数字
            row[0] = dataRg[rg_idx]
            rg_idx += 1
        except (ValueError, TypeError):
            continue
    
    return data