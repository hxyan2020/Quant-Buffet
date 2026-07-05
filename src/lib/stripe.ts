import Stripe from "stripe";

let cached: Stripe | null = null;

export function stripeServer(): Stripe | null {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key) {
    return null;
  }
  if (!cached) {
    cached = new Stripe(key);
  }
  return cached;
}
