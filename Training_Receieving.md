## Accurate-User-Database-and-Training-Resource-Optimization

### Preprocessing

We performed data preprocessing in the following steps:

#### Training Receieving

* Checked for missing values and imputed with 0
* Removed duplicate rows
* Removed unwanted punctuations
* Fixed the datatypes
* Assigned weights to the role receiving
* Standerdized the error cost feature using StandardScaler()
* Normalized rest of the features using MinMaxScaler()
* Performed dimantionality reduction using principal component analysis(PCA)
  
