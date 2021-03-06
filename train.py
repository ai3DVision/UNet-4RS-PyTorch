# Freddy @DP&BH, uWaterloo
# Feb 4, 2018

import torch
import torch.nn as nn
import torchvision.datasets as dsets
import torchvision.transforms as transforms
from torch.autograd import Variable

from PIL import Image
import numpy as np
import pandas as pd
from tqdm import *
import sys
import math
import argparse
from distutils.version import LooseVersion

from utils import *
from unet import *


# Hyper params
num_epochs = 30
batch_size = 3
learning_rate = 1e-4

# global vars
#parser = argparse.ArgumentParser(description='Short sample app')
#parser.add_argument('-d', action="debug_mode", dest='debug',default=False)
debug = False
#debug = True
load_prev = True
load_prev = False
if(torch.cuda.is_available()):
    use_gpu = True


# Handle data
train_set =img_dataset_train(sys.argv[1],sys.argv[2],
        transform=transforms.Compose([
            transforms.Resize((512,512)),
            transforms.ToTensor()]))

val_set =img_dataset_val(sys.argv[3],sys.argv[4],
        transform=transforms.Compose([
            transforms.Resize((512,512)),
            transforms.ToTensor()]))

test_set =img_dataset_test(sys.argv[5],
        transform=transforms.Compose([
            transforms.Resize((512,512)),
            transforms.ToTensor()]))

train_loader = torch.utils.data.DataLoader(
        train_set,
        batch_size=batch_size, shuffle=True)

val_loader = torch.utils.data.DataLoader(
        val_set,
        batch_size=1, shuffle=False)

test_loader = torch.utils.data.DataLoader(
        test_set,
        batch_size=1, shuffle=False)
unet = Unet(3,6)

if(load_prev):
    unet.load_state_dict(torch.load('prev_model.pkl'))

if(use_gpu):
    unet.cuda()

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(unet.parameters(), lr=learning_rate)

counter = 0

print("len(train_loader) :" ,len(train_loader))
# Train the Model
for epoch in range(num_epochs):
    #if(debug and counter>=3): break
    if (epoch == 5):
        optimizer = torch.optim.Adam(unet.parameters(), lr=learning_rate/10)
    elif (epoch == 10):
        optimizer = torch.optim.Adam(unet.parameters(), lr=learning_rate/20)
    elif (epoch == 20):
        optimizer = torch.optim.Adam(unet.parameters(), lr=learning_rate/100)

    for i,(image,label) in enumerate(train_loader):
        if(debug and counter>=3):break
        counter+=1
        #print(counter)
        images = Variable(image)
        labels = Variable(label)


        #print(test*255)
        #test = Image.fromarray(np.uint8(test*255))
        #test.show()
        #print(to_np(labels))

        labels = rgb2onehot(labels)
        if(use_gpu):
            images = images.cuda()
            labels = labels.cuda()

        # Forward + Backward + Optimize
        optimizer.zero_grad()
        outputs = unet(images)
        #print(outputs.size(), labels.size())
        #target = labels.view(-1, )
        #print(outputs)
        #print(labels)
        loss = criterion(outputs, labels)
        #loss = dice_loss(outputs, labels)
        loss.backward()
        optimizer.step()


        if (i+1) % 100 == 0:
            print ('Epoch [%d/%d], Batch [%d/%d] Loss: %.6f'
                   %(epoch+1, num_epochs,i+1, len(train_loader),loss.data[0]))

    #if(epoch == 0 or epoch % 20 != 0):
    #    continue

    ''' val '''
    print('Validation: ')
    accs = []
    for i,(image, label, name, (w,h)) in enumerate(val_loader):
        image = Variable(image).cuda()
        img = unet(image)
        img = onehot2rgb(img)
        
        # acc 
        label = rgb2onehot(Variable(label))
        acc = simple_acc(img,label)# Truth_Positive / NumberOfPixels
        accs.append(acc)
        print('%s acc: %.2f%%' % (str(name[0]), 100*acc))

        img = np.uint8(img[0]*255)
        img = Image.fromarray(img, 'RGB')
        img = img.resize((w.numpy(),h.numpy()))
        #img.show()
        img.save(sys.argv[6] + '/val_' + str(epoch) + '_' + str(i)+ '.png')
    print('Overall acc- all pics: %.2f%%' % (100*sum(accs)/float(len(accs)) ))
       
    ''' test '''
    print('running test set... ')
    for i,(image,(w,h)) in enumerate(tqdm(test_loader)):
        image = Variable(image).cuda()
        img = unet(image)
        #acc = simple_acc(outputs,labels)# Truth_Positive / NumberOfPixels
        #print(acc)
        img = onehot2rgb(img)
        img = np.uint8(img[0]*255)
        img = Image.fromarray(img, 'RGB')
        img = img.resize((w.numpy(),h.numpy()))
        #img.show()

        img.save(sys.argv[6] + '/test_' + str(epoch) + '_' + str(i)+ '.png')

    # save Model
    if (not debug):
        torch.save(unet.state_dict(),'prev_model.pkl')



