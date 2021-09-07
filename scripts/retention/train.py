from pycaret.classification import *

#ALGORITHMS=['gbc', 'lightgmb', 'rf']
ALGORITHMS=['gbc']
FOLDS=2
METRIC="F1"

def train_models(df_train):

    print(df_train.head())

    setup(
        df_train, 
        target='isnextyear_buyer', 
        train_size = 0.8, 
        silent=True,
        numeric_features=[
            'attendancePercent',
            'distToVenue',
            'missed_games_1',
            'missed_games_2',
            'missed_games_over_2',
            'recency',
            'renewedBeforeDays',
            'source_tenure',
            'totalSpent'
        ]
    )
    
    model_matrix = compare_models(fold=FOLDS, sort=METRIC, include=ALGORITHMS)

    best_model = create_model(model_matrix)

    feature_importances = best_model.feature_importances_

    #tuned_model = tune_model(best_model, optimize=METRIC)

    return best_model, feature_importances
    
