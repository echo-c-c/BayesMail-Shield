# BayesMail Shield

# 垃圾邮件贝叶斯分类系统

这是一个基于机器学习的垃圾邮件分类系统，使用贝叶斯分类算法实现邮件的智能分类。系统提供了完整的邮件管理功能，包括用户注册、登录、发送邮件、接收邮件，以及自动的垃圾邮件识别。

## 功能特点

- 用户认证系统
  - 用户注册和登录
  - 基于 session 的身份验证
  - 管理员权限支持

- 邮件管理
  - 发送和接收邮件
  - 查看收件箱、已发送邮件和垃圾邮件
  - 邮件详情查看

- 垃圾邮件分类
  - 基于朴素贝叶斯算法的邮件分类
  - 使用 TF-IDF 特征提取
  - 中文分词处理（基于结巴分词）

## 技术栈

- 后端：Flask (Python)
- 数据库：MySQL
- 机器学习：
  - scikit-learn
  - 自定义实现的 TF-IDF 向量化
  - 朴素贝叶斯分类器
- 前端：支持 RESTful API 接口

## 项目结构

```
├── app.py              # Flask 主应用程序
├── predict.py          # 邮件分类预测模块
├── NBClassify.py       # 贝叶斯分类器实现
├── init_db.py          # 数据库初始化脚本
├── config.py           # 配置文件
├── train_model.py      # 模型训练脚本
├── email_system.sql    # 数据库结构
├── model/              # 存放训练好的模型
└── tfidf_vectorizer.pkl # 预训练的 TF-IDF 向量器
```

## 安装和配置

1. 安装依赖：
```bash
pip install flask mysql-connector-python scikit-learn jieba numpy pandas flask-cors
```

2. 配置数据库：
- 在 `config.py` 中设置 MySQL 数据库连接信息
- 运行数据库初始化脚本：
```bash
python init_db.py
```

3. 训练模型（可选，如果需要重新训练）：
```bash
python train_model.py
```

## API 接口

### 用户相关
- POST `/api/register` - 用户注册
- POST `/api/login` - 用户登录
- GET `/api/user` - 获取当前用户信息
- POST `/api/logout` - 用户登出

### 邮件相关
- POST `/api/send_email` - 发送邮件
- GET `/api/inbox` - 获取收件箱
- GET `/api/spam` - 获取垃圾邮件
- GET `/api/sent` - 获取已发送邮件
- GET `/api/email/<email_id>` - 获取邮件详情
- POST `/api/classify` - 邮件分类

## 安全特性

- 密码加密存储（使用 SHA-256）
- 会话管理
- 登录验证中间件
- API 访问控制

## 开发说明

- 邮件分类模型使用了自定义的 TF-IDF 实现
- 系统支持中文邮件的处理和分类
- 提供了完整的用户认证和授权机制
- RESTful API 设计，支持前后端分离

## 注意事项

- 确保 MySQL 服务器正在运行
- 首次使用需要初始化数据库
- 建议在虚拟环境中运行项目
- 默认使用预训练的模型，如需自定义可重新训练