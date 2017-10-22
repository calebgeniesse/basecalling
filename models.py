import os
import tensorflow as tf
import config
import tensorflow.contrib.layers as layers

class Model:
    def __init__(self, training=True):
        self.training = training

    def _create_placeholder(self):
        with tf.name_scope('data'):
            self.signals = tf.placeholder(tf.float32, [None, config.max_seq_len, 1], name="signals_placeholder")
            self.labels = tf.placeholder(tf.int64, [None, config.max_base_len, 1], name="label_placeholder")
            self.sig_length = tf.placeholder(tf.int64, [None], name='sig_length_placeholder')
            self.base_length = tf.placeholder(tf.int64, [None], name='base_length_placeholder')
    
    def _inference(self):
        pass

    def _loss(self):
        pass

    def _train_op(self):
        pass

    def build_graph(self):
        self._create_placeholder()
        self._inference()
        self._loss()
        self._train_op()

class Baseline(Model):
    def resBlock(self, inputs, module_scope = ''):
        with tf.variable_scope(module_scope) as scope:
            conv1 = tf.layers.conv1d(inputs, filters=256, kernel_size=1, strides=1, activation=tf.nn.relu, use_bias=False, padding='same')
            conv1a = tf.layers.conv1d(inputs, filters=256, kernel_size=1, strides=1, activation=tf.nn.relu, padding='same')
            conv2 = tf.layers.conv1d(conv1, filters=256, kernel_size=3, strides=1, activation=tf.nn.relu, use_bias=False, padding='same')
            conv3 = tf.layers.conv1d(conv2, filters=256, kernel_size=1, strides=1, activation=tf.nn.relu, use_bias=False, padding='same')
            return conv3 + conv1a

    def _encode(self): #Just 1 residual block for now
        conv_encoding = self.resBlock(self.signals, 'res1')
        forward = tf.nn.rnn_cell.BasicLSTMCell(200)
        backward = tf.nn.rnn_cell.BasicLSTMCell(200)
        bi_outputs, last_encoder_state = tf.nn.bidirectional_dynamic_rnn(forward, backward, conv_encoding, sequence_length=self.sig_length, time_major=False, dtype=tf.float32)
        bi_outputs = tf.concat(bi_outputs, -1)
        return bi_outputs

    def _decode(self, encoding): #Just a FC layer like in Chiron Paper for Now
        flat_encoding = tf.reshape(encoding, (-1, 400))
        logits = tf.layers.dense(flat_encoding, 5) #CTC Loss needs another class for blank
        self.logits = tf.reshape(logits, (-1, config.max_seq_len, 5))
    
    #The loss here is getting tricky, need to make label sparse, possibly requires reading in input differently
    def _loss(self):
        self.loss = tf.reduce_mean(tf.nn.ctc_loss(label, self.logits, self.sig_len, ctc_merge_repeated=True, time_major=False))

    def _train_op(self):
        self.opt = tf.train.AdamOptimizer(config.lr).minimize(self.loss)

    def _inference(self):
        encoding = self._encode()
        self._decode(encoding)
        self._loss()