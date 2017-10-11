import tensorflow as tf
import numpy as np
import cv2
import scipy
import model.vgg19 as vgg
CONTENT_LAYER = ('relu4_2','relu5_2')
STYLE_LAYER = ('relu1_1','relu2_1','relu3_1','relu4_1','relu5_1')


def stylization(network,init,content,style,content_weigth,style_weight,layer_exp):

    # init
    vgg_weight,vgg_mean = vgg.load_net(network)

    content_shape = (1,content.shape())
    style_shape = (1,) + style.shape()
    content_feature = {}
    style_feature = {}


    #normalization
    layer_init = 1.0
    layer_sum = 0
    layer_weight = {}
    for style_layer in STYLE_LAYER:
        layer_weight[style_layer] = layer_init
        layer_sum += layer_init
        layer_init *= layer_exp
    for style_layer in STYLE_LAYER:
        layer_weight /= layer_sum

    #get features of two images
    graph = tf.Graph()
    with graph.as_default(),graph.device('/cpu:0'),tf.Session() as sess :
        image = tf.placeholder(tf.float32,shape = content_shape)
        input_layer = vgg.load_net(vgg_weight,image,'max')
        content_pre = np.array([vgg.preProcess(content,vgg_mean)])
        for layer in CONTENT_LAYER:
            content_feature[layer] = input_layer[layer].eval(feed_dict={image:content_pre})

    with graph.as_default(),graph.device('/cpu:0'),tf.Session() as sess :
        image = tf.placeholder(tf.float32,shape = style_shape)
        input_layer = vgg.load_net(vgg_weight,image,'max')
        style_pre = np.array([vgg.preProcess(style,vgg_mean)])
        for layer in STYLE_LAYER:
            feature = input_layer[layer].eval(feed_dict={image:style_pre})
            feature = np.reshape(feature,(-1,feature.shape[3]))
            gram = np.matmul(feature.T,feature)/feature.size
            style_feature[layer] = gram
    init_noise_coeff = 1.0 - init

    #make image
    with tf.Graph().as_default():
        noise  = np.random.normal(size=style_shape,scale=np.std(content)*0.1)
        initial = tf.random_normal(style_shape)*0.256

        image = tf.Variable(initial)
        net = vgg.load_net(vgg_weight,image,"max")

        #content loss
        content_layer_weights = {}
        content_layer_weights['relu4_2'] = content_weigth
        content_layer_weights['relu5_2'] = 1.0 - content_weigth

        conten_loss = 0
        content_losses = []
        for layer in CONTENT_LAYER:
            content_losses.append(content_layer_weights[layer]*content_weigth*(2*tf.nn.l2_loss(net[layer]-content_feature[layer])/content_feature[layer].size))
        conten_loss += reduce(tf.add,conten_loss)
