import json
from app.database_models import db, OptimizationRecord

def test_health_check(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/health' endpoint is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_optimize_endpoint(test_client, test_app):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/optimize' endpoint is posted to with valid data
    THEN check that the response is valid and a record is created in the database
    """
    mock_request_data = {
        "earnings": 50000,
        "isa_allowance_used": 1000,
        "savings_goals": [
            {"amount": 10000, "horizon": 12},
            {"amount": 5000, "horizon": 24}
        ]
    }

    response = test_client.post('/optimize', data=json.dumps(mock_request_data), content_type='application/json')
    
    # Check for a successful response
    assert response.status_code == 200
    response_data = response.json
    assert response_data['status'] == "Optimal"
    assert len(response_data['investments']) > 0

    # Check that a record was created in the database
    with test_app.app_context():
        # There should be exactly one record after this test
        records = OptimizationRecord.query.all()
        assert len(records) == 1
        
        record = records[0]
        assert record.total_investment == 15000
        assert record.earnings == 50000
        assert record.status == "Optimal"
        assert record.tax_band == "Basic Rate"
        
        # Clean up the record for other tests if needed, although the db is dropped anyway
        db.session.delete(record)
        db.session.commit() 