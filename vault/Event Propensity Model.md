![[StellarAlgo-Full-Colour-Logo.png]]
# Event Propensity Model
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

| feature                          | featureraw                  | source                  | engineered   | description                                                                                                                                                                                                                                                     |
|:---------------------------------|:----------------------------|:------------------------|:-------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Tenure                           | tenure                      | Ticketing               | true         | Days between first ticketing purchase date to the latest event date for a customer                                                                                                                                                                              |
| Attendance                       | attendancePercent           | Ticketing               | true         | The attendance percentage for the season                                                                                                                                                                                                                        |
| Click Link                       | click_link                  | Marketing               | true         | Total number of activities a customer clicked an marketing email                                                                                                                                                                                                |
| Click to Open Ratio              | clickToOpenRatio            | Marketing               | true         | Total number of clicked marketing email devided by opened email                                                                                                                                                                                                 |
| Click to Send Ratio              | clickToSendRatio            | Marketing               | true         | Total number of clicked marketing email devided by sent email                                                                                                                                                                                                   |
| Purchase Days Out From Event     | daysOut                     | Ticketing               | true         | How many days out (bucketed) this potential purchase is from the event date. Possible values are Day-of, 1-3 days, 4-7 days or 8+ days                                                                                                                          |
| Internal Feature                 | did_purchase                | Ticketing               | true         | In Case a customer bought ticket for an event did_purchase is 1 else 0. Target variable for prediction                                                                                                                                                          |
| Internal Feature                 | dimCustomerMasterId         | Customer                | false        | SCV ID for the fan making the potential purchase. Not used for prediction                                                                                                                                                                                       |
| Distance to Venue                | distanceToVenue             | Customer                | false        | Physical distance of fan from venue                                                                                                                                                                                                                             |
| Event Date                       | eventDate                   | Ticketing               | false        | Event date that the game happened                                                                                                                                                                                                                               |
| Event Name                       | eventName                   | Ticketing               | false        | Event name of the game. Not used for prediction                                                                                                                                                                                                                 |
| Events Purchased                 | events_purchased            | Ticketing               | true         | Total number of events purchased prior to the potential purchase                                                                                                                                                                                                |
| Forward Records                  | forward_records             | Secondary               | true         | Total number of Ticket Exchange forward records in a season year for a customer                                                                                                                                                                                 |
| Event Day Purchase Frequency     | frequency_eventDay          | Ticketing               | true         | Percentage of games purchased prior to the potential purchase on the same day of the week                                                                                                                                                                       |
| Event Time Purchase Frequency    | frequency_eventTime         | Ticketing               | true         | Percentage of games purchased prior to the potential purchase at the same time of day                                                                                                                                                                           |
| Opponent Purchase Frequency      | frequency_opponent          | Ticketing               | true         | Percentage of games purchased prior to the potential purchase with the same opponent                                                                                                                                                                            |
| Gender                           | gender                      | Demographic Data        | false        | Gender of the buyer                                                                                                                                                                                                                                             |
| No. Inbound Emails to Rep        | inbound_email               | Touchpoint Data         | true         | Total number of inbound activity in email                                                                                                                                                                                                                       |
| No. Inbound Phonecalls to Rep    | inbound_phonecall           | Touchpoint Data         | true         | Total number of outbound activity in email                                                                                                                                                                                                                      |
| In Market                        | inMarket                    | Customer                | false        | Whether the fan making this potential purchase is considered in-market                                                                                                                                                                                          |
| In Person Contact                | inperson_contact            | Touchpoint Data         | true         | Total number of touchpoint acivities which contains MEETING, inPersonContact , appointment, Significant appointment                                                                                                                                             |
| Internal Feature                 | isBuyer                     | Ticketing               | true         | If a customer bought ticket the isBuyer is True else False                                                                                                                                                                                                      |
| Internal Feature                 | isNextYear_Buyer            | nan                     | true         | If a customer bought ticket for next season the isNextYear_Buyer is 1 else 0                                                                                                                                                                                    |
| Internal Feature                 | maxDaysOut                  | Ticketing               | true         | Maximum bound for the above bucket. NULL for 8+ days bucket. Not used for prediction                                                                                                                                                                            |
| Internal Feature                 | minDaysOut                  | Ticketing               | true         | Minimum bound for the above bucket. Not used for prediction                                                                                                                                                                                                     |
| Missed Games Streak 1            | missed_games_1              | Ticketing               | true         | Number of times the customer has missed 1 consecutive game                                                                                                                                                                                                      |
| Missed Games Streak 2            | missed_games_2              | Ticketing               | true         | Number of times the customer has missed 2 consecutive games                                                                                                                                                                                                     |
| Missed Games Streak Over 2       | missed_games_over_2         | Ticketing               | true         | Number of times the customer has missed more than 2 consecutive games                                                                                                                                                                                           |
| Opened Marketing Email           | open_email                  | Marketing               | true         | Total number of activities a customer opened an marketing email                                                                                                                                                                                                 |
| Open to Send Ratio               | openToSendRatio             | Marketing               | true         | Total number of opened marketing email devided by sent email                                                                                                                                                                                                    |
| No. Outbound Emails from Rep     | outbound_email              | Touchpoint Data         | true         | Total number of outband activity in email                                                                                                                                                                                                                       |
| No. Outbound Phonecalls from Rep | outbound_phonecall          | Touchpoint Data         | true         | Total number of outband activity in phone call                                                                                                                                                                                                                  |
| Phonecall                        | phonecall                   | Touchpoint Data         | true         | Total number of phonecall activities in touchpoint data                                                                                                                                                                                                         |
| Product                          | productGrouping             | dimProduct              | false        | Scored product                                                                                                                                                                                                                                                  |
| Recency                          | recency                     | Ticketing               | true         | Recency is based on the most recently attended event                                                                                                                                                                                                            |
| Recent Email Click Rate          | recent_clickRate            | Marketing               | true         | Total number of clicked email divided by total number of opened email. For true purchases (training), scoped to the week prior to purchase date. For potential purchases (training + scoring), scoped to the week prior to the date corresponding to minDaysOut |
| Recent Email Open Rate           | recent_openRate             | Marketing               | true         | Total number of opened email divided by total number of sent email. For true purchases (training), scoped to the week prior to purchase date. For potential purchases (training + scoring), scoped to the week prior to the date corresponding to minDaysOut    |
| Last Attendance Date             | recentDate                  | Ticketing               | true         | The last event date that a customer attended the game                                                                                                                                                                                                           |
| Time to Renew                    | renewedBeforeDays           | Ticketing               | true         | The number of days a customer bought a ticket before game                                                                                                                                                                                                       |
| No. Marketing Email Sends        | send_email                  | Marketing               | true         | Total number of activities a customer Sent an marketing email                                                                                                                                                                                                   |
| Tenure (Provided by Team)        | source_tenure               | Ticketing               | true         | Source tenure for the customer provided by the team                                                                                                                                                                                                             |
| Total Games Attended             | totalGames                  | Ticketing               | true         | Total attended games by customer, season and product                                                                                                                                                                                                            |
| Total Ticketing Spend            | totalSpent                  | Ticketing               | true         | Total amount of dollars spent for the season                                                                                                                                                                                                                    |
| Year                             | year                        | dimSeason               | false        | Scored season year                                                                                                                                                                                                                                              |
| Female                           | gender_F                    | Pycaret                 | true         | Gender of the fan is female                                                                                                                                                                                                                                     |
| Male                             | gender_M                    | Pycaret                 | true         | Gender of the fan is male                                                                                                                                                                                                                                       |
| Unknown Gender                   | gender_Unknown              | Pycaret                 | true         | Gender of the fan is unknown                                                                                                                                                                                                                                    |
| Not Married                      | maritalStatus_0             | Pycaret                 | true         | Fan is not married                                                                                                                                                                                                                                              |
| Married                          | maritalStatus_1             | Pycaret                 | true         | Fan is married                                                                                                                                                                                                                                                  |
| No Post Secondary Education      | education_0                 | Pycaret                 | true         | Fan has a record of post secondary education                                                                                                                                                                                                                    |
| Post Secondary Education         | education_1                 | Pycaret                 | true         | Fan does not have record of post secondary education                                                                                                                                                                                                            |
| Gender Not Available             | gender_not_available        | Pycaret                 | true         | The availability of the gender of the fan.                                                                                                                                                                                                                      |