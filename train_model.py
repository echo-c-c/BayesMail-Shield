import numpy as np
from sklearn.naive_bayes import MultinomialNB
import joblib
from predict import TfidfVectorizer

# 训练数据
spam_texts = [
    "恭喜您中奖了！点击领取100万大奖！",
    "限时特价，全场1折起！",
    "您的账户出现异常，请立即验证！",
    "震撼优惠！名牌包包、手表特价销售！",
    "免费领取iPhone 15，仅此一天！",
    "紧急通知：您的账户将被冻结",
    "恭喜抽中大奖，点击领取",
    "您的银行账户出现异常，请立即处理",
    "特大优惠：名牌手表1折起",
    "最后一天优惠，错过不再有！"
]

ham_texts = [
    "关于项目进展的报告",
    "下周二下午2点开会讨论",
    "请查收本月工作总结",
    "新功能开发计划书",
    "周会会议纪要",
    "项目测试报告",
    "请回复确认收到文件",
    "关于系统升级的通知",
    "明天下午的会议安排",
    "本周工作进展情况"
]

# 准备训练数据
X = spam_texts + ham_texts
y = [1] * len(spam_texts) + [0] * len(ham_texts)  # 1表示垃圾邮件，0表示正常邮件

# 创建TF-IDF向量化器
vectorizer = TfidfVectorizer()
X_tfidf = vectorizer.fit_transform(X)

# 训练朴素贝叶斯模型
model = MultinomialNB()
model.fit(X_tfidf, y)

# 创建model目录（如果不存在）
import os
if not os.path.exists('model'):
    os.makedirs('model')

# 保存模型和向量化器
joblib.dump(model, 'model/naive_bayes_model.pkl')
joblib.dump(vectorizer, 'model/tfidf_vectorizer.pkl')

print("模型训练完成并保存！")

# 测试模型
test_texts = [
    "项目进展报告请查收",  # 正常邮件
    "恭喜中奖！点击领取！"  # 垃圾邮件
]

# 加载模型和向量化器
loaded_model = joblib.load('model/naive_bayes_model.pkl')
loaded_vectorizer = joblib.load('model/tfidf_vectorizer.pkl')

# 测试预测
for text in test_texts:
    X_test = loaded_vectorizer.transform([text])
    prediction = loaded_model.predict(X_test)
    result = "垃圾邮件" if prediction[0] == 1 else "正常邮件"
    print(f"文本: {text}")
    print(f"预测结果: {result}\n") 