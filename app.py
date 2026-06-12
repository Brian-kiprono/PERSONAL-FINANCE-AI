from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_socketio import SocketIO, emit
from database import Database
from ai_engine import AIEngine
from datetime import datetime
import secrets
import csv
import io
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from threading import Lock
import time
# Add at the top of app.py
from config import get_config
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration
config = get_config()
app.config.from_object(config)

# Use environment variable for secret key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Database path from environment
db = Database(os.environ.get('DATABASE_PATH', 'finance.db'))

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['CACHE_TYPE'] = 'SimpleCache'

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
thread = None
thread_lock = Lock()

db = Database()
ai = AIEngine(db)

# Background thread for real-time updates
def background_updates():
    """Background thread that sends real-time updates to clients"""
    while True:
        time.sleep(5)  # Update every 5 seconds
        try:
            # Get latest stats
            now = datetime.now()
            current_month_summary = db.get_monthly_summary(now.year, now.month)
            
            # Get recent transactions
            recent_transactions = db.get_transactions(limit=10)
            
            # Get spending trend data
            last_6_months = []
            monthly_totals = []
            for i in range(5, -1, -1):
                d = datetime(now.year, now.month - i, 1) if now.month - i > 0 else datetime(now.year - 1, now.month - i + 12, 1)
                month_summary = db.get_monthly_summary(d.year, d.month)
                last_6_months.append(d.strftime('%b %Y'))
                monthly_totals.append(month_summary['expense'])
            
            # Prepare real-time data
            realtime_data = {
                'timestamp': datetime.now().isoformat(),
                'current_income': current_month_summary['income'],
                'current_expense': current_month_summary['expense'],
                'current_savings': current_month_summary['income'] - current_month_summary['expense'],
                'recent_transactions': recent_transactions[:5],
                'spending_trend': {
                    'months': last_6_months,
                    'values': monthly_totals
                },
                'last_updated': datetime.now().strftime('%H:%M:%S')
            }
            
            # Emit to all connected clients
            socketio.emit('realtime_update', realtime_data)
            
        except Exception as e:
            print(f"Error in background update: {e}")

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_updates)
    emit('connected', {'data': 'Connected to real-time finance tracker'})

@socketio.on('request_update')
def handle_request_update():
    """Handle manual update request from client"""
    send_realtime_update()

def send_realtime_update():
    """Send immediate real-time update"""
    now = datetime.now()
    current_month_summary = db.get_monthly_summary(now.year, now.month)
    recent_transactions = db.get_transactions(limit=10)
    
    # Get category breakdown for pie chart
    category_breakdown = db.get_category_breakdown(now.year, now.month)
    
    # Create Plotly pie chart
    if category_breakdown:
        fig = go.Figure(data=[go.Pie(
            labels=[c['name'] for c in category_breakdown],
            values=[c['total'] for c in category_breakdown],
            hole=.3,
            marker=dict(colors=[c['color'] for c in category_breakdown]),
            textinfo='label+percent',
            textposition='auto'
        )])
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            showlegend=True,
            legend=dict(font=dict(color='white'))
        )
        pie_chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
    else:
        pie_chart_json = None
    
    # Create Plotly line chart for spending trend
    last_6_months = []
    monthly_totals = []
    for i in range(5, -1, -1):
        d = datetime(now.year, now.month - i, 1) if now.month - i > 0 else datetime(now.year - 1, now.month - i + 12, 1)
        month_summary = db.get_monthly_summary(d.year, d.month)
        last_6_months.append(d.strftime('%b %Y'))
        monthly_totals.append(month_summary['expense'])
    
    fig_line = go.Figure(data=[go.Scatter(
        x=last_6_months,
        y=monthly_totals,
        mode='lines+markers',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=8, color='#6366f1'),
        fill='tozeroy',
        fillcolor='rgba(99, 102, 241, 0.1)'
    )])
    fig_line.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Amount ($)'),
        hovermode='x unified'
    )
    line_chart_json = json.dumps(fig_line, cls=PlotlyJSONEncoder)
    
    # Prepare update data
    update_data = {
        'current_income': current_month_summary['income'],
        'current_expense': current_month_summary['expense'],
        'current_savings': current_month_summary['income'] - current_month_summary['expense'],
        'recent_transactions': recent_transactions[:5],
        'pie_chart': pie_chart_json,
        'line_chart': line_chart_json,
        'last_updated': datetime.now().strftime('%H:%M:%S')
    }
    
    socketio.emit('immediate_update', update_data)

