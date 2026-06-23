import os
import logging
from app import create_app

# Configure standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

if __name__ == '__main__':
    # Retrieve port from environment or default to 5000
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("-" * 50)
    logger.info(f"CreatorOS MVP Server Starting on http://127.0.0.1:{port}")
    logger.info("Design Palette: Orange & Cream grid template")
    logger.info("Features ready: Memory, Opportunity Alerts, AI Generator")
    logger.info("-" * 50)
    
    app.run(host='127.0.0.1', port=port, debug=debug_mode)
