from flask_mail import Message
from flask import current_app
import html

def get_horizon_label(value):
    """Convert horizon value to human-readable label."""
    horizon_options = [
        { 'value': 0, 'label': 'Easy access' },
        { 'value': 1, 'label': '1 month' },
        { 'value': 3, 'label': '3 months' },
        { 'value': 6, 'label': '6 months' },
        { 'value': 12, 'label': '1 year' },
        { 'value': 24, 'label': '2 years' },
        { 'value': 36, 'label': '3 years' },
        { 'value': 60, 'label': '5 years' }
    ]
    option = next((opt for opt in horizon_options if opt['value'] == value), None)
    return option['label'] if option else 'N/A'

def format_email_html(inputs, summary, investments):
    """Generate HTML email content with formatted results."""
    
    # Format savings goals
    savings_goals_html = ''
    if inputs and inputs.get('savings_goals'):
        for goal in inputs['savings_goals']:
            horizon_label = get_horizon_label(goal.get('horizon', 0))
            amount = goal.get('amount', 0)
            savings_goals_html += f'''
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;">£{amount:,.0f}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e0e0e0;">{horizon_label}</td>
            </tr>
            '''
    
    # Format investments as separate cards
    investments_html = ''
    if investments:
        for inv in investments:
            account_type = 'ISA' if inv.get('is_isa') else 'Standard'
            account_name = html.escape(str(inv.get('account_name', 'N/A')))
            url = inv.get('url', '')
            amount = float(inv.get('amount', 0))
            aer = inv.get('aer', 'N/A')
            term = inv.get('term', 'N/A')
            platform = html.escape(str(inv.get('platform', 'N/A')))
            
            # Make the entire card clickable if URL is available
            if url and url.strip() and url != '#':
                escaped_url = html.escape(url)
                card_link_start = f'<a href="{escaped_url}" style="text-decoration: none; color: inherit; display: block;" target="_blank">'
                card_link_end = '</a>'
            else:
                card_link_start = ''
                card_link_end = ''
            
            investments_html += f'''
            <div class="investment-card" style="background-color: #f9f9f9; border: 2px solid #9B7EDE; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                {card_link_start}
                <div style="margin-bottom: 15px;">
                    <h3 style="color: #2D1B4E; margin: 0 0 8px 0; font-size: 20px; font-weight: bold;">
                        {account_name}
                    </h3>
                    <p style="color: #666; font-size: 14px; margin: 0;">{platform} • {account_type}</p>
                </div>
                <table style="width: 100%; margin-top: 15px; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 0 10px 0 0; vertical-align: top;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Amount to Invest</div>
                            <div style="font-size: 18px; font-weight: bold; color: #2D1B4E;">£{amount:,.0f}</div>
                        </td>
                        <td style="padding: 0 10px; vertical-align: top;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">AER</div>
                            <div style="font-size: 18px; font-weight: bold; color: #2D1B4E;">{aer}%</div>
                        </td>
                        <td style="padding: 0 0 0 10px; vertical-align: top;">
                            <div style="font-size: 12px; color: #666; margin-bottom: 5px;">Term</div>
                            <div style="font-size: 18px; font-weight: bold; color: #2D1B4E;">{term}</div>
                        </td>
                    </tr>
                </table>
                {card_link_end}
            </div>
            '''
    
    earnings = inputs.get('earnings', 0) if inputs else 0
    isa_allowance_used = inputs.get('isa_allowance_used', 0) if inputs else 0
    other_savings_income = inputs.get('other_savings_income', 0) if inputs else 0
    
    net_annual_interest = summary.get('net_annual_interest', 0) if summary else 0
    equivalent_pre_tax_rate = summary.get('equivalent_pre_tax_rate', 0) if summary else 0
    net_effective_aer = summary.get('net_effective_aer', 0) if summary else 0
    total_investment = summary.get('total_investment', 0) if summary else 0
    
    html_content = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #9B7EDE;
            }}
            .header h1 {{
                color: #2D1B4E;
                margin: 0;
                font-size: 28px;
            }}
            .highlight-box {{
                background: linear-gradient(135deg, rgba(155, 126, 222, 0.1) 0%, rgba(196, 181, 232, 0.1) 100%);
                border: 2px solid rgba(155, 126, 222, 0.2);
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                text-align: center;
            }}
            .highlight-box h2 {{
                color: #2D1B4E;
                margin-top: 0;
                font-size: 20px;
            }}
            .highlight-box .big-number {{
                font-size: 32px;
                font-weight: bold;
                color: #9B7EDE;
                margin: 10px 0;
            }}
            .highlight-box .big-rate {{
                font-size: 32px;
                font-weight: bold;
                color: #9B7EDE;
                margin: 10px 0;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section h3 {{
                color: #2D1B4E;
                border-bottom: 2px solid #9B7EDE;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            th {{
                background-color: #9B7EDE;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 10px;
            }}
            a {{
                color: #9B7EDE;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .investment-card {{
                transition: background-color 0.2s;
            }}
            .investment-card:hover {{
                background-color: #f0f0f0;
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }}
            .summary-item {{
                background-color: #f9f9f9;
                padding: 15px;
                border-radius: 6px;
                border-left: 4px solid #9B7EDE;
            }}
            .summary-item .label {{
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;
            }}
            .summary-item .value {{
                font-size: 20px;
                font-weight: bold;
                color: #2D1B4E;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Your Savings Optimization Results</h1>
            </div>
            
            <div class="section">
                <h3 style="color: #2D1B4E; border-bottom: 2px solid #9B7EDE; padding-bottom: 10px; margin-bottom: 20px; font-size: 24px;">Recommended Investments</h3>
                {investments_html if investments_html else '<p style="color: #666;">No investments recommended.</p>'}
            </div>
            
            <div class="highlight-box">
                <h2>Your Savings Could Earn You</h2>
                <div class="big-number">£{net_annual_interest:,.0f}</div>
                <p style="color: #6B5B8A; margin: 10px 0;">after tax per year</p>
                <p style="color: #6B5B8A; margin: 15px 0 5px 0;">equivalent to</p>
                <div class="big-rate">{equivalent_pre_tax_rate:.2f}%</div>
                <p style="color: #6B5B8A; margin: 5px 0;">pre-tax rate</p>
            </div>
            
            <div class="section">
                <h3>Your Inputs</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="label">Annual Earnings</div>
                        <div class="value">£{earnings:,.0f}</div>
                    </div>
                    <div class="summary-item">
                        <div class="label">ISA Allowance Used</div>
                        <div class="value">£{isa_allowance_used:,.0f}</div>
                    </div>
                    {f'<div class="summary-item"><div class="label">Other Savings Income</div><div class="value">£{other_savings_income:,.0f}</div></div>' if other_savings_income > 0 else ''}
                </div>
                
                <h4 style="color: #2D1B4E; margin-top: 20px;">Savings Goals</h4>
                <table>
                    <thead>
                        <tr>
                            <th style="padding: 8px;">Amount</th>
                            <th style="padding: 8px;">Time Horizon</th>
                        </tr>
                    </thead>
                    <tbody>
                        {savings_goals_html}
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h3>Optimization Results</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="label">Total Savings</div>
                        <div class="value">£{total_investment:,.0f}</div>
                    </div>
                    <div class="summary-item">
                        <div class="label">Net Annual Interest</div>
                        <div class="value">£{net_annual_interest:,.0f}</div>
                    </div>
                    <div class="summary-item">
                        <div class="label">Effective Net AER</div>
                        <div class="value">{net_effective_aer:.2f}%</div>
                    </div>
                    <div class="summary-item">
                        <div class="label">Equivalent Pre-Tax Rate</div>
                        <div class="value">{equivalent_pre_tax_rate:.2f}%</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>Thank you for using Quantify Lite!</p>
                <p style="font-size: 12px; color: #999;">This email was generated automatically. Please review all investment options carefully before making any decisions.</p>
            </div>
        </div>
    </body>
    </html>
    '''
    return html_content

def send_results_email(recipient_email, inputs, summary, investments):
    """Send formatted results email to the user using Resend API (Railway's recommended approach)."""
    try:
        from flask import current_app
        import resend
        
        # Check for Resend API key (preferred method - works on all Railway plans)
        resend_api_key = current_app.config.get('RESEND_API_KEY')
        resend_from_email = current_app.config.get('RESEND_FROM_EMAIL')
        
        if resend_api_key:
            # Use Resend API (works with Railway's network restrictions, recommended by Railway)
            print(f"Using Resend API to send email to {recipient_email}")
            
            # Generate HTML content
            html_content = format_email_html(inputs, summary, investments)
            
            # Configure Resend
            resend.api_key = resend_api_key
            
            # Send email via Resend API
            params = {
                "from": resend_from_email,
                "to": [recipient_email],
                "subject": "Your Savings Optimization Results - Quantify Lite",
                "html": html_content
            }
            
            email = resend.Emails.send(params)
            
            print(f"Resend API response: {email}")
            if email and 'id' in email:
                print(f"Email sent successfully to {recipient_email} via Resend (ID: {email['id']})")
                return True, None
            else:
                error_msg = f"Resend API returned unexpected response: {email}"
                print(f"ERROR: {error_msg}")
                return False, error_msg
        
        # Fallback to SMTP (for local development only - won't work on Railway free plans)
        print("Resend not configured, attempting SMTP fallback...")
        from flask_mail import Message
        
        mail_server = current_app.config.get('MAIL_SERVER')
        mail_username = current_app.config.get('MAIL_USERNAME')
        mail_password = current_app.config.get('MAIL_PASSWORD')
        
        if not mail_server or not mail_username or not mail_password:
            error_msg = "Neither Resend API key nor SMTP credentials are configured"
            print(f"ERROR: {error_msg}")
            return False, error_msg
        
        # Generate HTML content
        html_content = format_email_html(inputs, summary, investments)
        
        # Create message
        msg = Message(
            subject='Your Savings Optimization Results - Quantify Lite',
            recipients=[recipient_email],
            html=html_content
        )
        
        # Get mail instance from current app extensions
        mail = current_app.extensions.get('mail')
        if not mail:
            error_msg = "Mail extension not found in app context"
            print(error_msg)
            return False, error_msg
        
        print(f"Attempting to send email via SMTP to {recipient_email}")
        mail.send(msg)
        print(f"Email sent successfully to {recipient_email} via SMTP")
        return True, None
        
    except Exception as e:
        error_msg = str(e)
        print(f"Error sending email to {recipient_email}: {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg

