#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 Restricted Boltzmann Machine (RBM)
 References :
   - Y. Bengio, P. Lamblin, D. Popovici, H. Larochelle: Greedy Layer-Wise
   Training of Deep Networks, Advances in Neural Information Processing
   Systems 19, 2007
   - DeepLearningTutorials
   https://github.com/lisa-lab/DeepLearningTutorials
"""

import sys
import numpy


numpy.seterr(all='ignore')

def sigmoid(x):
    return 1. / (1 + numpy.exp(-x))


class RBM(object):
    def __init__(self, input=None, n_visible=2, n_hidden=3, \
        W=None, hbias=None, vbias=None, numpy_rng=None):
        
        self.n_visible = n_visible  # num of units in visible (input) layer
        self.n_hidden = n_hidden    # num of units in hidden layer

        if numpy_rng is None:
            numpy_rng = numpy.random.RandomState(1234)


        if W is None:
            a = 1. / n_visible
            initial_W = numpy.array(numpy_rng.uniform(  # initialize W uniformly
                low=-a,
                high=a,
                size=(n_visible, n_hidden)))

            W = initial_W

        if hbias is None:
            hbias = numpy.zeros(n_hidden)  # initialize h bias 0

        if vbias is None:
            vbias = numpy.zeros(n_visible)  # initialize v bias 0


        self.numpy_rng = numpy_rng
        self.input = input
        self.W = W
        self.hbias = hbias
        self.vbias = vbias

        # self.params = [self.W, self.hbias, self.vbias]


    def contrastive_divergence(self, lr=0.1, k=1, input=None):
        if input is not None:
            self.input = input
        
        ''' CD-k '''
        ph_mean, ph_sample = self.sample_h_given_v(self.input)

        chain_start = ph_sample

        for step in range(k):
            if step == 0:
                nv_means, nv_samples,\
                nh_means, nh_samples = self.gibbs_hvh(chain_start)
            else:
                nv_means, nv_samples,\
                nh_means, nh_samples = self.gibbs_hvh(nh_samples)

        # chain_end = nv_samples


        self.W += lr * (numpy.dot(self.input.T, ph_sample)
                        - numpy.dot(nv_samples.T, nh_means))
        self.vbias += lr * numpy.mean(self.input - nv_samples, axis=0)
        self.hbias += lr * numpy.mean(ph_sample - nh_means, axis=0)

        # cost = self.get_reconstruction_cross_entropy()
        # return cost


    def sample_h_given_v(self, v0_sample):
        h1_mean = self.propup(v0_sample)
        h1_sample = self.numpy_rng.binomial(size=h1_mean.shape,   # discrete: binomial
                                       n=1,
                                       p=h1_mean)

        return [h1_mean, h1_sample]


    def sample_v_given_h(self, h0_sample):
        v1_mean = self.propdown(h0_sample)
        v1_sample = self.numpy_rng.binomial(size=v1_mean.shape,   # discrete: binomial
                                            n=1,
                                            p=v1_mean)
        
        return [v1_mean, v1_sample]

    def propup(self, v):
        pre_sigmoid_activation = numpy.dot(v, self.W) + self.hbias
        return sigmoid(pre_sigmoid_activation)

    def propdown(self, h):
        pre_sigmoid_activation = numpy.dot(h, self.W.T) + self.vbias
        return sigmoid(pre_sigmoid_activation)


    def gibbs_hvh(self, h0_sample):
        v1_mean, v1_sample = self.sample_v_given_h(h0_sample)
        h1_mean, h1_sample = self.sample_h_given_v(v1_sample)

        return [v1_mean, v1_sample,
                h1_mean, h1_sample]
    

    def get_reconstruction_cross_entropy(self):
        pre_sigmoid_activation_h = numpy.dot(self.input, self.W) + self.hbias
        sigmoid_activation_h = sigmoid(pre_sigmoid_activation_h)
        
        pre_sigmoid_activation_v = numpy.dot(sigmoid_activation_h, self.W.T) + self.vbias
        sigmoid_activation_v = sigmoid(pre_sigmoid_activation_v)

        cross_entropy =  - numpy.mean(
            numpy.sum(self.input * numpy.log(sigmoid_activation_v) +
            (1 - self.input) * numpy.log(1 - sigmoid_activation_v),
                      axis=1))
        
        return cross_entropy

    def reconstruct(self, v):
        h = sigmoid(numpy.dot(v, self.W) + self.hbias)
        reconstructed_v = sigmoid(numpy.dot(h, self.W.T) + self.vbias)
        return reconstructed_v
        
# 受限波茲曼機，具有糾錯功能(分群)，將某個沒出現過的向量，分到已出現過的向量中
# 這有點像 K近鄰算法的功效。
def train_rbm(data, n_hidden, learning_rate=0.1, k=1, training_epochs=1000, rng=numpy.random.RandomState(123)):
    # construct RBM
    rbm = RBM(input=data, n_visible=len(data[0]), n_hidden=n_hidden, numpy_rng=rng)

    # train
    for epoch in range(training_epochs):
        rbm.contrastive_divergence(lr=learning_rate, k=k)
        cost = rbm.get_reconstruction_cross_entropy()
        print(f'Training epoch {epoch}, cost is {cost}')
    return rbm

if __name__ == "__main__":
    data = numpy.array([[1,1,1,0,0,0],
                        [1,0,1,0,0,0],
                        [1,1,1,0,0,0],
                        [0,0,1,1,1,0],
                        [0,0,1,1,0,0],
                        [0,0,1,1,1,0]])
    rbm = train_rbm(data, 2)
    # test
    v = numpy.array([[0, 0, 0, 1, 1, 0], # 被歸回 001110
                     [1, 1, 0, 0, 0, 0]]) # 被歸回 111000

    print(rbm.reconstruct(v))
