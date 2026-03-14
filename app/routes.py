from flask import Blueprint, request, jsonify
from app.services.account_data_service import get_accounts
from app.services.optimization_service import optimize_savings
from app.services.email_service import send_results_email
from app.models import OptimizationInput, SavingsGoal
from app.database_models import db, OptimizationRecord, Feedback, EmailRequest
from dataclasses import asdict
import json
import threading
import os

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

        other_savings_income = data.get('other_savings_income')
        if other_savings_income is not None:
            other_savings_income = float(other_savings_income)
        else:
            other_savings_income = 0.0

        excluded_providers = data.get('excluded_providers')
        if excluded_providers is not None:
            if not isinstance(excluded_providers, list):
                return jsonify({"error": "'excluded_providers' must be a list of strings"}), 400
            excluded_providers = [str(p) for p in excluded_providers]
        else:
            excluded_providers = []

    except (ValueError, TypeError, KeyError):
        return jsonify({"error": "Invalid data in 'savings_goals' or 'earnings' or 'isa_allowance_used' or 'other_savings_income'"}), 400

    # 1. Get account data
    accounts = get_accounts()
    if not accounts:
        return jsonify({"error": "Could not retrieve account data"}), 500

    # 2. Create optimization input
    opt_input = OptimizationInput(
        total_investment=total_investment,
        savings_goals=savings_goals,
        earnings=earnings,
        isa_allowance_used=isa_allowance_used,
        other_savings_income=other_savings_income,
        excluded_providers=excluded_providers
    )

    # 3. Run optimization
    result = optimize_savings(opt_input, accounts)

    # 4. Save optimization record to database
    try:
        # Extract session_id and batch_id from request (optional, for tracking)
        session_id = data.get('session_id')
        batch_id = data.get('batch_id')
        
        record = OptimizationRecord(
            total_investment=opt_input.total_investment,
            earnings=opt_input.earnings,
            isa_allowance_used=opt_input.isa_allowance_used,
            other_savings_income=opt_input.other_savings_income,
            savings_goals_json=json.dumps([asdict(goal) for goal in opt_input.savings_goals]),
            status=result.status,
            total_gross_interest=result.summary.gross_annual_interest if result.summary else None,
            total_net_interest=result.summary.net_annual_interest if result.summary else None,
            net_effective_aer=result.summary.net_effective_aer if result.summary else None,
            tax_due=result.summary.tax_due if result.summary else None,
            tax_band=result.summary.tax_band if result.summary else None,
            personal_savings_allowance=result.summary.personal_savings_allowance if result.summary else None,
            tax_rate=result.summary.tax_rate if result.summary else None,
            tax_free_allowance_remaining=result.summary.tax_free_allowance_remaining if result.summary else None,
            equivalent_pre_tax_rate=result.summary.equivalent_pre_tax_rate if result.summary else None,
            investments_json=json.dumps([asdict(inv) for inv in result.investments]) if result.investments else None,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr,
            session_id=session_id,
            batch_id=batch_id
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
        print("Feedback endpoint: Missing data in request body")
        return jsonify({"error": "Missing data in request body"}), 400

    print(f"Feedback endpoint received data: {data}")

    required_fields = ['optimization_record_id', 'nps_score', 'useful']
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        print(f"Feedback endpoint: Missing required fields: {missing_fields}")
        return jsonify({"error": f"Missing required fields: {missing_fields}"}), 400

    try:
        # Validate and convert optimization_record_id
        try:
            optimization_record_id = int(data['optimization_record_id'])
        except (ValueError, TypeError):
            print(f"Feedback endpoint: Invalid optimization_record_id: {data.get('optimization_record_id')}")
            return jsonify({"error": f"Invalid optimization_record_id: {data.get('optimization_record_id')}"}), 400
        
        # Validate and convert nps_score
        try:
            nps_score = int(data['nps_score'])
        except (ValueError, TypeError):
            print(f"Feedback endpoint: Invalid nps_score: {data.get('nps_score')}")
            return jsonify({"error": f"Invalid nps_score: {data.get('nps_score')}"}), 400
        
        # Validate useful field
        useful_value = str(data['useful']) if data['useful'] is not None else None
        if not useful_value:
            print(f"Feedback endpoint: Invalid useful value: {data.get('useful')}")
            return jsonify({"error": f"Invalid useful value: {data.get('useful')}"}), 400
        
        # Handle optional age field - convert to int only if provided and not empty
        age_value = None
        if 'age' in data and data['age'] is not None and data['age'] != '':
            try:
                age_value = int(data['age'])
            except (ValueError, TypeError):
                print(f"Feedback endpoint: Invalid age value: {data.get('age')}")
                return jsonify({"error": f"Invalid age value: {data.get('age')}"}), 400
        
        # Handle improvements - convert empty string to None
        improvements_value = data.get('improvements')
        if improvements_value == '':
            improvements_value = None
        
        # Handle optional session_id and batch_id
        session_id = data.get('session_id')
        batch_id = data.get('batch_id')
        
        # If batch_id not provided, try to get it from the optimization record
        if not batch_id and optimization_record_id:
            try:
                opt_record = OptimizationRecord.query.get(optimization_record_id)
                if opt_record and opt_record.batch_id:
                    batch_id = opt_record.batch_id
            except Exception as e:
                print(f"Could not retrieve batch_id from optimization record: {e}")
        
        feedback_entry = Feedback(
            optimization_record_id=optimization_record_id,
            session_id=session_id,
            batch_id=batch_id,
            nps_score=nps_score,
            useful=useful_value,
            improvements=improvements_value,
            age=age_value
        )
        db.session.add(feedback_entry)
        db.session.commit()
        print("Feedback endpoint: Successfully saved feedback")
    except (ValueError, TypeError, KeyError) as e:
        db.session.rollback()
        print(f"Feedback endpoint: Invalid data provided - {type(e).__name__}: {e}")
        return jsonify({"error": f"Invalid data provided: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error saving feedback to database: {e}")
        return jsonify({"error": "Failed to save feedback"}), 500

    return jsonify({"message": "Feedback submitted successfully"}), 201

@bp.route('/email-results', methods=['POST'])
def email_results():
    """
    Endpoint to email optimization results to the user.
    Expects a JSON payload with 'email', 'inputs', 'summary', and 'investments'.
    Also accepts optional 'session_id', 'optimization_record_id', and 'batch_id'.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing data in request body"}), 400
    
    # Validate required fields
    email = data.get('email')
    if not email:
        return jsonify({"error": "Missing 'email' field"}), 400
    
    # Basic email validation
    if '@' not in email or '.' not in email.split('@')[1]:
        return jsonify({"error": "Invalid email address"}), 400
    
    inputs = data.get('inputs')
    summary = data.get('summary')
    investments = data.get('investments', [])
    
    if not inputs or not summary:
        return jsonify({"error": "Missing 'inputs' or 'summary' in request body"}), 400
    
    # Extract optional tracking fields
    session_id = data.get('session_id')
    optimization_record_id = data.get('optimization_record_id')
    batch_id = data.get('batch_id')
    
    # If batch_id not provided, try to get it from the optimization record
    if not batch_id and optimization_record_id:
        try:
            opt_record = OptimizationRecord.query.get(int(optimization_record_id))
            if opt_record and opt_record.batch_id:
                batch_id = opt_record.batch_id
        except Exception as e:
            print(f"Could not retrieve batch_id from optimization record: {e}")
    
    # Create email request record in database
    email_request = None
    try:
        email_request = EmailRequest(
            email=email,
            optimization_record_id=int(optimization_record_id) if optimization_record_id else None,
            session_id=session_id,
            batch_id=batch_id,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr,
            email_sent=False
        )
        db.session.add(email_request)
        db.session.commit()
        email_request_id = email_request.id
    except Exception as e:
        db.session.rollback()
        print(f"Error saving email request to database: {e}")
        return jsonify({"error": "Failed to save email request"}), 500
    
    # Send the email asynchronously to prevent worker timeout
    def send_email_async(email_request_id, recipient_email, inputs, summary, investments):
        """Send email in background thread and update database record."""
        import sys
        import os
        from app import create_app
        
        try:
            print(f"[EMAIL THREAD] Starting async email send for request {email_request_id} to {recipient_email}")
            print(f"[EMAIL THREAD] Thread: {threading.current_thread().name}, PID: {os.getpid()}")
            sys.stdout.flush()  # Force flush to ensure logs appear
            
            # Create a new app context for the background thread
            print(f"[EMAIL THREAD] Creating app context...")
            app = create_app()
            print(f"[EMAIL THREAD] App created, entering context...")
            with app.app_context():
                try:
                    print(f"[EMAIL THREAD] App context active, fetching email request {email_request_id}")
                    sys.stdout.flush()
                    
                    # Get the email request record
                    email_request = EmailRequest.query.get(email_request_id)
                    if not email_request:
                        print(f"[EMAIL THREAD] ERROR: Email request {email_request_id} not found")
                        return
                    
                    print(f"[EMAIL THREAD] Email request found, calling send_results_email...")
                    sys.stdout.flush()
                    
                    # Send the email
                    success, error = send_results_email(recipient_email, inputs, summary, investments)
                    
                    print(f"[EMAIL THREAD] send_results_email returned: success={success}, error={error if error else 'None'}")
                    sys.stdout.flush()
                    
                    # Update email request record with sending status
                    try:
                        email_request.email_sent = success
                        if not success:
                            email_request.email_error = error[:500] if error else "Unknown error"
                            print(f"[EMAIL THREAD] Email sending failed for request {email_request_id}: {error}")
                        else:
                            print(f"[EMAIL THREAD] Email sent successfully for request {email_request_id}")
                        db.session.commit()
                        print(f"[EMAIL THREAD] Email request {email_request_id} updated in database: sent={success}")
                        sys.stdout.flush()
                    except Exception as e:
                        db.session.rollback()
                        print(f"[EMAIL THREAD] ERROR updating email request status: {e}")
                        import traceback
                        traceback.print_exc()
                        sys.stdout.flush()
                except Exception as e:
                    # Update email request record with error
                    print(f"[EMAIL THREAD] EXCEPTION in async email sending: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    sys.stdout.flush()
                    try:
                        email_request = EmailRequest.query.get(email_request_id)
                        if email_request:
                            email_request.email_sent = False
                            email_request.email_error = str(e)[:500]
                            db.session.commit()
                            print(f"[EMAIL THREAD] Updated email request {email_request_id} with error status")
                            sys.stdout.flush()
                    except Exception as db_error:
                        db.session.rollback()
                        print(f"[EMAIL THREAD] ERROR updating email request error status: {db_error}")
                        import traceback
                        traceback.print_exc()
                        sys.stdout.flush()
        except Exception as outer_error:
            print(f"[EMAIL THREAD] FATAL ERROR in thread setup: {type(outer_error).__name__}: {outer_error}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
            # Try to update database even if app context failed
            try:
                app = create_app()
                with app.app_context():
                    email_request = EmailRequest.query.get(email_request_id)
                    if email_request:
                        email_request.email_sent = False
                        email_request.email_error = f"Thread setup failed: {str(outer_error)[:500]}"
                        db.session.commit()
            except:
                pass
    
    # Start email sending in background thread
    # Note: daemon=False so thread completes even if main thread exits
    thread = threading.Thread(
        target=send_email_async,
        args=(email_request_id, email, inputs, summary, investments),
        name=f"EmailSender-{email_request_id}"
    )
    thread.daemon = False  # Changed to False so thread completes
    thread.start()
    print(f"Started email thread: {thread.name} (ID: {thread.ident})")
    
    # Return immediately - email will be sent in background
    return jsonify({"message": "Email request received and will be sent shortly"}), 202 