import jieba
import numpy as np
import joblib

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
            words = ['']
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

def predict_label(text):
    """
    使用训练好的模型预测文本是否为垃圾邮件
    """
    try:
        # 加载模型和向量器
        model = joblib.load('model/naive_bayes_model.pkl')
        vectorizer = joblib.load('model/tfidf_vectorizer.pkl')
        
        # 转换文本
        X = vectorizer.transform([text])
        
        # 预测
        prediction = model.predict(X)
        
        # 返回预测结果
        return '垃圾邮件' if prediction[0] == 1 else '正常邮件'
    except Exception as e:
        print(f"预测错误: {e}")
        return '正常邮件'  # 如果出错，默认为正常邮件
