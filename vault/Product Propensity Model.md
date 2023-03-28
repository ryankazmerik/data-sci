![[StellarAlgo-Full-Colour-Logo.png]]
# Product Propensity Model
## Business Challenge

### How can we best identify and activate on our existing fans for a larger commitment to attendance in future games?

The product propensity model aims to generate the best potential leads for:

### Package Buyers Upsells
* Full Season Buyers - what half season package buyers, and mini plan buyers may be good leads to purchase a full season package?
* Half Season Buyers -  what mini plan buyers may be good leads to purchase a half season package?
	  
### Individual Ticket Buyers Upsells 
* What individual ticket buyers may be good leads to purchase any type of package?*

To solve this problem, we use a multi-class classification model to assess what package type might be best for each fan. For more detail on multi-class classification models, see the *Multi-class Model Explanation* section below.

## Lead Availability

### CDP - Lead Recommender
Leads provided by the product propensity model are available in the CDP Lead Recommender:

![[Pasted image 20230316104429.png]]

Package leads for every product are capped at the top 200 until they take action. Top leads may still show up on the next day if their propensity outweighs their last action date.

Individual leads are capped at 2000 until they take action. Top Leads who have been stale for >90 days will show up again and be flagged as fresh for Sales team to start re-engaging/warming them up again.

### CDP - Segment Builder
A larger list of leads are also available in the CDP Segment Builder:

![[Pasted image 20230316102500.png]]

How many leads are available can be configured on a team by team basis in the CDP. A target size of 50,000 leads is recommended for creating segments via the segment builder.



## Features
The model is trained and scored using the following features:
* atp_last : the average ticket price from last season
* attended_last : how many games the fan attended last season
* attended_prior : how many games the fan attended in all past seasons
* events_last : how many events the fan purchased last season
* events_prior : how many events the fan purchased in all past seasons
* tenure : how many days since the fans first purchase with the tea


## Additional Data
The following fields are also available along side the scores for additional data analysis:
* attendedpct_prior
* attendedpct_last
* attendance_current
* clientcode
* dimcustomermasterid
* distance
* events_current
* lkupclientid
* product_current
* product_last
* seasonyear
* spend_current
* volume_current
* sends
* sends_prior
* opens
* opens_prior
* date_last_send
* date_last_touch
* date_last_save

** see the data dictionary section below for full descriptions of each of these fields. **

## Algorithm
The product propensity model uses a random forest tree-based algorithm to assign a probabilty to each fan for each package type. See the *Algorithm Explanation* section for more information on the random forest algorithm.

ex. Let's say Fan XYZ has the following values for each model feature:
* atp_last = $320
* attended_last = 24
* attended_prior = 140
* events_last = 26
* events_prior = 155
* tenure = 1056

The model will score this fan and assign a probability for each package type:
* Full Season = 0.25
* Half Season = 0.55
* Mini Plan = 0.20

This means the model is suggesting that this fan may be a good candidate for a Half Season package, because their features look most similar to a typical Half Season fan.

## Model Performance
The product propensity model is evaluated based on 5 common machine learning performance metrics:

### Accuracy
Accuracy is a common performance metric used in machine learning that measures the overall correctness of a model's predictions. It is calculated by dividing the number of correct predictions by the total number of predictions made. It is expressed as a percentage and can range from 0% to 100%. While accuracy can be a useful metric, it can sometimes be misleading if the classes in the dataset are imbalanced.
    
### Precision
Precision is a performance metric that measures how many of the positive predictions made by a model are actually correct. It is calculated by dividing the number of true positives (i.e., correctly classified positive examples) by the sum of true positives and false positives (i.e., incorrectly classified positive examples). Precision is useful in situations where false positives are costly or undesirable.

### Recall
Recall is a performance metric that measures how many of the actual positive examples in a dataset were correctly identified by the model. It is calculated by dividing the number of true positives by the sum of true positives and false negatives (i.e., positive examples that were incorrectly classified as negative). Recall is useful in situations where false negatives are costly or undesirable.
    
