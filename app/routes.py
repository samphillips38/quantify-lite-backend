from flask import Blueprint, request, jsonify
from app.services.account_data_service import get_accounts
from app.services.optimization_service import optimize_savings
from app.models import OptimizationInput, SavingsGoal
from app.database_models import db, OptimizationRecord, Feedback
from dataclasses import asdict
import json

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
            SavingsGoal(amount=float(goal['amount']), horizon=int(goal['horizon']))
            for goal in data['savings_goals']
        ]

        total_investment = sum(goal.amount for goal in savings_goals)
        if total_investment <= 0:
            return jsonify({"error": "'total_investment' derived from goals must be positive"}), 400

        earnings = data.get('earnings')
        if earnings is not None:
            earnings = float(earnings)

        isa_allowance_used = data.get('isa_allowance_used')
        if isa_allowance_used is not None:
            isa_allowance_used = float(isa_allowance_used)
        else:
            isa_allowance_used = 0.0

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid data in 'savings_goals' or 'earnings' or 'isa_allowance_used'"}), 400

    # 1. Get account data
    accounts = get_accounts()
    if not accounts:
        return jsonify({"error": "Could not retrieve account data"}), 500

    # 2. Create optimization input
    opt_input = OptimizationInput(
        total_investment=total_investment,
        savings_goals=savings_goals,
        earnings=earnings,
        isa_allowance_used=isa_allowance_used
    )

    # 3. Run optimization
    result = optimize_savings(opt_input, accounts)

    # 4. Save optimization record to database
    try:
        record = OptimizationRecord(
            total_investment=opt_input.total_investment,
            earnings=opt_input.earnings,
            isa_allowance_used=opt_input.isa_allowance_used,
            savings_goals_json=json.dumps([asdict(goal) for goal in opt_input.savings_goals]),
            status=result.status,
            total_gross_interest=result.summary.gross_annual_interest if result.summary else None,
            total_net_interest=result.summary.net_annual_interest if result.summary else None,
            net_effective_aer=result.summary.net_effective_aer if result.summary else None,
            tax_due=result.summary.tax_due if result.summary else None,
            tax_band=result.summary.tax_band if result.summary else None,
            personal_savings_allowance=result.summary.personal_savings_allowance if result.summary else None,
            tax_rate=result.summary.tax_rate if result.summary else None,
            tax_free_allowance=result.summary.tax_free_allowance if result.summary else None,
            investments_json=json.dumps([asdict(inv) for inv in result.investments]) if result.investments else None,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        db.session.add(record)
        db.session.commit()

        # Add the record ID to the result
        result.optimization_record_id = record.id

    except Exception as e:
        db.session.rollback()
        print(f"Error saving optimization record to database: {e}")
        # We don't want to fail the main request if logging fails, so we just print the error.

    # 5. Return result
    return jsonify(asdict(result))

@bp.route('/health', methods=['GET'])
def health_check():
    """
    A simple health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@bp.route('/analytics', methods=['GET'])
def get_analytics():
    """
    A simple analytics endpoint to view aggregated optimization data.
    """
    try:
        total_optimizations = OptimizationRecord.query.count()
        successful_optimizations = OptimizationRecord.query.filter_by(status="Optimal").count()
        
        # Using func for aggregations
        avg_investment = db.session.query(db.func.avg(OptimizationRecord.total_investment)).scalar()
        
        analytics_data = {
            'total_optimizations': total_optimizations,
            'successful_optimizations': successful_optimizations,
            'average_investment_amount': round(avg_investment, 2) if avg_investment else 0,
        }
        return jsonify(analytics_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/feedback', methods=['POST'])
def feedback():
    """
    Endpoint to submit feedback.
    Expects a JSON payload with 'optimization_record_id', 'nps_score', 'useful', and 'improvements'.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing data in request body"}), 400

    required_fields = ['optimization_record_id', 'nps_score', 'useful']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    try:
        feedback_entry = Feedback(
            optimization_record_id=int(data['optimization_record_id']),
            nps_score=int(data['nps_score']),
            useful=str(data['useful']),
            improvements=data.get('improvements'),
            age=int(data['age'])
        )
        db.session.add(feedback_entry)
        db.session.commit()
    except (ValueError, TypeError, KeyError) as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data provided: {e}"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error saving feedback to database: {e}")
        return jsonify({"error": "Failed to save feedback"}), 500

    return jsonify({"message": "Feedback submitted successfully"}), 201 