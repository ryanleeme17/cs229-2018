import numpy as np
import matplotlib.pyplot as plt
import math
import sys

MAX_POOL_SIZE = 5
CONVOLUTION_SIZE = 4
CONVOLUTION_FILTERS = 2

def forward_softmax(x):
    """
    Compute softmax function for a single example.
    The shape of the input is of size # num classes.

    Important Note: You must be careful to avoid overflow for this function. Functions
    like softmax have a tendency to overflow when very large numbers like e^10000 are computed.
    You will know that your function is overflow resistent when it can handle input like:
    np.array([[10000, 10010, 10]]) without issues.

        x: A 1d numpy float array of shape number_of_classes

    Returns:
        A 1d numpy float array containing the softmax results of shape  number_of_classes
    """
    x = x - np.max(x,axis=0)
    exp = np.exp(x)
    s = exp / np.sum(exp,axis=0)
    return s

def backward_softmax(x, grad_outputs):
    """
    Compute the gradient of the loss with respect to x.

    grad_outputs is the gradient of the loss with respect to the outputs of the softmax.

    Args:
        x: A 1d numpy float array of shape number_of_classes
        grad_outputs: A 1d numpy float array of shape number_of_classes

    Returns:
        A 1d numpy float array of the same shape as x with the derivative of the loss with respect to x
    """
    
    # *** START CODE HERE ***
    S = forward_softmax(x)
    J_softmax = np.diag(S)-np.outer(S,S) 
    return J_softmax@grad_outputs
    # *** END CODE HERE ***

def forward_relu(x):
    """
    Compute the relu function for the input x.

    Args:
        x: A numpy float array

    Returns:
        A numpy float array containing the relu results
    """
    out = np.copy(x) # Make a copy to avoid modifying input
    out[out <= 0] = 0

    return out

def backward_relu(x, grad_outputs):
    """
    Compute the gradient of the loss with respect to x

    Args:
        x: A numpy array of arbitrary shape containing the input.
        grad_outputs: A numpy array of the same shape of x containing the gradient of the loss with respect
            to the output of relu

    Returns:
        A numpy array of the same shape as x containing the gradients with respect to x.
    """

    # *** START CODE HERE ***
    grad_relu = np.where(x>0,1,0)
    return grad_outputs*grad_relu
    # *** END CODE HERE ***

def get_initial_params():
    """
    Compute the initial parameters for the neural network.

    This function should return a dictionary mapping parameter names to numpy arrays containing
    the initial values for those parameters.

    There should be four parameters for this model:
    W1 is the weight matrix for the convolutional layer
    b1 is the bias vector for the convolutional layer
    W2 is the weight matrix for the output layers
    b2 is the bias vector for the output layer

    Weight matrices should be initialized with values drawn from a random normal distribution.
    The mean of that distribution should be 0.
    The variance of that distribution should be 1/sqrt(n) where n is the number of neurons that
    feed into an output for that layer.

    Bias vectors should be initialized with zero.
    
    
    Returns:
        A dict mapping parameter names to numpy arrays
    """

    size_after_convolution = 28 - CONVOLUTION_SIZE + 1
    size_after_max_pooling = size_after_convolution // MAX_POOL_SIZE

    num_hidden = size_after_max_pooling * size_after_max_pooling * CONVOLUTION_FILTERS

    return {
        'W1': np.random.normal(size = (CONVOLUTION_FILTERS, 1, CONVOLUTION_SIZE, CONVOLUTION_SIZE), scale=1/ math.sqrt(CONVOLUTION_SIZE * CONVOLUTION_SIZE)),
        'b1': np.zeros(CONVOLUTION_FILTERS),
        'W2': np.random.normal(size = (num_hidden, 10), scale = 1/ math.sqrt(num_hidden)),
        'b2': np.zeros(10)
    }

