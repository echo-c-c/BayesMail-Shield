# encoding=utf8
import numpy as np
import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, log_loss, confusion_matrix, classification_report
import joblib
import jieba
from matplotlib import pyplot as plt
import seaborn as sns

# 定义自定义的CountVectorizer类
class CountVectorizer:
    def __init__(self, *, vocabulary=None, ngram_range=(1, 1), stop_words=None):
        self.vocabulary = vocabulary
        self.ngram_range = ngram_range
        self.stop_words = stop_words

    def fit_transform(self, texts):
        self.vocabulary_ = {}
        self.index_ = {}
        index = 0
        for text in texts:
            ngrams = self._get_ngrams(text)
            for ngram in ngrams:
                if self.vocabulary is not None and ngram not in self.vocabulary:
                    continue
                if ngram not in self.vocabulary_:
                    self.vocabulary_[ngram] = index
                    self.index_[index] = ngram
                    index += 1

        matrix = np.zeros((len(texts), len(self.vocabulary_)), dtype=int)
        for i, text in enumerate(texts):
            ngrams = self._get_ngrams(text)
            for ngram in ngrams:
                if ngram in self.vocabulary_:
                    j = self.vocabulary_[ngram]
                    matrix[i][j] += 1
        return matrix

    def transform(self, texts):
        matrix = np.zeros((len(texts), len(self.vocabulary_)), dtype=int)
        for i, text in enumerate(texts):
            ngrams = self._get_ngrams(text)
            for ngram in ngrams:
                if ngram in self.vocabulary_:
                    j = self.vocabulary_[ngram]
                    matrix[i][j] += 1
        return matrix

    def _get_ngrams(self, text):
        try:
            words = list(jieba.cut(text))
        except:
            words =['']
        if self.stop_words is not None:
            words = [word for word in words if word not in self.stop_words]

        ngrams = []
        min_n, max_n = self.ngram_range
        for n in range(min_n, max_n + 1):
            for i in range(len(words) - n + 1):
                ngram = ' '.join(words[i:i + n])
                ngrams.append(ngram)
        return ngrams

class TfidfVectorizer(CountVectorizer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.idf_ = None

    def fit_transform(self, texts):
        tf_matrix = super().fit_transform(texts)
        self.idf_ = np.log((1 + len(texts)) / (1 + np.sum(tf_matrix > 0, axis=0))) + 1
        tfidf_matrix = tf_matrix * self.idf_
        row_norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
        tfidf_matrix = tfidf_matrix / np.where(row_norms == 0, 1, row_norms)
        return tfidf_matrix

    def transform(self, texts):
        tf_matrix = super().transform(texts)
        tfidf_matrix = tf_matrix * self.idf_ if self.idf_ is not None else tf_matrix
        row_norms = np.linalg.norm(tfidf_matrix, axis=1, keepdims=True)
        tfidf_matrix = tfidf_matrix / np.where(row_norms == 0, 1, row_norms)
        return tfidf_matrix

# 加载数据
save_path = "./CNEC.csv"
content_index = 'content'
label_index = 'label'
data = pd.read_csv(save_path)
data = data.head(10000)

# 把数据分为训练集和测试集，比例为8:2
train_data = data.sample(frac=0.8, random_state=1)
test_data = data.drop(train_data.index)

# 使用自定义的TfidfVectorizer将文本转换为词频矩阵
vectorizer = TfidfVectorizer()
X_train = vectorizer.fit_transform(train_data[content_index])
X_test = vectorizer.transform(test_data[content_index])

# 使用MultinomialNB进行朴素贝叶斯分类
clf = MultinomialNB()
clf.fit(X_train, train_data[label_index])

# 保存模型和向量化器
joblib.dump(clf, 'naive_bayes_model.pkl')
joblib.dump(vectorizer, 'tfidf_vectorizer.pkl')

# 评估模型
y_pred = clf.predict(X_test)
y_prob = clf.predict_proba(X_test)[:, 1]

loss = log_loss(test_data[label_index], y_prob)
print(f'Log Loss: {loss:.4f}')

labels = sorted(list(set(train_data[label_index])))
labels = [str(i) for i in labels]

total_accuracy = accuracy_score(test_data[label_index], y_pred)
print(f'Total Accuracy: {total_accuracy:.4f}')

classification_report = classification_report(test_data[label_index], y_pred, target_names=labels, output_dict=True)
df_classification_report = pd.DataFrame.from_dict(classification_report).transpose()
df_classification_report = df_classification_report.round(4)
print(df_classification_report)

cm = confusion_matrix(test_data[label_index], y_pred)
print('Confusion Matrix:')
print(cm)

plt.figure(figsize=(10, 7))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()
