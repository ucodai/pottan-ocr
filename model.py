from __future__ import print_function
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.autograd import Variable

from utils import readJson
from os import path
import glob
import cv2 
import numpy as np
import torch
cachedData = './cache/trainData.npy'
savedModel = './cache/model-state'

def getTrainData( fname ):
    img = cv2.imread( fname, cv2.IMREAD_GRAYSCALE )
    img = resizedImg = cv2.resize( img, ( 32, 32 ), interpolation=cv2.INTER_CUBIC )
    return np.expand_dims( img.astype( np.float32 ), axis=0 )


if( path.exists( cachedData ) ):
    print('Loading cached data')
    trainData = np.load( cachedData )
    print('Loaded')
else:
    print('Saving cached data')
    glyphs = readJson('./cache/glyph_labels.json')
    charMap = {}
    for idx, ( glyph, lable ) in enumerate( glyphs ):
        charMap[ lable ] = idx
    trainFiles = glob.glob('./cache/generated/**/*.pgm')
    traiImagenData = [ getTrainData( fname ) for fname in trainFiles ]
    labels = [ charMap[ fname.split('/')[3] ] for fname in trainFiles ]
    trainData = np.array( list( zip( traiImagenData, labels )))
    print('Saved')
    np.save( cachedData, trainData )


#  import ipdb; ipdb.set_trace()

# Training settings
parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                    help='input batch size for training (default: 64)')
parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
                    help='input batch size for testing (default: 1000)')
parser.add_argument('--epochs', type=int, default=10, metavar='N',
                    help='number of epochs to train (default: 10)')
parser.add_argument('--lr', type=float, default=0.005, metavar='LR',
                    help='learning rate (default: 0.01)')
parser.add_argument('--momentum', type=float, default=0.3, metavar='M',
                    help='SGD momentum (default: 0.5)')
parser.add_argument('--no-cuda', action='store_true', default=False,
                    help='disables CUDA training')
parser.add_argument('--seed', type=int, default=1, metavar='S',
                    help='random seed (default: 1)')
parser.add_argument('--log-interval', type=int, default=10, metavar='N',
                    help='how many batches to wait before logging training status')
args = parser.parse_args()
args.cuda = not args.no_cuda and torch.cuda.is_available()

torch.manual_seed(args.seed)
if args.cuda:
    torch.cuda.manual_seed(args.seed)


kwargs = {'num_workers': 1, 'pin_memory': True} if args.cuda else {}
train_loader = torch.utils.data.DataLoader(
    [ i.tolist() for i in trainData ],
    batch_size=args.batch_size, shuffle=True, **kwargs)
test_loader = train_loader

xx = 3000

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 60, kernel_size=5 )
        self.conv2 = nn.Conv2d( 60, 120, kernel_size=5 )
        self.conv2_drop = nn.Dropout2d()
        self.fc1 = nn.Linear( xx, 800 )
        self.fc2 = nn.Linear( 800, 395)

    def forward(self, x):
        x = F.relu(F.max_pool2d(self.conv1(x), 2))
        x = F.relu(F.max_pool2d(self.conv2_drop(self.conv2(x)), 2))
        #  import ipdb; ipdb.set_trace()
        x = x.view(-1, xx )
        x = F.relu(self.fc1(x))
        x = F.dropout(x, training=self.training)
        x = self.fc2(x)
        return F.log_softmax(x)

model = Net()
if( path.exists( savedModel ) ):
    model.load_state_dict( torch.load( savedModel ) )

if args.cuda:
    model.cuda()

optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)

def train(epoch):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        if args.cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data), Variable(target)
        optimizer.zero_grad()
        output = model(data)
        #  import ipdb; ipdb.set_trace()
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % args.log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                100. * batch_idx / len(train_loader), loss.data[0]))

def test():
    model.eval()
    test_loss = 0
    correct = 0
    for data, target in test_loader:
        if args.cuda:
            data, target = data.cuda(), target.cuda()
        data, target = Variable(data, volatile=True), Variable(target)
        output = model(data)
        test_loss += F.nll_loss(output, target, size_average=False).data[0] # sum up batch loss
        pred = output.data.max(1, keepdim=True)[1] # get the index of the max log-probability
        correct += pred.eq(target.data.view_as(pred)).cpu().sum()

    test_loss /= len(test_loader.dataset)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))


for epoch in range(1, args.epochs + 1):
    try:
        train(epoch)
        test()
    except KeyboardInterrupt:
        torch.save( model.state_dict(), savedModel )
        print('Saved model')
        break





#  import ipdb; ipdb.set_trace()