def forward_convolution(conv_W, conv_b, data):
    """
    Compute the output from a convolutional layer given the weights and data.

    conv_W is of the shape (# output channels, # input channels, convolution width, convolution height )
    conv_b is of the shape (# output channels)

    data is of the shape (# input channels, width, height)

    The output should be the result of a convolution and should be of the size:
        (# output channels, width - convolution width + 1, height -  convolution height + 1)

    Returns:
        The output of the convolution as a numpy array
    """

    conv_channels, _, conv_width, conv_height = conv_W.shape

    input_channels, input_width, input_height = data.shape

    output = np.zeros((conv_channels, input_width - conv_width + 1, input_height - conv_height + 1))

    for x in range(input_width - conv_width + 1):
        for y in range(input_height - conv_height + 1):
            for output_channel in range(conv_channels):
                output[output_channel, x, y] = np.sum(
                    np.multiply(data[:, x:(x + conv_width), y:(y + conv_height)], conv_W[output_channel, :, :, :])) + conv_b[output_channel]

    return output

def backward_convolution(conv_W, conv_b, data, output_grad):
    """
    Compute the gradient of the loss with respect to the parameters of the convolution.

    See forward_convolution for the sizes of the arguments.
    output_grad is the gradient of the loss with respect to the output of the convolution.

    Returns:
        A tuple containing 3 gradients.
        The first element is the gradient of the loss with respect to the convolution weights
        The second element is the gradient of the loss with respect to the convolution bias
        The third element is the gradient of the loss with respect to the input data
    """

    # *** START CODE HERE ***
    conv_channels, _, conv_width, conv_height = conv_W.shape # don't save input_channels as it is described in next line
    input_channels, input_width, input_height = data.shape

    # calculate derivative of loss wrt conv weights, conv equation for 1 filter is output = w.T@x+b
    dL_dW = np.zeros((conv_channels,input_channels,conv_width,conv_height))
    dL_dData = np.zeros((input_channels,input_width,input_height))

    for x in range(input_width - conv_width + 1):
        for y in range(input_height - conv_height + 1):
            for output_channel in range(conv_channels): # 
                
                dC_dW = data[:, x:(x + conv_width), y:(y + conv_height)] #deriv of conv wrt W at output channel is x volume
                dL_dC = output_grad[output_channel,x,y] # scalar value
                
                # Calculate gradient for this patch and accumulate it into the dL_dW tensor
                dL_dW[output_channel,:,:,:] += dL_dC*dC_dW #accumulation, as there is overlap during conv
                
                #gradient of data at patch
                dL_dData[:, x:(x + conv_width), y:(y + conv_height)] += output_grad[output_channel, x, y] * conv_W[output_channel, :, :, :]

                # Assertions for dimensional consistency
                assert(dC_dW.shape == (input_channels, conv_width, conv_height))
                assert(dL_dW[output_channel].shape == (input_channels,conv_width,conv_height)) 
    
    # derivative of loss with respect to bias
    dL_db = np.zeros(conv_channels)
    for x in range(input_width - conv_width + 1):
        for y in range(input_height - conv_height + 1):
            for output_channel in range(conv_channels):
                dL_db[output_channel] +=  1*output_grad[output_channel,x,y] # 1 is deriv output wrt bias
    
    return (dL_dW, dL_db,dL_dData)
    # *** END CODE HERE ***

