from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from app import schemas


app = FastAPI()
# In-memory data storage
transactions: List[schemas.Transaction] = []
balances: Dict[str, int] = {}
total_available_points: int = 0
transactions_history: List[schemas.Transaction]=[]

@app.get("/")
def root():
    return {"message": "Hello Fetch Engineer!"}


# Add Points Endpoint
@app.post("/add")
def add_points(transaction: schemas.Transaction):
    global total_available_points
    # Add transaction to list
    transactions.append(transaction)
    transactions_history.append(transaction)
    
    # Update balance for the payer
    if transaction.payer not in balances:
        balances[transaction.payer] = 0
    balances[transaction.payer] += transaction.points

    total_available_points += transaction.points
    # Sort transactions by timestamp (oldest first)
    transactions.sort(key=lambda x: x.timestamp)
    
    return {"status": "success"}

# Spend Points Endpoint
@app.post("/spend")
def spend_points(spend_request: schemas.SpendRequest):
    global total_available_points
    points_to_spend = spend_request.points
    if points_to_spend <= 0:
        raise HTTPException(status_code=400, detail="Points to spend must be positive")

    # Temporary balances to track in-progress spending
    temp_balances = {}
    

    # Check if total points are enough to cover the spend request
    if points_to_spend > total_available_points:
        raise HTTPException(status_code=400, detail="Not enough points available to spend")

    # List to store the points spent from each payer
    points_spent: Dict[str, int] = {}

    for transaction in transactions:
        #FIXME: This skips the transactions instead we need to comeback to these transactions
        if points_to_spend <= 0 and transaction.points >= 0:
            continue
        
        payer = transaction.payer
        points_in_transaction = transaction.points

        if payer not in temp_balances:
            temp_balances[payer] = 0
        temp_balances[payer] += transaction.points
        
        # Check if the payer has enough points to spend if not update the points spent
        if temp_balances[payer] < 0:
            points_spent[payer]-=temp_balances[payer]
            points_to_spend-=temp_balances[payer]
            temp_balances[payer] = 0
            transaction.points = 0
            #We don't need to update the previous transaction since we have already spent all the possible points from them
            #We could also remove these transactions to reduce time spent sorting
            continue
            
        # Calculate the points we can spend from this transaction
        points_to_deduct = min(points_in_transaction, points_to_spend)

        # Check if spending these points would make the payer's balance go negative
        if temp_balances[payer] - points_to_deduct >= 0:
            # Temporarily reduce the payer's balance
            temp_balances[payer] -= points_to_deduct
            points_to_spend -= points_to_deduct

            # Update the transaction points
            transaction.points -= points_to_deduct

            # Track points spent from each payer
            if payer not in points_spent:
                points_spent[payer] = 0
            points_spent[payer] -= points_to_deduct
        

    for payer, points in points_spent.items():
        balances[payer] += points
        total_available_points+=points
    # Return the list of points spent per payer
    response = [{"payer": payer, "points": points} for payer, points in points_spent.items()]
    return response

# Get Balance Endpoint
@app.get("/balance")
def get_balance():
    return balances
