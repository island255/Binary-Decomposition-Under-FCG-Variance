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


class RF:
    def __init__(self, n_estimators):
        self.name = "RF"
        self.RF = RandomForestClassifier(n_estimators)

    def train(self, training_data, training_label):
        self.RF.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.RF.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class GB:
    def __init__(self, n_estimators):
        self.name = "GB"
        self.GB = GradientBoostingClassifier(n_estimators=n_estimators)

    def train(self, training_data, training_label):
        self.GB.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.GB.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class adaboost:
    def __init__(self, n_estimators):
        self.name = "adaboost"
        self.adaboost = AdaBoostClassifier(n_estimators=n_estimators)

    def train(self, training_data, training_label):
        self.adaboost.fit(training_data, training_label)

    def predict(self, testing_data):
        predicted_labels = self.adaboost.predict(testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class KNN:
    def __init__(self, n_estimators):
        self.name = "KNN"
        self.n_estimators = n_estimators
        self.KNN_base = KNeighborsClassifier(n_neighbors=10)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.KNN = bagging.train_model(self.KNN_base, training_data, training_label, 0.5, self.n_estimators)

    def predict(self, testing_data):
        predicted_labels = bagging.predict(self.KNN, testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class LR:
    def __init__(self, n_estimators):
        self.name = "LR"
        self.n_estimators = n_estimators
        self.LR_base = LogisticRegression(penalty='l2', max_iter=10000)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.LR = bagging.train_model(self.LR_base, training_data, training_label, 0.5, self.n_estimators)

    def predict(self, testing_data):
        predicted_labels = bagging.predict(self.LR, testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class LDA:
    def __init__(self, n_estimators):
        self.name = "LDA"
        self.n_estimators = n_estimators
        self.LDA_base = LinearDiscriminantAnalysis()
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.LDA = bagging.train_model(self.LDA_base, training_data, training_label, 0.5, self.n_estimators)

    def predict(self, testing_data):
        predicted_labels = bagging.predict(self.LDA, testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class QDA:
    def __init__(self, n_estimators):
        self.name = "QDA"
        self.n_estimators = n_estimators
        self.QDA_base = QuadraticDiscriminantAnalysis()
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.QDA = bagging.train_model(self.QDA_base, training_data, training_label, 0.5, self.n_estimators)

    def predict(self, testing_data):
        predicted_labels = bagging.predict(self.QDA, testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class SVM:
    def __init__(self, n_estimators):
        self.name = "SVM"
        self.n_estimators = n_estimators
        self.SVM_base = SVC(kernel='rbf', probability=True)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.SVM = bagging.train_model(self.SVM_base, training_data, training_label, 0.5, self.n_estimators)

    def predict(self, testing_data):
        predicted_labels = bagging.predict(self.SVM, testing_data)
        return predicted_labels

    def get_name(self):
        return self.name


class NBC:
    def __init__(self, n_estimators):
        self.name = "NBC"
        self.n_estimators = n_estimators
        self.NBC_base = MultinomialNB(alpha=0.01)
        # self.RFPCT = random_forest.RandomForest(self.PCT_model, n_estimators)

    def train(self, training_data, training_label):
        self.NBC = bagging.train_model(self.NBC_base, training_data, training_label, 0.5, self.n_estimators)

    def predict(self, testing_data):
        predicted_labels = bagging.predict(self.NBC, testing_data)
        return predicted_labels

    def get_name(self):
        return self.name
