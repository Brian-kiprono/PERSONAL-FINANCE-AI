import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from collections import defaultdict

class AIEngine:
    def __init__(self, db):
        self.db = db
    
    def predict_spending(self, months_ahead=3):
        transactions = self.db.get_transactions()
        if not transactions:
            return {'predictions': [], 'trend': 'insufficient_data'}
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        
        monthly_expenses = df[df['type'] == 'expense'].groupby('month')['amount'].sum()
        
        if len(monthly_expenses) < 3:
            return {'predictions': [], 'trend': 'insufficient_data'}
        
        x = np.arange(len(monthly_expenses)).reshape(-1, 1)
        y = monthly_expenses.values
        
        model = LinearRegression()
        model.fit(x, y)
        
        future_months = np.arange(len(monthly_expenses), len(monthly_expenses) + months_ahead).reshape(-1, 1)
        predictions = model.predict(future_months)
        
        result = []
        last_date = pd.to_datetime(monthly_expenses.index[-1].start_time)
        for i, pred in enumerate(predictions):
            next_month = last_date + timedelta(days=32*(i+1))
            result.append({
                'month': next_month.strftime('%B %Y'),
                'predicted_spending': float(max(0, pred)),
                'confidence': float(0.7 + (len(monthly_expenses) / 100))
            })
        
        trend = 'increasing' if model.coef_[0] > 0 else 'decreasing' if model.coef_[0] < 0 else 'stable'
        
        return {'predictions': result, 'trend': trend}
    
    def get_budget_recommendations(self, year, month):
        summary = self.db.get_monthly_summary(year, month)
        category_breakdown = self.db.get_category_breakdown(year, month)
        
        if not category_breakdown:
            return []
        
        total_expense = summary['expense']
        recommendations = []
        
        for cat in category_breakdown:
            percentage = (cat['total'] / total_expense * 100) if total_expense > 0 else 0
            
            recommended_limit = cat['total']
            if percentage > 30:
                recommended_limit = cat['total'] * 0.85
                reason = "High spending detected - consider reducing"
            elif percentage < 10:
                recommended_limit = cat['total'] * 1.1
                reason = "You have room to increase budget"
            else:
                recommended_limit = cat['total']
                reason = "Current spending is balanced"
            
            recommendations.append({
                'category_name': cat['name'],
                'current_spending': cat['total'],
                'recommended_budget': round(recommended_limit, 2),
                'percentage_of_total': round(percentage, 2),
                'reason': reason,
                'icon': cat['icon']
            })
        
        return recommendations
    
    def analyze_saving_patterns(self):
        transactions = self.db.get_transactions()
        if not transactions:
            return {'message': 'Add more transactions for analysis'}
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        current_month = datetime.now().month
        last_3_months = df[df['date'] >= (datetime.now() - timedelta(days=90))]
        
        income = last_3_months[last_3_months['type'] == 'income']['amount'].sum()
        expenses = last_3_months[last_3_months['type'] == 'expense']['amount'].sum()
        savings = income - expenses
        
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        tips = []
        if savings_rate < 20:
            tips.append("Aim to save at least 20% of your income")
        if savings_rate > 30:
            tips.append("Excellent savings rate! Consider investing the surplus")
        
        category_spending = last_3_months[last_3_months['type'] == 'expense'].groupby('category_name')['amount'].sum().sort_values(ascending=False)
        
        if len(category_spending) > 0:
            top_category = category_spending.index[0]
            tips.append(f"Your highest expense is {top_category} - review if necessary")
        
        return {
            'total_income_3m': float(income),
            'total_expenses_3m': float(expenses),
            'savings': float(savings),
            'savings_rate': round(savings_rate, 2),
            'tips': tips
        }