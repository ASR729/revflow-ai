"""
RevFlow Executor — Simulated Comms Writer.

Per §3.2, §8.4: No HTTP client exists in this code path at all.
Writes to simulated_actions and contact_log. Never transmits.
"""
import random
from datetime import datetime, timezone
from typing import Optional

from revflow.contracts.enums import SimulatedChannel, Locale
from revflow.adapters.llm import get_llm_adapter
from revflow.ingestion.normaliser import Event
from revflow.db.connection import get_connection


# Templates for simulated outreach (when LLM unavailable)
TEMPLATES = {
    "sms": {
        "en": "Dear customer, your payment of ₹{amount:.2f} is overdue. Please pay at your earliest convenience. Thank you.",
        "hi": "प्रिय ग्राहक, आपका ₹{amount:.2f} का भुगतान बकाया है। कृपया जल्द से जल्द भुगतान करें। धन्यवाद।",
        "hinglish": "Dear customer, aapka ₹{amount:.2f} ka payment overdue hai. Please jaldi pay karein. Thanks!",
    },
    "whatsapp": {
        "en": "Hi! This is a reminder about your pending payment of ₹{amount:.2f}. Please complete it soon to avoid service disruption.",
        "hi": "नमस्ते! यह आपके ₹{amount:.2f} के बकाया भुगतान की याद दिला रहा है। कृपया जल्द पूरा करें।",
        "hinglish": "Hi! Reminder: aapka ₹{amount:.2f} pending hai. Please jaldi complete karein.",
    },
    "voice_script": {
        "en": "Hello, this is an automated reminder from our billing department. Your payment of ₹{amount:.2f} is overdue. Please make the payment at your earliest convenience. Thank you.",
        "hi": "नमस्ते, यह हमारे बिलिंग विभाग की ओर से एक स्वचालित अनुस्मारक है। आपका ₹{amount:.2f} का भुगतान बकाया है। कृपया जल्द से जल्द भुगतान करें। धन्यवाद।",
        "hinglish": "Hello, yeh billing department se automated reminder hai. Aapka ₹{amount:.2f} overdue hai. Please jaldi payment karein. Thank you.",
    },
}


def get_template(channel: SimulatedChannel, locale: Locale) -> str:
    """Get template for channel/locale."""
    channel_templates = TEMPLATES.get(channel.value, TEMPLATES["sms"])
    return channel_templates.get(locale.value, channel_templates["en"])


async def generate_nudge_body(event: Event, cause: str, locale: Locale, tone: str) -> str:
    """
    Generate outreach body text.

    Tries LLM first, falls back to template.
    """
    adapter = get_llm_adapter()
    body = await adapter.generate_outreach(event, cause, locale.value, tone)

    if body and len(body.strip()) > 10:
        return body.strip()

    # Fallback to template
    template = get_template(SimulatedChannel.SMS, locale)  # Default to SMS template
    amount = event.amount_inr / 100
    return template.format(amount=amount)


async def write_simulated_nudge(
    run_id: str,
    audit_log_id: int,
    event: Event,
    cause: str,
    locale: Locale = Locale.EN,
    channel: SimulatedChannel = SimulatedChannel.SMS,
    tone: str = "neutral",
) -> int:
    """
    Write a simulated nudge to simulated_actions and contact_log.

    Returns the simulated_actions row ID.
    """
    body_text = await generate_nudge_body(event, cause, locale, tone)

    with get_connection() as conn:
        # Insert simulated_actions
        cursor = conn.execute(
            """INSERT INTO simulated_actions (
                audit_log_id, channel, locale, body_text, tts_audio_path, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                audit_log_id,
                channel.value,
                locale.value,
                body_text,
                None,  # tts_audio_path - optional
                "simulated",
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        sim_id = cursor.lastrowid

        # Insert contact_log for frequency cap tracking
        conn.execute(
            """INSERT INTO contact_log (run_id, customer_id, contact_date, audit_log_id)
               VALUES (?, ?, ?, ?)""",
            (
                run_id,
                event.customer_id,
                datetime.now(timezone.utc).date().isoformat(),
                audit_log_id,
            ),
        )

    return sim_id