### F1 Score
The F1 score is a performance metric that is used to balance the trade-off between precision and recall. It is the harmonic mean of precision and recall and is calculated by dividing 2 times the product of precision and recall by their sum. The F1 score ranges from 0 to 1, where 1 indicates perfect precision and recall, and 0 indicates poor performance.

### AUC (Area Under the ROC Curve)
AUC is a performance metric that measures the ability of a model to distinguish between positive and negative examples. It is calculated by plotting the true positive rate (TPR) against the false positive rate (FPR) at various threshold settings, and calculating the area under the resulting curve. The AUC ranges from 0.5 (random classification) to 1 (perfect classification), with higher values indicating better performance. AUC is often used in binary classification problems where the classes are balanced, but can also be used in multi-class problems.

## Algorithm Explanation

Random Forest is a group of decision trees that work together to solve a problem.

Imagine you have a bunch of toys on the floor and you want to put them away in the right boxes. You ask your friends for help, but they might make mistakes. So, you ask many friends to help you, and you give each friend a different set of toys to put away.

Each friend decides where to put each toy by asking questions like, "Is this toy soft or hard?" or "Is this toy blue or green?" based on what they see. They keep asking questions together until they put all their toys away.

When all your friends are done, you can look at all the toys in their correct boxes, and you can be confident that the toys are put away correctly.

That's what Random Forest does. It uses many decision trees that work together, and each tree asks different questions to help solve a problem. When all the trees are done, they vote on the best answer, and that's the answer the Random Forest gives you.

## Multi-class Model Explanation

A multi-classification model is a type of machine learning model that is designed to classify data points into multiple classes or categories.

In a multi-classification problem, there are more than two possible outcomes or classes. For example, a model might be trained to classify images of animals into categories such as dogs, cats, and birds.

A common approach is to use an ensemble of binary classifiers, where each classifier is trained to distinguish between two classes. The final prediction is then made by combining the outputs of all the binary classifiers.

To evaluate the performance of a multi-classification model, metrics such as accuracy, precision, recall, and F1 score can be used. These metrics measure how well the model is able to correctly classify data points into the correct classes.

Overall, a multi-classification model is a powerful tool for solving complex classification problems with multiple outcomes, and can be used in a wide range of applications, from image classification to natural language processing.

## Pipeline Architecutre

![[Pasted image 20230316101435.png]]

