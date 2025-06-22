from flask import Blueprint, request, jsonify
from app.services.account_data_service import get_accounts
from app.services.optimization_service import optimize_savings
from app.models import OptimizationInput, SavingsGoal
from dataclasses import asdict

bp = Blueprint('main', __name__)

@bp.route('/optimize', methods=['POST'])
def optimize():
    """
    Endpoint to trigger the savings optimization.
    Expects a JSON payload with 'earnings' and 'savings_goals'.
    e.g. {"earnings": 50000, "savings_goals": [{"amount": 10000, "horizon": "1 year"}]}
    """
    data = request.get_json()
    if not data or 'savings_goals' not in data or not isinstance(data['savings_goals'], list):
        return jsonify({"error": "Missing or invalid 'savings_goals' in request body"}), 400

    try:
        if not data['savings_goals']:
            return jsonify({"error": "'savings_goals' cannot be empty"}), 400

        savings_goals = [
            SavingsGoal(amount=float(goal['amount']), horizon=goal['horizon'])
            for goal in data['savings_goals']
        ]

        total_investment = sum(goal.amount for goal in savings_goals)
        if total_investment <= 0:
            return jsonify({"error": "'total_investment' derived from goals must be positive"}), 400

        earnings = data.get('earnings')
        if earnings is not None:
            earnings = float(earnings)

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid data in 'savings_goals' or 'earnings'"}), 400

    # 1. Get account data
    accounts = get_accounts()
    if not accounts:
        return jsonify({"error": "Could not retrieve account data"}), 500

    # 2. Create optimization input
    opt_input = OptimizationInput(
        total_investment=total_investment,
        savings_goals=savings_goals,
        earnings=earnings
    )

    # 3. Run optimization
    result = optimize_savings(opt_input, accounts)

    # 4. Return result
    return jsonify(asdict(result))

@bp.route('/health', methods=['GET'])
def health_check():
    """
    A simple health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200 