
import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.payment import Payment
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    
    async def create_checkout_session(self, user: User, plan_type: str) -> dict:
        if plan_type == "monthly":
            price_id = "price_monthly_subscription"  # Replace with actual Stripe price ID
        elif plan_type == "credit_pack":
            price_id = "price_credit_pack"  # Replace with actual Stripe price ID
        else:
            raise ValueError("Invalid plan type")
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription' if plan_type == "monthly" else 'payment',
            success_url=f"{settings.FRONTEND_URL}/dashboard?success=true",
            cancel_url=f"{settings.FRONTEND_URL}/dashboard?canceled=true",
            customer_email=user.email,
            metadata={
                'user_id': str(user.id),
                'plan_type': plan_type
            }
        )
        
        return {"checkout_url": session.url}
    
    async def handle_webhook(self, payload: bytes, sig_header: str, db: AsyncSession):
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = int(session['metadata']['user_id'])
            plan_type = session['metadata']['plan_type']
            
            # Update user plan/credits
            user = await db.get(User, user_id)
            if user:
                if plan_type == "monthly":
                    user.plan = "monthly"
                elif plan_type == "credit_pack":
                    user.credits_balance += 100
                
                # Create payment record
                payment = Payment(
                    user_id=user_id,
                    stripe_charge_id=session['id'],
                    amount=session['amount_total'] / 100,  # Convert from cents
                    type=plan_type,
                    status="completed"
                )
                db.add(payment)
                await db.commit()