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
* Normalizing the rating column
* Displayed the results by score from large to small
* Display top 10 users that have the higher scores
* Outer join two tables by using common field "user"
* Generated new dashboard
* Renamed the columns
* Show results by score from large to small
* Select user records that have rating >= 0
* Outer join the three table, using a common field "user"
* Checked if there is missing value (missing value here has a meaning, which means the user doesnt have specific role) 
* Calculating the total rating 
* Displayed the top 10 highest scoring users 
* Generated new table
* Displayed if the user has a specific role. If he has a role, the value = 1
* Displayed the top 10 highest scoring users
* Displayed the top 10 location in role disposals
* Displayed the top 10 location in role location
* Displayed the top 10 location in role receiving
* Calculated the total rating
* Sorted the location id in descending order
* Display the results by score from large to small
* Export table to s3 to create dashboard

  
