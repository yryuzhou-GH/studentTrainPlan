# 学生培养计划可视化系统

一个集培养计划可视化、智能课程推荐、选课管理、AI助手、论坛讨论为一体的教学辅助平台，帮助学生掌握个人学业进度，也便于管理员集中维护学生数据。

## ✨ 功能概览

### 核心功能

- **📊 可视化培养计划树**：树形结构展示培养计划，实时统计学分完成情况
- **🎯 智能课程推荐**：基于协同过滤的动态推荐系统，个性化推荐专业选修课程
- **📚 选课中心**：学生可自主选择/退选专业选修课程，实时查看选课统计
- **🤖 AI 学习助手**：基于 DeepSeek API 的智能问答助手，解答学习问题
- **💬 课程论坛**：支持课程公告发布和课程讨论，促进学习交流
- **📈 课程进度管理**：可视化展示个人课程完成进度和学分统计
- **👤 个人中心**：查看和编辑个人基本信息
- **🔧 管理员功能**：维护学生基础信息、登录记录等

### 推荐系统特性

- **动态推荐**：每次推荐都重新加载最新选课数据，确保推荐结果实时更新
- **多策略融合**：
  - 协同过滤推荐（基于用户相似度）
  - 冷启动推荐（新同学基于专业的热门课程）
  - 热门课程推荐（回退策略）
- **相似学生推荐**：推荐志同道合的朋友，基于选课偏好相似度
- **专业匹配**：优先推荐学生专业相关的选修课程

> 📖 详细的推荐系统机制说明请查看 [课程推荐机制说明.md](./课程推荐机制说明.md)

## 🛠️ 技术栈

### 后端
- **Python 3.8+**
- **Flask 1.0+**：Web 框架
- **NumPy**：数值计算和矩阵运算
- **PyMySQL**：MySQL 数据库连接
- **OpenAI Client**：DeepSeek API 调用（AI 助手）

### 前端
- **HTML5 + CSS3 + JavaScript**
- **jQuery**：DOM 操作和 AJAX 请求
- **ECharts**：数据可视化图表（课程推荐、相似学生）
- **Bootstrap**：响应式 UI 框架（部分页面）

### 数据库
- **MySQL 5.7+**（必须使用 `utf8mb4` 字符集）

## 📦 安装依赖

```bash
pip install Flask numpy pymysql openai
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/gsolvit/studentTrainPlan.git
cd studentTrainPlan
```

### 2. 准备数据库

**重要**：必须使用 `utf8mb4` 字符集，防止中文插入报错。

```sql
mysql -u root -p
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

DROP DATABASE IF EXISTS studenttrainplan;
CREATE DATABASE studenttrainplan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE studenttrainplan;

SOURCE sql/schema.sql;
SOURCE sql/insert_student.sql;
SOURCE sql/insert_loginformation.sql;
SOURCE sql/insert_education_plan.sql;
SOURCE sql/insert_choose.sql;
SOURCE sql/insert_edu_stu_plan.sql;
```

> ⚠️ 如果遇到 `Data too long` 或 `Incorrect string value` 错误，请确认：
> 1. 已执行 `SET NAMES utf8mb4;` 和 `SET CHARACTER SET utf8mb4;`
> 2. SQL 文件保存为 UTF-8 编码
> 3. 数据库和表都使用 `utf8mb4` 字符集

### 3. 配置数据库连接

编辑 `config.py`：

```python
config = {
    'default': Config,
    'MYSQL_PASSWORD': '你的MySQL密码',  # 修改为你的MySQL密码
    'DATABASE_NAME': 'studenttrainplan'
}
```

### 4. 配置 AI 助手（可选）

如果需要使用 AI 助手功能，需要设置环境变量：

**Windows:**
```cmd
set DEEPSEEK_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export DEEPSEEK_API_KEY=your_api_key_here
```

> 💡 如果不使用 AI 助手功能，可以忽略此步骤，相关功能按钮将不可用。

### 5. 启动服务

```bash
python main.py
```

