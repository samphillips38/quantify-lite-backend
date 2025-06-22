from flask import Blueprint, request, jsonify
from app.services.account_data_service import get_accounts
from app.services.optimization_service import optimize_savings
from app.models import OptimizationInput
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
        # For now, we sum the amounts from all goals to get a single total_investment.
        # This is a simplification until the backend logic is updated to handle multiple horizons.
        total_investment = sum(float(goal.get('amount', 0)) for goal in data['savings_goals'])
        if total_investment <= 0:
            return jsonify({"error": "'total_investment' derived from goals must be positive"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid 'amount' in savings_goals"}), 400

    # 1. Get account data
    accounts = get_accounts()
    if not accounts:
        return jsonify({"error": "Could not retrieve account data"}), 500

    # 2. Create optimization input
    opt_input = OptimizationInput(total_investment=total_investment)

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