## Data Dictionary
Below is a full list of features and their definitions:
```
[

{

"feature": "Tenure",

"featureraw": "tenure",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Days between first ticketing purchase date to the latest event date for a customer"

},

{

"feature": "Attendance",

"featureraw": "attendancePercent",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "The attendance percentage for the season"

},

{

"feature": "Click Link",

"featureraw": "click_link",

"datatype": "int64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of activities a customer clicked an marketing email"

},

{

"feature": "Click to Open Ratio",

"featureraw": "clickToOpenRatio",

"datatype": "float64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of clicked marketing email devided by opened email"

},

{

"feature": "Click to Send Ratio",

"featureraw": "clickToSendRatio",

"datatype": "float64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of clicked marketing email devided by sent email"

},

{

"feature": "Received Credits After Refund",

"featureraw": "credits_after_refund",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Total amonut of credit a customer has after getting refund"

},

{

"feature": "Internal Feature",

"featureraw": "customerNumber",

"datatype": "object",

"source": "dimCustomer table",

"engineered": "false",

"description": "Source ticketing account number"

},

{

"feature": "Purchase Days Out From Event",

"featureraw": "daysOut",

"datatype": "object",

"source": "Ticketing",

"engineered": "true",

"description": "How many days out (bucketed) this potential purchase is from the event date. Possible values are Day-of, 1-3 days, 4-7 days or 8+ days"

},

{

"feature": "Internal Feature",

"featureraw": "did_purchase",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "In Case a customer bought ticket for an event did_purchase is 1 else 0. Target variable for prediction"

},

{

"feature": "Internal Feature",

"featureraw": "dimCustomerMasterId",

"datatype": "int64",

"source": "Customer",

"engineered": "false",

"description": "SCV ID for the fan making the potential purchase. Not used for prediction"

},

{

"feature": "Internal Feature",

"featureraw": "dimCustomerMasterId",

"datatype": "int64",

"source": "dimCustomerMaster table",

"engineered": "false",

"description": "SCV ID for the fan making the potential purchase. Not used for prediction"

},

{

"feature": "Distance to Venue",

"featureraw": "distanceToVenue",

"datatype": "float64",

"source": "Customer",

"engineered": "false",

"description": "Physical distance of fan from venue"

},

{

"feature": "Distance to Venue",

"featureraw": "distToVenue",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Physical distance of fan from venue"

},

{

"feature": "Event Date",

"featureraw": "eventDate",

"datatype": "datetime64",

"source": "Ticketing",

"engineered": "false",

"description": "Event date that the game happened"

},

{

"feature": "Event Name",

"featureraw": "eventName",

"datatype": "object",

"source": "Ticketing",

"engineered": "false",

"description": "Event name of the game. Not used for prediction"

},

{

"feature": "Events Purchased",

"featureraw": "events_purchased",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Total number of events purchased prior to the potential purchase"

},

{

"feature": "Forward Records",

"featureraw": "forward_records",

"datatype": "int64",

"source": "Secondary",

"engineered": "true",

"description": "Total number of Ticket Exchange forward records in a season year for a customer"

},

{

"feature": "Event Day Purchase Frequency",

"featureraw": "frequency_eventDay",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Percentage of games purchased prior to the potential purchase on the same day of the week"

},

{

"feature": "Event Time Purchase Frequency",

"featureraw": "frequency_eventTime",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Percentage of games purchased prior to the potential purchase at the same time of day"

},

{

"feature": "Opponent Purchase Frequency",

"featureraw": "frequency_opponent",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Percentage of games purchased prior to the potential purchase with the same opponent"

},

{

"feature": "Gender",

"featureraw": "gender",

"datatype": "object",

"source": "Demographic Data",

"engineered": "false",

"description": "Gender of the buyer"

},

{

"feature": "No. Inbound Emails to Rep",

"featureraw": "inbound_email",

"datatype": "int64",

"source": "Touchpoint Data",

"engineered": "true",

"description": "Total number of inbound activity in email"

},

{

"feature": "No. Inbound Phonecalls to Rep",

"featureraw": "inbound_phonecall",

"datatype": "int64",

"source": "Touchpoint Data",

"engineered": "true",

"description": "Total number of outbound activity in email"

},

{

"feature": "In Market",

"featureraw": "inMarket",

"datatype": "object",

"source": "Customer",

"engineered": "false",

"description": "Whether the fan making this potential purchase is considered in-market"

},

{

"feature": "In Person Contact",

"featureraw": "inperson_contact",

"datatype": "int64",

"source": "Touchpoint Data",

"engineered": "true",

"description": "Total number of touchpoint acivities which contains MEETING, inPersonContact , appointment, Significant appointment"

},

{

"feature": "Stadium Availability",

"featureraw": "is_Lockdown",

"datatype": "int64",

"source": "nan",

"engineered": "true",

"description": "If a most of the days in a year was lockdown during Covid then is_Lockdown is 1 else 0"

},

{

"feature": "Internal Feature",

"featureraw": "isBuyer",

"datatype": "object",

"source": "Ticketing",

"engineered": "true",

"description": "If a customer bought ticket the isBuyer is True else False"

},

{

"feature": "Internal Feature",

"featureraw": "isNextYear_Buyer",

"datatype": "int64",

"source": "nan",

"engineered": "true",

"description": "If a customer bought ticket for next season the isNextYear_Buyer is 1 else 0"

},

{

"feature": "Internal Feature",

"featureraw": "maxDaysOut",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Maximum bound for the above bucket. NULL for 8+ days bucket. Not used for prediction"

},

{

"feature": "Internal Feature",

"featureraw": "minDaysOut",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Minimum bound for the above bucket. Not used for prediction"

},

{

"feature": "Missed Games Streak 1",

"featureraw": "missed_games_1",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Number of times the customer has missed 1 consecutive game"

},

{

"feature": "Missed Games Streak 2",

"featureraw": "missed_games_2",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Number of times the customer has missed 2 consecutive games "

},

{

"feature": "Missed Games Streak Over 2",

"featureraw": "missed_games_over_2",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Number of times the customer has missed more than 2 consecutive games"

},

{

"feature": "No. Games per Season",

"featureraw": "NumberofGamesPerSeason",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Total number of games in a season year"

},

{

"feature": "Opened Marketing Email",

"featureraw": "open_email",

"datatype": "int64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of activities a customer opened an marketing email"

},

{

"feature": "Open to Send Ratio",

"featureraw": "openToSendRatio",

"datatype": "float64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of opened marketing email devided by sent email"

},

{

"feature": "No. Outbound Emails from Rep",

"featureraw": "outbound_email",

"datatype": "int64",

"source": "Touchpoint Data",

"engineered": "true",

"description": "Total number of outband activity in email"

},

{

"feature": "No. Outbound Phonecalls from Rep",

"featureraw": "outbound_phonecall",

"datatype": "int64",

"source": "Touchpoint Data",

"engineered": "true",

"description": "Total number of outband activity in phone call"

},

{

"feature": "Phonecall",

"featureraw": "phonecall",

"datatype": "int64",

"source": "Touchpoint Data",

"engineered": "true",

"description": "Total number of phonecall activities in touchpoint data"

},

{

"feature": "Product",

"featureraw": "productGrouping",

"datatype": "object",

"source": "dimProduct",

"engineered": "false",

"description": "Scored product"

},

{

"feature": "Recency",

"featureraw": "recency",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Recency is based on the most recently attended event"

},

{

"feature": "Recent Email Click Rate",

"featureraw": "recent_clickRate",

"datatype": "float64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of clicked email divided by total number of opened email. For true purchases (training), scoped to the week prior to purchase date. For potential purchases (training + scoring), scoped to the week prior to the date corresponding to minDaysOut"

},

{

"feature": "Recent Email Open Rate",

"featureraw": "recent_openRate",

"datatype": "float64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of opened email divided by total number of sent email. For true purchases (training), scoped to the week prior to purchase date. For potential purchases (training + scoring), scoped to the week prior to the date corresponding to minDaysOut"

},

{

"feature": "Last Attendance Date",

"featureraw": "recentDate",

"datatype": "object",

"source": "Ticketing",

"engineered": "true",

"description": "The last event date that a customer attended the game"

},

{

"feature": "Attendance Month - January",

"featureraw": "recentDate_month_1",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (1 = January)"

},

{

"feature": "Attendance Month - October",

"featureraw": "recentDate_month_10",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (10 = October)"

},

{

"feature": "Attendance Month - November",

"featureraw": "recentDate_month_11",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (11 = November)"

},

{

"feature": "Attendance Month - February",

"featureraw": "recentDate_month_2",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (2 = February"

},

{

"feature": "Attendance Month - March",

"featureraw": "recentDate_month_3",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (3 =March)"

},

{

"feature": "Attendance Month - April",

"featureraw": "recentDate_month_4",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (4 = April)"

},

{

"feature": "Attendance Month - May",

"featureraw": "recentDate_month_5",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (5 = May)"

},

{

"feature": "Attendance Month - June",

"featureraw": "recentDate_month_6",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (6 = June)"

},

{

"feature": "Attendance Month - July",

"featureraw": "recentDate_month_7",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (7 = July)"

},

{

"feature": "Attendance Month - August",

"featureraw": "recentDate_month_8",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (8 = August)"

},

{

"feature": "Attendance Month - September",

"featureraw": "recentDate_month_9",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (9 = September)"

},

{

"feature": "Attendance Day - Sunday",

"featureraw": "recentDate_weekday_0",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (0 = Sunday)"

},

{

"feature": "Attendance Day - Monday",

"featureraw": "recentDate_weekday_1",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (1 = Monday)"

},

{

"feature": "Attendance Day - Tuesday",

"featureraw": "recentDate_weekday_2",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (2 = Tuesday)"

},

{

"feature": "Attendance Day - Friday",

"featureraw": "recentDate_weekday_5",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (5 = Friday)"

},

{

"feature": "Attendance Day - Saturday",

"featureraw": "recentDate_weekday_6",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (6 = Saturday)"

},

{

"feature": "Time to Renew",

"featureraw": "renewedBeforeDays",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "The number of days a customer bought a ticket before game"

},

{

"feature": "No. Marketing Email Sends",

"featureraw": "send_email",

"datatype": "int64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of activities a customer Sent an marketing email"

},

{

"feature": "Tenure (Provided by Team)",

"featureraw": "source_tenure",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Source tenure for the customer provided by the team"

},

{

"feature": "Total Games Attended",

"featureraw": "totalGames",

"datatype": "int64",

"source": "Ticketing",

"engineered": "true",

"description": "Total attended games by customer, season and product"

},

{

"feature": "Total Ticketing Spend",

"featureraw": "totalSpent",

"datatype": "float64",

"source": "Ticketing",

"engineered": "true",

"description": "Total amount of dollars spent for the season"

},

{

"feature": "No. Email Marketing Unsubscribes",

"featureraw": "unsubscribe_email",

"datatype": "int64",

"source": "Marketing",

"engineered": "true",

"description": "Total number of activities a customer unsibscribed an marketing email"

},

{

"feature": "Urbanicity",

"featureraw": "urbanicity",

"datatype": "object",

"source": "Demographic Data",

"engineered": "true",

"description": "Represents if the customer lives in an urban or suburban area"

},

{

"feature": "Year",

"featureraw": "year",

"datatype": "int64",

"source": "dimSeason",

"engineered": "false",

"description": "Scored season year"

},

{

"feature": "First Day of Month",

"featureraw": "recentDate_is_month_start_1",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents if the event date was the first day of the month"

},

{

"feature": "Last Day of Month",

"featureraw": "recentDate_is_month_end_1",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents if the event date was the last day of the month"

},

{

"feature": "Attendance Month - December",

"featureraw": "recentDate_month_12",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the month of the recentDate feature (12 = December)"

},

{

"feature": "Attendance Day - Wednesday",

"featureraw": "recentDate_weekday_3",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (3 = Wednesday)"

},

{

"feature": "Attendance Day - Thursday",

"featureraw": "recentDate_weekday_4",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents the day of the recentDate feature (4 = Thursday)"

},

{

"feature": "Not First Day of Month",

"featureraw": "recentDate_is_month_start_0",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents if the event date was not the first day of the month"

},

{

"feature": "Not Last Day of Month",

"featureraw": "recentDate_is_month_end_0",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Represents if the event date was not the last day of the month"

},

{

"feature": "Female",

"featureraw": "gender_F",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Gender of the fan is female"

},

{

"feature": "Male",

"featureraw": "gender_M",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Gender of the fan is male"

},

{

"feature": "Unknown Gender",

"featureraw": "gender_Unknown",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Gender of the fan is unknown"

},

{

"feature": "Not Married",

"featureraw": "maritalStatus_0",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Fan is not married"

},

{

"feature": "Married",

"featureraw": "maritalStatus_1",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Fan is married"

},

{

"feature": "No Post Secondary Education",

"featureraw": "education_0",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Fan has a record of post secondary education"

},

{

"feature": "Post Secondary Education",

"featureraw": "education_1",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "Fan does not have record of post secondary education"

},

{

"feature": "Gender Not Available",

"featureraw": "gender_not_available",

"datatype": "object",

"source": "Pycaret",

"engineered": "true",

"description": "The availability of the gender of the fan."

}

]
```
