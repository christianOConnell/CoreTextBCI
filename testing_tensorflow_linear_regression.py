import numpy as np
from sklearn import datasets
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# Create dataset
X, y = datasets.make_regression(
    n_samples=1000, n_features=10, noise=5, random_state=4)
y = y.reshape(-1, 1)

# Normalize the data
X_scaler = MinMaxScaler()
X_scaled = X_scaler.fit_transform(X)
y_scaler = MinMaxScaler()
y_scaled = y_scaler.fit_transform(y)

# Split the data into training and testing
X_train, X_test, y_train, y_test = train_test_split(
  X_scaled, y_scaled, test_size=0.33, random_state=42)


class Data(Dataset):
  '''Dataset Class to store the samples and their corresponding labels, 
  and DataLoader wraps an iterable around the Dataset to enable easy access to the samples.
  '''

  def __init__(self, X: np.ndarray, y: np.ndarray) -> None:

    # need to convert float64 to float32 else 
    # will get the following error
    # RuntimeError: expected scalar type Double but found Float
    self.X = torch.from_numpy(X.astype(np.float32))
    self.y = torch.from_numpy(y.astype(np.float32))
    self.len = self.X.shape[0]
  
  def __getitem__(self, index: int) -> tuple:
    return self.X[index], self.y[index]

  def __len__(self) -> int:
    return self.len
  
# Generate the training dataset
traindata = Data(X_train, y_train)

batch_size = 64
# tells the data loader instance how many sub-processes to use for data loading
# if the num_worker is zero (default) the GPU has to weight for CPU to load data
# Theoretically, greater the num_workers, 
# more efficiently the CPU load data and less the GPU has to wait
num_workers = 0

# Load the training data into data loader with the 
# respective batch_size and num_workers
trainloader = DataLoader(traindata, batch_size=batch_size, 
                         shuffle=True, num_workers=num_workers)


class LinearRegression(nn.Module):
  '''Linear Regression Model
  '''

  def __init__(self, input_dim: int, hidden_dim: int, output_dim: int) -> None:
    '''The network has 4 layers
         - input layer
         - hidden layer
         - hidden layer
         - output layer
    '''
    super(LinearRegression, self).__init__()
    self.input_to_hidden = nn.Linear(input_dim, hidden_dim)
    self.hidden_layer_1 = nn.Linear(hidden_dim, hidden_dim)
    self.hidden_layer_2 = nn.Linear(hidden_dim, hidden_dim)
    self.hidden_to_output = nn.Linear(hidden_dim, output_dim)

  def forward(self, x: torch.Tensor) -> torch.Tensor:
    # no activation and no softmax at the end
    x = self.input_to_hidden(x)
    x = self.hidden_layer_1(x)
    x = self.hidden_layer_2(x)
    x = self.hidden_to_output(x)
    return x
  
# number of features (len of X cols)
input_dim = X_train.shape[1]
# number of hidden layers
hidden_layers = 50
# output dimension is 1 because of linear regression
output_dim = 1
# initiate the linear regression model
model = LinearRegression(input_dim, hidden_layers, output_dim)
print(model)

# criterion to computes the loss between input and target
criterion = nn.MSELoss()
# optimizer that will be used to update weights and biases
optimizer = torch.optim.SGD(model.parameters(), lr=0.1)

# start training
epochs = 1000
for epoch in range(epochs):
  running_loss = 0.0
  for i, (inputs, labels) in enumerate(trainloader):
    # inputs, labels = data

    # forward propagation
    outputs = model(inputs)
    loss = criterion(outputs, labels)

    # set optimizer to zero grad 
    # to remove previous epoch gradients
    optimizer.zero_grad()

    # backward propagation
    loss.backward()

    # optimize
    optimizer.step()
    running_loss += loss.item()

  # display statistics
  if not ((epoch + 1) % (epochs // 10)):
    print(f'Epochs:{epoch + 1:5d} | ' \
          f'Batches per epoch: {i + 1:3d} | ' \
          f'Loss: {running_loss / (i + 1):.10f}')
    
testdata = Data(X_test, y_test)
testloader = DataLoader(testdata, batch_size=batch_size, 
                        shuffle=True, num_workers=num_workers)

# Validate trained model using the test dataset
with torch.no_grad():
  loss = 0
  for i, (inputs, labels) in enumerate(testloader):
    # calculate output by running through the network
    predictions = model(inputs)
    labels = torch.from_numpy(y_scaler.inverse_transform(labels))
    predictions = torch.from_numpy(y_scaler.inverse_transform(predictions))
    loss += F.mse_loss(predictions, labels)
  print(f'MSE Loss: {loss / (i + 1):.5f}')
