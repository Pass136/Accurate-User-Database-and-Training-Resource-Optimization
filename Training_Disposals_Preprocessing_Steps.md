## Accurate-User-Database-and-Training-Resource-Optimization

### Preprocessing

 We performed data preprocessing in the following steps:
 
 #### Training Disposals
 
* Removed duplicates 
* Changed the datatypes
* Imputed the missing data
* Created additional columns based on the calculations that we did from the preexisting ones 
* Removed the unnessacary columns 
* Performed some mathematical calculations to find the weights for disposal roles
* Standardized the error cost column using the StandardScaler 
* Normalized every other feature using the MinMaxScaler()  
* Merged the orginal total cost to the result for reference
* Outer join two tables "top 10 highest scoring users" and orginal total cost and result tables by using common field "user"
* Removed the duplicate rows
* Generated new dashboard
* Renamed the new columns
* Removed the dupicate rows
