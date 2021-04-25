## Accurate-User-Database-and-Training-Resource-Optimization

One of the Accenture's Federal clients has a global supply chain and the system that they maintain for client tracks the procurement, distribution, maintenance, and retirement of their assets. The system contains more than 10 years of data. Every user in their system is assigned different roles abased on the functions that they need to perform. The goal of this project is to Create a dashboard that can be broken down by location that gives a list of the users that need training and the training area sorted by urgency.

### Preprocessing
* Removed duplicates 
* Changed the datatypes
* Imputed the missing data
* Created additional columns based on the calculations that we did from the preexisting ones 
* Removed the unnessacary columns 
* Performed some mathematical calculations to find the weights for disposal roles
* Standardized the error cost column using the StandardScaler 
* Normalized every other feature using the MinMaxScaler()  
* Performed dimensionality reduction by using Principal component analysis (PCA)
* Normalized rating
* Merged the orginal total cost to the result for reference
