#!/bin/sh
# Fetch the daily and weekly files. Data: TrainerGigs, https://trainergigs.com
curl -s https://trainergigs.com/ai-training-jobs-data.json -o daily.json
curl -s https://trainergigs.com/ai-training-jobs-weekly.csv -o weekly.csv
echo "Saved daily.json and weekly.csv"
