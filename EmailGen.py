from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import mailslurp_client
from mailslurp_client.rest import ApiException
import re
import os
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Professional HTML  with complete functionality
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Gen - Professional Email Testing</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .loading { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .fade-in { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        .slide-in { animation: slideIn 0.3s ease-out; }
        @keyframes slideIn { from { transform: translateY(-10px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    </style>
</head>
<body class="bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="bg-blue-600 p-2 rounded-lg">
                        <i class="fas fa-envelope text-white text-xl"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900">Email pro</h1>
                        <p class="text-sm text-gray-500">Professional Email generator By <b>Israel Dev</b></p>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="text-sm text-gray-500">Status:</span>
                    <span id="status" class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                        Ready
                    </span>
                </div>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Configuration Panel -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-xl shadow-sm border p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-cog text-blue-600 mr-2"></i>
                        Configuration
                    </h2>
                    
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                MailSlurp API Key
                            </label>
                            <input type="password" id="apiKey" 
                                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   placeholder="Enter your API key">
                            <p class="text-xs text-gray-500 mt-1">
                                Get your API key from <a href="https://app.mailslurp.com" target="_blank" class="text-blue-600 hover:underline">MailSlurp Dashboard</a>
                            </p>
                        </div>

                        <button id="createInboxBtn" 
                                class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center justify-center">
                            <i class="fas fa-plus mr-2"></i>
                            Create New Inbox
                        </button>

                        <div id="inboxInfo" class="hidden p-4 bg-green-50 border border-green-200 rounded-lg">
                            <h3 class="font-medium text-green-800 mb-2">Inbox Created</h3>
                            <div class="text-sm space-y-1">
                                <div class="flex items-center justify-between">
                                    <span class="text-green-700">Email:</span>
                                    <button id="copyEmail" class="text-blue-600 hover:text-blue-800 text-xs">
                                        <i class="fas fa-copy mr-1"></i>Copy
                                    </button>
                                </div>
                                <div id="emailAddress" class="font-mono text-xs bg-white p-2 rounded border break-all"></div>
                                <div class="text-green-700">ID: <span id="inboxId" class="font-mono text-xs"></span></div>
                                <div class="text-green-700">Created: <span id="createdAt" class="text-xs"></span></div>
                            </div>
                        </div>

                        <button id="waitEmailBtn" 
                                class="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                            <i class="fas fa-clock mr-2"></i>
                            Wait for Email
                        </button>

                        <div id="waitingIndicator" class="hidden p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                            <div class="flex items-center">
                                <i class="fas fa-spinner loading text-yellow-600 mr-2"></i>
                                <span class="text-yellow-800 text-sm">Waiting for email (60s timeout)...</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Statistics Panel -->
                <div class="bg-white rounded-xl shadow-sm border p-6 mt-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-chart-bar text-green-600 mr-2"></i>
                        Statistics
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600" id="inboxCount">0</div>
                            <div class="text-xs text-gray-500">Inboxes Created</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600" id="emailCount">0</div>
                            <div class="text-xs text-gray-500">Emails Received</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content Area -->
            <div class="lg:col-span-2">
                <div class="bg-white rounded-xl shadow-sm border">
                    <!-- Email Display Header -->
                    <div class="px-6 py-4 border-b bg-gray-50 rounded-t-xl">
                        <h2 class="text-lg font-semibold text-gray-900 flex items-center">
                            <i class="fas fa-inbox text-blue-600 mr-2"></i>
                            Email Content
                        </h2>
                    </div>

                    <!-- Email Content -->
                    <div id="emailContent" class="p-6">
                        <div class="text-center py-12">
                            <i class="fas fa-envelope-open text-gray-300 text-4xl mb-4"></i>
                            <p class="text-gray-500">Create an inbox and wait for emails to display content here</p>
                        </div>
                    </div>

                    <!-- Email Details -->
                    <div id="emailDetails" class="hidden border-t bg-gray-50 px-6 py-4">
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                            <div>
                                <span class="font-medium text-gray-700">From:</span>
                                <span id="emailFrom" class="ml-2 text-gray-600"></span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Subject:</span>
                                <span id="emailSubject" class="ml-2 text-gray-600"></span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Received:</span>
                                <span id="emailReceived" class="ml-2 text-gray-600"></span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Email ID:</span>
                                <span id="emailId" class="ml-2 text-gray-600 font-mono text-xs"></span>
                            </div>
                        </div>
                        
                        <!-- OTP Extraction -->
                        <div class="mt-4 pt-4 border-t">
                            <button id="extractOtpBtn" 
                                    class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium">
                                <i class="fas fa-key mr-2"></i>Extract OTP
                            </button>
                            <span id="otpResult" class="ml-4 text-sm"></span>
                        </div>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="mt-6 flex space-x-4">
                    <button id="clearBtn" 
                            class="flex-1 bg-gray-600 text-white py-2 px-4 rounded-lg hover:bg-gray-700 transition-colors font-medium">
                        <i class="fas fa-trash mr-2"></i>Clear All
                    </button>
                    <button id="exportBtn" 
                            class="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors font-medium">
                        <i class="fas fa-download mr-2"></i>Export Data
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Notifications -->
    <div id="toast" class="fixed top-4 right-4 z-50 hidden">
        <div class="bg-white border rounded-lg shadow-lg p-4 max-w-sm">
            <div class="flex items-center">
                <i id="toastIcon" class="text-lg mr-3"></i>
                <span id="toastMessage" class="text-sm font-medium"></span>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let currentInboxId = null;
        let currentApiKey = null;
        let stats = { inboxes: 0, emails: 0 };
        let currentEmailData = null;

        // DOM elements
        const elements = {
            apiKey: document.getElementById('apiKey'),
            createInboxBtn: document.getElementById('createInboxBtn'),
            waitEmailBtn: document.getElementById('waitEmailBtn'),
            inboxInfo: document.getElementById('inboxInfo'),
            emailAddress: document.getElementById('emailAddress'),
            inboxId: document.getElementById('inboxId'),
            createdAt: document.getElementById('createdAt'),
            waitingIndicator: document.getElementById('waitingIndicator'),
            emailContent: document.getElementById('emailContent'),
            emailDetails: document.getElementById('emailDetails'),
            status: document.getElementById('status'),
            copyEmail: document.getElementById('copyEmail'),
            extractOtpBtn: document.getElementById('extractOtpBtn'),
            otpResult: document.getElementById('otpResult'),
            clearBtn: document.getElementById('clearBtn'),
            exportBtn: document.getElementById('exportBtn'),
            inboxCount: document.getElementById('inboxCount'),
            emailCount: document.getElementById('emailCount')
        };

        // Utility functions
        function showToast(message, type = 'info') {
            const toast = document.getElementById('toast');
            const icon = document.getElementById('toastIcon');
            const messageEl = document.getElementById('toastMessage');
            
            const icons = {
                success: 'fas fa-check-circle text-green-500',
                error: 'fas fa-exclamation-circle text-red-500',
                info: 'fas fa-info-circle text-blue-500',
                warning: 'fas fa-exclamation-triangle text-yellow-500'
            };
            
            icon.className = icons[type];
            messageEl.textContent = message;
            toast.classList.remove('hidden');
            toast.classList.add('fade-in');
            
            setTimeout(() => {
                toast.classList.add('hidden');
                toast.classList.remove('fade-in');
            }, 3000);
        }

        function updateStatus(status, type = 'info') {
            const statusEl = elements.status;
            const colors = {
                success: 'bg-green-100 text-green-600',
                error: 'bg-red-100 text-red-600',
                info: 'bg-blue-100 text-blue-600',
                warning: 'bg-yellow-100 text-yellow-600'
            };
            
            statusEl.className = `px-2 py-1 text-xs font-medium rounded-full ${colors[type]}`;
            statusEl.textContent = status;
        }

        function updateStats() {
            elements.inboxCount.textContent = stats.inboxes;
            elements.emailCount.textContent = stats.emails;
        }

        function formatDate(dateString) {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString();
        }

        // API functions
        async function createInbox(apiKey) {
            const response = await fetch('/api/create_inbox', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ apiKey })
            });
            return response.json();
        }

        async function waitEmail(apiKey, inboxId) {
            const response = await fetch('/api/wait_email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ apiKey, inboxId })
            });
            return response.json();
        }

        async function extractOtp(content) {
            const response = await fetch('/api/extract_otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content })
            });
            return response.json();
        }

        // Event handlers
        elements.createInboxBtn.addEventListener('click', async () => {
            const apiKey = elements.apiKey.value.trim();
            if (!apiKey) {
                showToast('Please enter your MailSlurp API key', 'error');
                return;
            }

            currentApiKey = apiKey;
            elements.createInboxBtn.disabled = true;
            elements.createInboxBtn.innerHTML = '<i class="fas fa-spinner loading mr-2"></i>Creating...';
            updateStatus('Creating inbox...', 'info');

            try {
                const result = await createInbox(apiKey);
                
                if (result.error) {
                    throw new Error(result.error);
                }

                currentInboxId = result.id;
                elements.emailAddress.textContent = result.emailAddress;
                elements.inboxId.textContent = result.id;
                elements.createdAt.textContent = formatDate(result.createdAt);
                
                elements.inboxInfo.classList.remove('hidden');
                elements.inboxInfo.classList.add('slide-in');
                elements.waitEmailBtn.disabled = false;
                
                stats.inboxes++;
                updateStats();
                updateStatus('Inbox created successfully', 'success');
                showToast('Inbox created successfully!', 'success');
                
            } catch (error) {
                showToast(`Error: ${error.message}`, 'error');
                updateStatus('Error creating inbox', 'error');
            } finally {
                elements.createInboxBtn.disabled = false;
                elements.createInboxBtn.innerHTML = '<i class="fas fa-plus mr-2"></i>Create New Inbox';
            }
        });

        elements.waitEmailBtn.addEventListener('click', async () => {
            if (!currentApiKey || !currentInboxId) {
                showToast('Please create an inbox first', 'error');
                return;
            }

            elements.waitEmailBtn.disabled = true;
            elements.waitingIndicator.classList.remove('hidden');
            updateStatus('Waiting for email...', 'warning');

            try {
                const result = await waitEmail(currentApiKey, currentInboxId);
                
                if (result.error) {
                    throw new Error(result.error);
                }

                currentEmailData = result;
                displayEmail(result);
                
                stats.emails++;
                updateStats();
                updateStatus('Email received', 'success');
                showToast('Email received successfully!', 'success');
                
            } catch (error) {
                showToast(`Error: ${error.message}`, 'error');
                updateStatus('Error waiting for email', 'error');
            } finally {
                elements.waitEmailBtn.disabled = false;
                elements.waitingIndicator.classList.add('hidden');
            }
        });

        elements.copyEmail.addEventListener('click', async () => {
            const email = elements.emailAddress.textContent;
            try {
                await navigator.clipboard.writeText(email);
                showToast('Email address copied to clipboard!', 'success');
            } catch (error) {
                showToast('Failed to copy email address', 'error');
            }
        });

        elements.extractOtpBtn.addEventListener('click', async () => {
            if (!currentEmailData) {
                showToast('No email data available', 'error');
                return;
            }

            try {
                const content = currentEmailData.body || currentEmailData.htmlBody || '';
                const result = await extractOtp(content);
                
                if (result.otp) {
                    elements.otpResult.innerHTML = `<span class="font-mono bg-yellow-100 px-2 py-1 rounded text-yellow-800">${result.otp}</span>`;
                    showToast(`OTP extracted: ${result.otp}`, 'success');
                } else {
                    elements.otpResult.innerHTML = '<span class="text-gray-500">No OTP found</span>';
                    showToast('No OTP found in email', 'warning');
                }
            } catch (error) {
                showToast(`Error extracting OTP: ${error.message}`, 'error');
            }
        });

        elements.clearBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all data?')) {
                currentInboxId = null;
                currentApiKey = null;
                currentEmailData = null;
                
                elements.inboxInfo.classList.add('hidden');
                elements.emailDetails.classList.add('hidden');
                elements.waitEmailBtn.disabled = true;
                elements.apiKey.value = '';
                elements.otpResult.innerHTML = '';
                
                elements.emailContent.innerHTML = `
                    <div class="text-center py-12">
                        <i class="fas fa-envelope-open text-gray-300 text-4xl mb-4"></i>
                        <p class="text-gray-500">Create an inbox and wait for emails to display content here</p>
                    </div>
                `;
                
                updateStatus('Ready', 'info');
                showToast('All data cleared', 'info');
            }
        });

        elements.exportBtn.addEventListener('click', () => {
            if (!currentEmailData) {
                showToast('No email data to export', 'error');
                return;
            }

            const exportData = {
                inbox: {
                    id: currentInboxId,
                    email: elements.emailAddress.textContent,
                    created: elements.createdAt.textContent
                },
                email: currentEmailData,
                exportedAt: new Date().toISOString()
            };

            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            
            const link = document.createElement('a');
            link.href = URL.createObjectURL(dataBlob);
            link.download = `mailslurp-export-${Date.now()}.json`;
            link.click();
            
            showToast('Data exported successfully', 'success');
        });

        function displayEmail(emailData) {
            const content = emailData.htmlBody || emailData.body || 'No content available';
            
            elements.emailContent.innerHTML = `
                <div class="fade-in">
                    <div class="prose max-w-none">
                        ${emailData.htmlBody ? content : `<pre class="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg">${content}</pre>`}
                    </div>
                </div>
            `;

            // Update email details
            document.getElementById('emailFrom').textContent = emailData.from || 'N/A';
            document.getElementById('emailSubject').textContent = emailData.subject || 'No Subject';
            document.getElementById('emailReceived').textContent = formatDate(emailData.receivedAt);
            document.getElementById('emailId').textContent = emailData.id || 'N/A';
            
            elements.emailDetails.classList.remove('hidden');
            elements.emailDetails.classList.add('slide-in');
        }

        // Initialize
        updateStats();
        updateStatus('Ready', 'info');
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template_string(INDEX_HTML)

