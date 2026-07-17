import os
import requests
import logging

logger = logging.getLogger(__name__)

class PaymentGatewayService:
    """
    Adapter to communicate with external payment APIs (like mock KBZPay/WavePay).
    Supports live network calls or an automatic local offline fallback.
    """
    # Looks for an environment variable first. If none is set, defaults to offline mode.
    API_URL = os.getenv("PAYMENT_API_URL", "MOCK_OFFLINE")

    @classmethod
    def authorize_payment(cls, order_id, amount):
        # 🌟 1. OFFLINE FALLBACK PATH (Perfect for local development/seeding)
        if cls.API_URL == "MOCK_OFFLINE":
            logger.info(f"Payment for {order_id} processed locally via offline mock mode.")
            return "APPROVED", f"TX-LOCAL-OFFLINE-{order_id[-4:]}"

        # 🌐 2. LIVE EXTERNAL INTEGRATION PATH (Meets the business scenario requirements)
        payload = {
            "order_id": order_id,
            "amount": float(amount),
            "currency": "USD"
        }
        
        try:
            logger.info(f"Hitting external payment gateway at: {cls.API_URL}")
            response = requests.post(cls.API_URL, json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Expected payload from external service: {"status": "APPROVED", "transaction_ref": "TX-1001"}
                return data.get("status", "DECLINED"), data.get("transaction_ref")
                
            return "DECLINED", None
            
        except requests.RequestException as e:
            logger.error(f"External Payment Gateway network failure: {e}")
            # Fail-closed to prevent unpaid orders from completing if the endpoint crashes
            return "DECLINED", None