# Page routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/transactions')
def transactions_page():
    return render_template('transactions.html')

@app.route('/categories')
def categories_page():
    return render_template('categories.html')

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/predictions')
def predictions_page():
    return render_template('predictions.html')

@app.route('/visualizations')
def visualizations_page():
    return render_template('visualizations.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')

# API routes
@app.route('/api/stats')
def get_stats():
    now = datetime.now()
    current_month_summary = db.get_monthly_summary(now.year, now.month)
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1
    last_month_summary = db.get_monthly_summary(last_month_year, last_month)
    
    transactions = db.get_transactions(limit=1000)
    avg_monthly = 0
    if transactions:
        df_months = set()
        for t in transactions:
            date_obj = datetime.strptime(t['date'], '%Y-%m-%d')
            df_months.add((date_obj.year, date_obj.month))
        if df_months:
            total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
            avg_monthly = total_expense / len(df_months)
    
    return jsonify({
        'current_month_income': current_month_summary['income'],
        'current_month_expense': current_month_summary['expense'],
        'current_month_savings': current_month_summary['income'] - current_month_summary['expense'],
        'previous_month_expense': last_month_summary['expense'],
        'avg_monthly_expense': round(avg_monthly, 2),
        'transaction_count': len(transactions)
    })

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    trans_id = request.args.get('id', type=int)
    limit = request.args.get('limit', 100, type=int)
    
    if trans_id:
        transaction = db.get_transactions(trans_id=trans_id)
        return jsonify(transaction) if transaction else jsonify({'error': 'Not found'}), 404
    
    transactions = db.get_transactions(limit=min(limit, 500))
    return jsonify(transactions)

@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    required = ['amount', 'description', 'date', 'type']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    trans_id = db.add_transaction(
        data['amount'],
        data['description'],
        data['date'],
        data.get('category_id'),
        data['type']
    )
    # Send real-time update after transaction
    send_realtime_update()
    return jsonify({'id': trans_id, 'success': True, 'message': 'Transaction created'}), 201

@app.route('/api/transactions/<int:trans_id>', methods=['PUT'])
def update_transaction(trans_id):
    data = request.json
    updated = db.update_transaction(
        trans_id,
        amount=data.get('amount'),
        description=data.get('description'),
        date=data.get('date'),
        category_id=data.get('category_id'),
        trans_type=data.get('type')
    )
    if updated:
        send_realtime_update()
        return jsonify({'success': True, 'message': 'Transaction updated'})
    return jsonify({'error': 'Transaction not found'}), 404

@app.route('/api/transactions/<int:trans_id>', methods=['DELETE'])
def delete_transaction(trans_id):
    deleted = db.delete_transaction(trans_id)
    if deleted:
        send_realtime_update()
        return jsonify({'success': True, 'message': 'Transaction deleted'})
    return jsonify({'error': 'Transaction not found'}), 404

@app.route('/api/categories', methods=['GET'])
def get_categories():
    cat_id = request.args.get('id', type=int)
    if cat_id:
        category = db.get_categories(category_id=cat_id)
        return jsonify(category) if category else jsonify({'error': 'Not found'}), 404
    
    categories = db.get_categories()
    return jsonify(categories)

@app.route('/api/categories', methods=['POST'])
def create_category():
    data = request.json
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'Name and type required'}), 400
    
    cat_id = db.add_category(
        data['name'],
        data['type'],
        data.get('color', '#3b82f6'),
        data.get('icon', '📌')
    )
    return jsonify({'id': cat_id, 'success': True, 'message': 'Category created'}), 201