@app.route('/api/create_inbox', methods=['POST'])
def api_create_inbox():
    """Create a new MailSlurp inbox"""
    try:
        data = request.get_json() or {}
        api_key = data.get('apiKey')
        
        if not api_key:
            logger.warning("API key missing in create_inbox request")
            return jsonify({'error': 'API key is required'}), 400

        # Configure MailSlurp client
        config = mailslurp_client.Configuration()
        config.api_key['x-api-key'] = api_key
        
        with mailslurp_client.ApiClient(config) as client:
            inbox_api = mailslurp_client.InboxControllerApi(client)
            inbox = inbox_api.create_inbox()
            
            logger.info(f"Created inbox: {inbox.id} ({inbox.email_address})")
            
            return jsonify({
                'id': inbox.id,
                'emailAddress': inbox.email_address,
                'createdAt': inbox.created_at.isoformat() if inbox.created_at else None
            })
            
    except ApiException as e:
        logger.error(f"MailSlurp API error in create_inbox: {e}")
        error_msg = f"MailSlurp API error: {e.reason if hasattr(e, 'reason') else str(e)}"
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        logger.error(f"Unexpected error in create_inbox: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/wait_email', methods=['POST'])
def api_wait_email():
    """Wait for the latest email in an inbox"""
    try:
        data = request.get_json() or {}
        api_key = data.get('apiKey')
        inbox_id = data.get('inboxId')
        timeout = data.get('timeout', 60000)  # Default 60 seconds
        
        if not api_key or not inbox_id:
            logger.warning("Missing apiKey or inboxId in wait_email request")
            return jsonify({'error': 'API key and inbox ID are required'}), 400

        # Configure MailSlurp client
        config = mailslurp_client.Configuration()
        config.api_key['x-api-key'] = api_key
        
        with mailslurp_client.ApiClient(config) as client:
            wait_api = mailslurp_client.WaitForControllerApi(client)
            email = wait_api.wait_for_latest_email(
                inbox_id=inbox_id,
                timeout=timeout,
                unread_only=True
            )
            
            logger.info(f"Received email: {email.id} in inbox {inbox_id}")
            
            return jsonify({
                'id': email.id,
                'subject': email.subject,
                'from': email._from,  # Note: 'from' is a reserved keyword
                'body': email.body,
                'htmlBody': email.html_body,
                'receivedAt': email.received_at.isoformat() if email.received_at else None,
                'to': email.to,
                'attachments': len(email.attachments) if email.attachments else 0
            })
            
    except ApiException as e:
        logger.error(f"MailSlurp API error in wait_email: {e}")
        error_msg = f"MailSlurp API error: {e.reason if hasattr(e, 'reason') else str(e)}"
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        logger.error(f"Unexpected error in wait_email: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/extract_otp', methods=['POST'])
def api_extract_otp():
    """Extract OTP/verification codes from email content"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '')
        
        if not content:
            return jsonify({'otp': None, 'message': 'No content provided'})
        
        # Enhanced OTP patterns
        patterns = [
            r'\b(\d{4,8})\b',  # 4-8 digit codes
            r'(?:code|otp|pin)[\s:]*(\d{4,8})',  # "code: 123456"
            r'verification[\s\w]*?(\d{4,8})',  # "verification code 123456"
            r'(\d{6})',  # Common 6-digit pattern
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                otp = match.group(1)
                logger.info(f"Extracted OTP: {otp}")
                return jsonify({'otp': otp, 'pattern': pattern})
        
        logger.info("No OTP found in content")
        return jsonify({'otp': None, 'message': 'No OTP pattern found'})
        
    except Exception as e:
        logger.error(f"Error in extract_otp: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({'error': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Configuration from environment variables
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() in ('1', 'true')
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting MailSlurp Pro application on {host}:{port}")
    logger.info(f"Debug mode: {'enabled' if debug else 'disabled'}")
    
    # Install flask-cors if not available
    try:
        from flask_cors import CORS
    except ImportError:
        logger.warning("flask-cors not installed. Install with: pip install flask-cors")
        CORS = lambda app: None  # Dummy function if CORS not available
    
    app.run(host=host, port=port, debug=debug)