![[StellarAlgo-Full-Colour-Logo.png]]
# Retention Model
## Business Challenge

### How can we best identify those who are most likely to renew their current ticket package from those who are less likely to renew? 

The retention model aims to help prioritize customers during the renewal process for:

### Package Buyers
The retention model focusses on multi-game package buyers. Regardless of package type from a 'full season' ticket holder to a 'mini plan' buyer, the model looks at scoring a customer on how likely they are to renew that specific package for the next season.

To solve this problem, we use a binary classification model to assess from 0 to 100, how likely it is that an individual will renew their package. For more detail on binary classification models, see the *Binary Classification Model Explanation* below.

## Retention Score Availability

### CDP - Retention
Retention scores provided by the retention model are available in the CDP Data Analysis: retention page:

![[Pasted image 20230324143916.png]]

### CDP - Segment Builder
The retention scores are also available in the CDP Segment Builder:

![[Pasted image 20230324143408.png]]

## Features
The model is trained and scored using the following features:
- attendancepercent: percentage of games a fan has attended in a season
- disttovenue: how far a fan is from the venue
- missed_games_1: how many times a fan has missed 1 game
- missed_games_2: how many times a fan has missed 2 games in a row
- missed_games_over_2: how many times a fan has missed more than 2 games in a row
- recency: how many days since the fans last game attended
- renewedbeforedays: how many days before the first game of the season did the fan renew their package
- tenure: how many days since the fans first purchase with the team
- totalspent: total amount spent by a fan in the current season


## Additional Data
The following fields are also available along side the scores for additional data analysis:
- dimcustomermasterid
- lkupclientid
- mostrecentattendance
- product
- sascore
- scoredate
- seasonyear
- tenuredays

** see the data dictionary section below for full descriptions of each of these fields. **

## Algorithm
The retention model uses the light gradient-boosting machine (LightGBM) algorithm to assign a probabilty of renewal for each fan based on their package type. See the *Algorithm Explanation* section for more information on the LightGBM algorithm.

ex. Let's say Fan XYZ has the following values for each model feature:
- attendancepercent: 0.84
- disttovenue: 8
- missed_games_1: 3
- missed_games_2: 1
- missed_games_over_2: 0
- recency: 0
- renewedbeforedays: 42 
- tenure: 1264
- totalspent: $7010

The model will score this fan and assign a probability that they will renew their package:
* Score = 0.84

This means the model is suggesting that this fan is very likely to renew their ticket package, because their features look similar to a typical fan that renews their same ticket package.

## Model Performance
The retention model is evaluated based on 5 common machine learning performance metrics:

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

LightGBM is like a very smart and fast teacher who helps you learn things quickly.

Imagine you are learning to read and your teacher has a bunch of books with different stories in them. She wants to help you learn how to read faster, so she gives you the most important words from each story and puts them on flashcards. These are words that appear a lot in the stories and will help you understand what's going on.

LightGBM does something similar when it's trying to learn from data. Instead of books and flashcards, it has a big table of data with different columns that represent different things. For example, if we're trying to predict whether a person will buy a certain product or not, we might have columns for their age, gender, income, and so on.

LightGBM wants to find the most important columns, or "features," that will help it make accurate predictions. So it looks at all the columns and tries to figure out which ones are the most important. It does this by looking at lots of different examples of people who did or didn't buy the product, and seeing which columns were most helpful in predicting whether they would buy it or not.

Once LightGBM has figured out which columns are the most important, it uses those to make its predictions. It does this by building a tree - like a decision tree - where each node represents a decision based on one of the important columns. The tree splits the data into smaller and smaller groups, and eventually makes a prediction for each group based on the examples in that group.

Overall, LightGBM is really good at finding the most important features and making accurate predictions quickly. That's why it's such a popular algorithm for machine learning!

## Binary Classification Explanation

Imagine you have a box of apples, and you want to sort them into two groups: ripe apples and unripe apples. A binary classification model is like a super smart robot that can help you do this automatically.

The robot looks at each apple and decides whether it's ripe or unripe based on certain characteristics, like its color, size, and firmness. If the apple is ripe, the robot puts it in the "ripe" group, and if it's unripe, it puts it in the "unripe" group.

Similarly, a binary classification model looks at data and decides whether each example belongs to one of two groups, like "yes" or "no", "spam" or "not spam", "dog" or "cat", and so on. It does this by looking at certain characteristics, called "features," of each example. For example, if we're trying to classify whether an email is spam or not, the model might look at features like the words used in the email, the sender's email address, and the subject line.

The model learns from lots of examples of data that are already labeled as belonging to one of the two groups. It tries to find patterns in the features of each example that are associated with one group or the other. Once it has learned these patterns, it can use them to make predictions on new, unseen data.

So in short, a binary classification model is a tool that helps us sort things into two groups automatically based on certain characteristics, and it learns from examples of labeled data to do so.

## Pipeline Architecutre

![[retention-arch.png]]

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