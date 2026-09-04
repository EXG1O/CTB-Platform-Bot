from typing import Final

PAYMENT_SUPPORT_COMMAND: Final[str] = 'paysupport'

PRE_PAYMENT_FAILED_SHORT_TEXT: Final[str] = 'Unable to process this purchase.'

PAYMENT_FAILED_TEXT: Final[str] = f"""\
⚠️ <b>Payment processing error.</b>

💬 Please contact support using the /{PAYMENT_SUPPORT_COMMAND} command.
"""
PAYMENT_SUCCESS_TEXT: Final[str] = f"""\
🎉 <b>You have successfully purchased a Premium subscription!</b> ({{period_days}} days / {{amount_stars}} stars)

❤️ <b>Thank you for supporting us!</b> Your contribution helps us keep improving the project.

💬 If you have any questions about your subscription or payment, please contact support using the /{PAYMENT_SUPPORT_COMMAND} command.
"""

PAYMENT_SUPPORT_TEXT: Final[str] = """\
If you have payment issues, please contact @exg1o via Telegram for assistance.
"""