浏览器访问 [http://localhost:5000](http://localhost:5000) 即可。

## 👤 默认账号

| 角色 | 账号 | 密码 | 说明 |
| ---- | ---- | ---- | ---- |
| 管理员 | `admin` | `123456` | 拥有学生信息增删改权限 |
| 学生示例 | `3016216097` | `3016216097` | 其余学生账号密码均为学号 |

- **管理员登录**：跳转到 `/manager` 管理页面
- **学生登录**：进入首页，可访问个人中心、课程推荐、选课中心等模块

## 📁 项目结构

```
studentTrainPlan/
├── main.py                    # Flask 应用入口
├── config.py                  # 配置文件（数据库连接等）
├── errors.py                  # 错误处理
├── utils/                     # 工具模块
│   ├── query.py              # 数据库查询工具
│   ├── dynamic_recommend.py  # 动态课程推荐系统
│   ├── course_selection.py   # 选课功能模块
│   ├── recommed_module.py    # 旧版推荐模块（SVD算法，作为备用）
│   ├── map_student_course.py # 学生-课程映射工具
│   └── toJson.py             # JSON 转换工具
├── templates/                 # HTML 模板
│   ├── index.html            # 首页
│   ├── login.html            # 登录页
│   ├── recommed.html         # 课程推荐页
│   ├── course_selection.html # 选课中心页
│   ├── train_plan.html       # 课程进度页
│   ├── personal_information.html  # 个人中心
│   ├── news_center.html      # 课程公告
│   ├── course_discussion.html    # 课程讨论
│   └── ...
├── static/                    # 静态资源
│   ├── css/                  # 样式文件
│   ├── js/                   # JavaScript 文件
│   │   ├── recommedBar.js    # 推荐图表展示
│   │   └── ...
│   └── images/               # 图片资源
├── sql/                       # 数据库脚本
│   ├── schema.sql            # 数据库表结构
│   ├── insert_student.sql    # 学生数据
│   ├── insert_education_plan.sql  # 培养计划数据
│   ├── insert_choose.sql     # 选课数据
│   └── ...
├── 课程推荐机制说明.md        # 推荐系统详细说明文档
└── README.md                  # 本文件
```

## 🎯 主要功能模块

### 1. 课程推荐系统

**访问路径**：`/recommed`

**功能特点**：
- 基于协同过滤算法，根据学生选课历史推荐专业选修课程
- 动态更新：选课/退课后，推荐结果自动更新
- 相似学生推荐：推荐志同道合的朋友
- 支持刷新推荐，获取最新推荐结果

**推荐策略**：
- 选课历史充足（≥3门）：使用协同过滤推荐
- 选课历史不足（<3门）：使用冷启动推荐（基于专业的热门课程）
- 推荐失败时：回退到热门课程推荐

### 2. 选课中心

**访问路径**：`/course_selection`

**功能特点**：
- 查看可选的专业选修课程列表
- 查看已选的专业选修课程
- 选课/退课功能
- 实时显示课程容量和已选人数
- 选课成功后，推荐系统自动更新

### 3. AI 学习助手

**访问路径**：通过首页或导航栏访问

**功能特点**：
- 基于 DeepSeek API 的智能问答
- 支持学习相关问题咨询
- 实时对话交互

**配置要求**：需要设置 `DEEPSEEK_API_KEY` 环境变量

### 4. 课程进度

**访问路径**：`/train_plan`

**功能特点**：
- 树形结构展示培养计划
- 实时统计学分完成情况
- 可视化课程完成状态

### 5. 课程论坛

**访问路径**：`/news_center`（课程公告）、`/course_discussion`（课程讨论）

**功能特点**：
- 发布和查看课程公告
- 课程讨论区，支持发帖和回复
- 促进学习交流

## 🔧 常见问题

### 数据库相关

**Q: ERROR 1366 / 1406 错误？**

A: 99% 是字符集未设置为 `utf8mb4`。解决方法：
1. 重新执行 `SET NAMES utf8mb4;` 和 `SET CHARACTER SET utf8mb4;`
2. 确认数据库和表都使用 `utf8mb4` 字符集
3. 重新导入 SQL 文件

**Q: 无法连接数据库？**

A: 检查以下几点：
1. 确认 `config.py` 中的密码与本地 MySQL 一致
2. 确保 MySQL 服务已启动
3. 检查 MySQL 用户权限

### AI 助手相关

**Q: AI 助手报错？**

A: 
1. 确认已设置 `DEEPSEEK_API_KEY` 环境变量
2. 检查 API Key 是否有效
3. 如果不使用该功能，可以忽略相关错误

### 推荐系统相关

**Q: 推荐结果为空？**

A: 可能原因：
1. 学生已选完所有专业选修课程
2. 数据库中选课数据不足
3. 检查后端控制台的调试信息

**Q: 相似学生推荐都是 0.5？**

A: 这通常表示所有学生的相似度值相同。系统已优化，会综合考虑共同选课比例和评分相似度，提供更有区分度的推荐。

## 📚 相关文档

- [课程推荐机制说明.md](./课程推荐机制说明.md)：详细的推荐系统算法和机制说明

## 🚢 部署

可参考作者的 [CSDN 博客](https://blog.csdn.net/qq_40423339/article/details/86606308#commentsedit) 或自行将 Flask 应用部署到常见 PaaS / 服务器。

### 部署建议

- **开发环境**：直接运行 `python main.py`
- **生产环境**：建议使用 Gunicorn + Nginx
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 main:app
  ```

## 📸 界面预览

![主页](./exampleImage/index.png)
![课程进度](./exampleImage/plan.png)
![推荐](./exampleImage/recommend.png)
![课程论坛](./exampleImage/discuss.png)
![AI助手](./exampleImage/aiAssistant.png)

## 📝 更新日志

### v2.0 (最新)
- ✨ 新增选课中心功能，支持选课/退课
- 🎯 升级推荐系统为动态推荐（基于协同过滤）
- 🔄 推荐结果支持动态更新
- 👥 新增相似学生推荐功能
- 🐛 修复推荐系统相关问题
- 📚 完善文档说明

### v1.0
- 基础功能实现
- 培养计划可视化
- 基于 SVD 的课程推荐
- 课程论坛
- AI 助手

## 📄 许可证

本项目采用 MIT 许可证。

## 👥 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 GitHub Issue
- 参考 [CSDN 博客](https://blog.csdn.net/qq_40423339)

---

**⭐ 如果这个项目对你有帮助，欢迎 Star！**