@app.route('/api/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.json
    updated = db.update_category(
        cat_id,
        name=data.get('name'),
        type_val=data.get('type'),
        color=data.get('color'),
        icon=data.get('icon')
    )
    if updated:
        return jsonify({'success': True, 'message': 'Category updated'})
    return jsonify({'error': 'Category not found'}), 404

@app.route('/api/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    deleted = db.delete_category(cat_id)
    if deleted:
        return jsonify({'success': True, 'message': 'Category deleted'})
    return jsonify({'error': 'Category not found'}), 404

@app.route('/api/monthly_report')
def monthly_report():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if not year or not month:
        now = datetime.now()
        year = now.year
        month = now.month
    
    summary = db.get_monthly_summary(year, month)
    breakdown = db.get_category_breakdown(year, month)
    
    return jsonify({
        'year': year,
        'month': month,
        'income': summary['income'],
        'expense': summary['expense'],
        'savings': summary['income'] - summary['expense'],
        'categories': breakdown
    })

@app.route('/api/predictions')
def get_predictions():
    predictions = ai.predict_spending()
    return jsonify(predictions)

@app.route('/api/recommendations')
def get_recommendations():
    now = datetime.now()
    recommendations = ai.get_budget_recommendations(now.year, now.month)
    return jsonify(recommendations)

@app.route('/api/savings_analysis')
def get_savings_analysis():
    analysis = ai.analyze_saving_patterns()
    return jsonify(analysis)

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'GET':
        currency = db.get_setting('currency', 'USD')
        return jsonify({'currency': currency})
    else:
        data = request.json
        if 'currency' in data:
            db.set_setting('currency', data['currency'])
        return jsonify({'success': True})

@app.route('/api/visualization/heatmap')
def get_heatmap():
    try:
        transactions = db.get_transactions()
        if not transactions:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['amount'] = df['amount'].astype(float)
        
        expense_df = df[df['type'] == 'expense'].copy()
        if expense_df.empty:
            return jsonify({'error': 'No expense data'}), 404
        
        heatmap_data = expense_df.pivot_table(
            values='amount', 
            index='day', 
            columns='month', 
            aggfunc='sum', 
            fill_value=0
        )
        
        fig, ax = plt.subplots(figsize=(12, 8))
        im = ax.imshow(heatmap_data.values, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(heatmap_data.columns)))
        ax.set_xticklabels(heatmap_data.columns)
        ax.set_yticks(range(len(heatmap_data.index)))
        ax.set_yticklabels(heatmap_data.index)
        plt.colorbar(im, ax=ax, label='Spending Amount ($)')
        ax.set_xlabel('Month')
        ax.set_ylabel('Day of Month')
        ax.set_title('Daily Spending Heatmap')
        
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
        buf.seek(0)
        plt.close()
        
        img_base64 = base64.b64encode(buf.getvalue()).decode()
        return jsonify({'image': f'data:image/png;base64,{img_base64}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv')
def export_csv():
    transactions = db.export_all_transactions()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Description', 'Amount', 'Type', 'Category', 'Created At'])
    
    for t in transactions:
        writer.writerow([
            t['id'], t['date'], t['description'], 
            t['amount'], t['type'], t.get('category_name', 'Uncategorized'),
            t['created_at']
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.route('/api/delete_all_transactions', methods=['DELETE'])
def delete_all_transactions():
    deleted = db.delete_all_transactions()
    send_realtime_update()
    return jsonify({'success': True, 'deleted_count': deleted})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🚀 PERSONAL FINANCE MANAGER - REAL-TIME EDITION")
    print("="*60)
    print(f"  📊 Dashboard:     http://127.0.0.1:5000/")
    print(f"  💰 Transactions:  http://127.0.0.1:5000/transactions")
    print(f"  🏷️  Categories:    http://127.0.0.1:5000/categories")
    print(f"  📈 Reports:       http://127.0.0.1:5000/reports")
    print(f"  🤖 AI Predictions: http://127.0.0.1:5000/predictions")
    print(f"  📊 Visuals:       http://127.0.0.1:5000/visualizations")
    print(f"  ⚙️  Settings:      http://127.0.0.1:5000/settings")
    print("="*60)
    print("  ✨ Real-time updates active - Charts update automatically!")
    print("="*60 + "\n")
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)