def forward_max_pool(data, pool_width, pool_height):
    """
    Compute the output from a max pooling layer given the data and pool dimensions.

    The stride length should be equal to the pool size

    data is of the shape (# channels, width, height)

    The output should be the result of the max pooling layer and should be of size:
        (# channels, width // pool_width, height // pool_height)

    Returns:
        The result of the max pooling layer
    """
    input_channels, input_width, input_height = data.shape
    
    output = np.zeros((input_channels, input_width // pool_width, input_height // pool_height))

    for x in range(0, input_width, pool_width):
        for y in range(0, input_height, pool_height):

            output[:, x // pool_width, y // pool_height] = np.amax(data[:, x:(x + pool_width), y:(y + pool_height)], axis=(1, 2))

    return output

def backward_max_pool(data, pool_width, pool_height, output_grad):
    """
    Compute the gradient of the loss with respect to the data in the max pooling layer.

    data is of the shape (# channels, width, height)
    output_grad is of shape (# channels, width // pool_width, height // pool_height)

    output_grad is the gradient of the loss with respect to the output of the backward max
    pool layer.

    Returns:
        The gradient of the loss with respect to the data (of same shape as data)
    """
    
    # *** START CODE HERE ***
    input_channels, input_width, input_height = data.shape
    grad_data = np.zeros((input_channels, input_width, input_height))

    for x in range(0, input_width, pool_width):
        for y in range(0, input_height, pool_height):
            # extract pooling patch
            pooling_patch = data[:, x:(x + pool_width), y:(y + pool_height)]

            # extract the max value of pooling patch. Reshape (#channels,) -> (#channels,1,1)
            max_val = np.amax(pooling_patch, axis=(1, 2)).reshape((input_channels,1,1))            
            
            # create an indicator mask (1 where max value is)
            dP_dData = (pooling_patch == max_val).astype(int)

            # dL/dPool is a set of scalars (1 at each channel) 
            # at output_grad loc: x//pool_width, y//pool_height. Reshape (#channels,) -> (#channels,1,1)
            dL_dP = output_grad[:, x // pool_width, y // pool_height].reshape((input_channels,1,1)) 
            
            # calculate grad of loss wrt to data. Elementwise mult. of mask with max value at channel
            grad_data[:, x:(x + pool_width), y:(y + pool_height)] = dL_dP*dP_dData

    return grad_data
    # *** END CODE HERE ***

def forward_cross_entropy_loss(probabilities, labels):
    """
    Compute the output from a cross entropy loss layer given the probabilities and labels.

    probabilities is of the shape (# classes)
    labels is of the shape (# classes)

    The output should be a scalar

    Returns:
        The result of the log loss layer
    """

    result = 0

    for i, label in enumerate(labels):
        if label == 1:
            result += -np.log(probabilities[i])

    return result

def backward_cross_entropy_loss(probabilities, labels):
    """
    Compute the gradient of the cross entropy loss with respect to the probabilities.

    probabilities is of the shape (# classes)
    labels is of the shape (# classes)

    The output should be the gradient with respect to the probabilities.

    Returns:
        The gradient of the loss with respect to the probabilities.
    """

    # *** START CODE HERE ***
    epsilon = 1e-10
    return -labels / (probabilities + epsilon)
    # *** END CODE HERE ***

def forward_linear(weights, bias, data):
    """
    Compute the output from a linear layer with the given weights, bias and data.
    weights is of the shape (input # feature [n], output # features [d])
    bias is of the shape (output # features [d])
    data is of the shape (input # features [n])

    The output should be of the shape (output # features)

    Returns:
        The result of the linear layer
    """
    return data.dot(weights) + bias

def backward_linear(weights, bias, data, output_grad):
    """
    Compute the gradients of the loss with respect to the parameters of a linear layer.

    See forward_linear for information about the shapes of the variables.

    output_grad is the gradient of the loss with respect to the output of this layer.

    This should return a tuple with three elements:
    - The gradient of the loss with respect to the weights
    - The gradient of the loss with respect to the bias
    - The gradient of the loss with respect to the data
    """

    # *** START CODE HERE ***

    # Gradient w.r.t. weights. This is an outer product.
    dL_dW = np.outer(data, output_grad)
    
    # Gradient w.r.t. bias.
    dL_db = output_grad.copy()
    
    # Gradient w.r.t. data. dL/dData = weights
    dL_dData = weights.dot(output_grad)

    return (dL_dW, dL_db, dL_dData)

    # *** END CODE HERE ***

def forward_prop(data, labels, params):
    """
    Implement the forward layer given the data, labels, and params.
    
    Args:
        data: A numpy array containing the input (shape is 1 by 28 by 28)
        labels: A 1d numpy array containing the labels (shape is 10)
        params: A dictionary mapping parameter names to numpy arrays with the parameters.
            This numpy array will contain W1, b1, W2 and b2
            W1 and b1 represent the weights and bias for the hidden layer of the network
            W2 and b2 represent the weights and bias for the output layer of the network

    Returns:
        A 2 element tuple containing:
            1. A numpy array The output (after the softmax) of the output layer
            2. The average loss for these data elements
    """

    W1 = params['W1']
    b1 = params['b1']
    W2 = params['W2']
    b2 = params['b2']

    first_convolution = forward_convolution(W1, b1, data)
    first_max_pool = forward_max_pool(first_convolution, MAX_POOL_SIZE, MAX_POOL_SIZE)
    first_after_relu = forward_relu(first_max_pool)

    flattened = np.reshape(first_after_relu, (-1))
    
    logits = forward_linear(W2, b2, flattened)

    y = forward_softmax(logits)
    cost = forward_cross_entropy_loss(y, labels)

    return y, cost

def backward_prop(data, labels, params):
    """
    Implement the backward propagation gradient computation step for a neural network
    
    Args:
        data: A numpy array containing the input for a single example
        labels: A 1d numpy array containing the labels for a single example
        params: A dictionary mapping parameter names to numpy arrays with the parameters.
            This numpy array will contain W1, b1, W2, and b2
            W1 and b1 represent the weights and bias for the convolutional layer
            W2 and b2 represent the weights and bias for the output layer of the network

    Returns:
        A dictionary of strings to numpy arrays where each key represents the name of a weight
        and the values represent the gradient of the loss with respect to that weight.
        
        In particular, it should have 4 elements:
            W1, W2, b1, and b2
    """

    # *** START CODE HERE ***
    # Since this implementation of forward pass does not store intermediate values or activations
    # we need to re-run the forward pass to do backprop
    
    # Forward Pass for intermediate values
    first_convolution = forward_convolution(params['W1'], params['b1'], data)
    first_max_pool = forward_max_pool(first_convolution, MAX_POOL_SIZE, MAX_POOL_SIZE)
    first_after_relu = forward_relu(first_max_pool) # RELU 
    flattened = np.reshape(first_after_relu, (-1)) 
    logits = forward_linear(params['W2'], params['b2'], flattened) # coverd
    y = forward_softmax(logits)                  # covered
    cost = forward_cross_entropy_loss(y, labels) # covered

    # IMPLEMENT BACKPROPOGATION
    grads = {}

    # 1. get grad of cost
    grad_CE = backward_cross_entropy_loss(y, labels)      # y after softmax is probabilities

    # 2. get grad of softmax. Problem, need x, which is the logits
    grad_softmax = backward_softmax(logits, grad_CE)             # logits are (k,) size

    # 3. get grad of forward_linear for fully connected layer (FC)
    (grads['W2'], grads['b2'], grad_linear) = backward_linear(params['W2'], params['b2'], flattened, grad_softmax)

    # 4. get grad of RELU layer
    grad_linear = grad_linear.reshape((first_after_relu.shape))
    grad_relu = backward_relu(first_max_pool, grad_linear) # x is input to RELU, grad_output.

    # 5. get grad of Pool layer with backprop
    grad_pool = backward_max_pool(first_convolution, MAX_POOL_SIZE, MAX_POOL_SIZE, grad_relu)

    # 6. get grad of Conv Layer with backprop
    (grads['W1'], grads['b1'],_) = backward_convolution(params['W1'], params['b1'], data, grad_pool)

    return grads
    # *** END CODE HERE ***

def forward_prop_batch(batch_data, batch_labels, params, forward_prop_func):
    """Apply the forward prop func to every image in a batch"""

    y_array = []
    cost_array = []

    for item, label in zip(batch_data, batch_labels):
        y, cost = forward_prop_func(item, label, params)
        y_array.append(y)
        cost_array.append(cost)

    return np.array(y_array), np.array(cost_array)

def gradient_descent_batch(batch_data, batch_labels, learning_rate, params, backward_prop_func):
    """
    Perform one batch of gradient descent on the given training data using the provided learning rate.

    This code should update the parameters stored in params.
    It should not return anything

    Args:
        batch_data: A numpy array containing the training data for the batch
        train_labels: A numpy array containing the training labels for the batch
        learning_rate: The learning rate
        params: A dict of parameter names to parameter values that should be updated.
        backward_prop_func: A function that follows the backwards_prop API

    Returns: This function returns nothing.
    """

    total_grad = {}

    for i in range(batch_data.shape[0]):
        grad = backward_prop_func(
            batch_data[i, :, :],
            batch_labels[i, :],
            params)
        for key, value in grad.items():
            if key not in total_grad:
                total_grad[key] = np.zeros(value.shape)

            total_grad[key] += value

    params['W1'] = params['W1'] - learning_rate * total_grad['W1']
    params['W2'] = params['W2'] - learning_rate * total_grad['W2']
    params['b1'] = params['b1'] - learning_rate * total_grad['b1']
    params['b2'] = params['b2'] - learning_rate * total_grad['b2']

    # This function does not return anything
    return

def nn_train(
    train_data, train_labels, dev_data, dev_labels,
    get_initial_params_func, forward_prop_func, backward_prop_func,
    learning_rate=5.0, batch_size=16, num_batches=400):

    m = train_data.shape[0]

    params = get_initial_params_func()

    cost_dev = []
    accuracy_dev = []
    for batch in range(num_batches):
        print('Currently processing {} / {}'.format(batch, num_batches))

        batch_data = train_data[batch * batch_size:(batch + 1) * batch_size, :, :, :]
        batch_labels = train_labels[batch * batch_size: (batch + 1) * batch_size, :]

        if batch % 100 == 0:
            output, cost = forward_prop_batch(dev_data, dev_labels, params, forward_prop_func)
            cost_dev.append(sum(cost) / len(cost))
            accuracy_dev.append(compute_accuracy(output, dev_labels))

            print('Cost and accuracy', cost_dev[-1], accuracy_dev[-1])

        gradient_descent_batch(batch_data, batch_labels,
            learning_rate, params, backward_prop_func)

    return params, cost_dev, accuracy_dev

def nn_test(data, labels, params):
    output, cost = forward_prop(data, labels, params) # MODIFIED, forward_pr not valid
    accuracy = compute_accuracy(output, labels)
    return accuracy

def compute_accuracy(output, labels):
    correct_output = np.argmax(output,axis=1)
    correct_labels = np.argmax(labels,axis=1)

    is_correct = [a == b for a,b in zip(correct_output, correct_labels)]

    accuracy = sum(is_correct) * 1. / labels.shape[0]
    return accuracy

def one_hot_labels(labels):
    one_hot_labels = np.zeros((labels.size, 10))
    one_hot_labels[np.arange(labels.size),labels.astype(int)] = 1
    return one_hot_labels

def read_data(images_file, labels_file):
    x = np.loadtxt(images_file, delimiter=',')
    y = np.loadtxt(labels_file, delimiter=',')

    x = np.reshape(x, (x.shape[0], 1, 28, 28))

    return x, y

def run_train(all_data, all_labels, backward_prop_func):
    params, cost_dev, accuracy_dev = nn_train(
        all_data['train'], all_labels['train'],
        all_data['dev'], all_labels['dev'],
        get_initial_params, forward_prop, backward_prop_func,
        learning_rate=1e-2, batch_size=16, num_batches=400
    )

    t = np.arange(400 // 100)

    fig, (ax1, ax2) = plt.subplots(2, 1)

    ax1.plot(t, cost_dev, 'b')
    ax1.set_xlabel('time')
    ax1.set_ylabel('loss')
    ax1.set_title('Training curve')

    ax2.plot(t, accuracy_dev, 'b')
    ax2.set_xlabel('time')
    ax2.set_ylabel('accuracy')

    fig.savefig('output/train.png')

def main():
    np.random.seed(100)
    train_data, train_labels = read_data('../data/images_train.csv', '../data/labels_train.csv')
    train_labels = one_hot_labels(train_labels)
    p = np.random.permutation(60000)
    train_data = train_data[p,:]
    train_labels = train_labels[p,:]

    dev_data = train_data[0:400,:]
    dev_labels = train_labels[0:400,:]
    train_data = train_data[400:,:]
    train_labels = train_labels[400:,:]

    mean = np.mean(train_data)
    std = np.std(train_data)
    train_data = (train_data - mean) / std
    dev_data = (dev_data - mean) / std

    all_data = {
        'train': train_data,
        'dev': dev_data,
    }

    all_labels = {
        'train': train_labels,
        'dev': dev_labels,
    }
    
    run_train(all_data, all_labels, backward_prop)

if __name__ == '__main__':
    main()