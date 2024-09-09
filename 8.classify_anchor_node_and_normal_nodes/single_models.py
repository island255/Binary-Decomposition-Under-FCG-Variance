import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

import bagging
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier

import random


class KNN:
    def __init__(self):
        self.name = "KNN"
        self.KNN = KNeighborsClassifier(n_neighbors=10)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.KNN.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.KNN.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class LR:
    def __init__(self):
        self.name = "LR"
        self.LR = LogisticRegression(penalty='l2', max_iter=10000)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.LR.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.LR.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class LDA:
    def __init__(self):
        self.name = "LDA"
        self.LDA = LinearDiscriminantAnalysis()
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.LDA.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.LDA.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class QDA:
    def __init__(self):
        self.name = "QDA"
        self.QDA = QuadraticDiscriminantAnalysis()
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.QDA.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.QDA.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class SVM:
    def __init__(self):
        self.name = "SVM"
        self.SVM = SVC(kernel='rbf', probability=True)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.SVM.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.SVM.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class DT:
    def __init__(self):
        self.name = "DT"
        self.DT = DecisionTreeClassifier()
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.DT.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.DT.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class NBC:
    def __init__(self):
        self.name = "NBC"
        self.NBC = MultinomialNB(alpha=0.01)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.NBC.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.NBC.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name
