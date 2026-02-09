"""Telegram Bot for LinkedIn Autoposter.

Provides command handlers for draft approval workflow:
- /start - Bot greeting
- /pending - List pending drafts
- /approve <id> - Approve a draft
- /reject <id> <reason> - Reject a draft
- /preview <id> - View full draft content
- /help - Show available commands

Also handles inline keyboard callbacks for button-based approval.
"""

import logging
import uuid

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes

from ..config import settings
from ..db import SessionLocal
from ..models import Comment, Draft, DraftStatus
from ..services.audit import log_audit
from ..services.telegram_service import format_draft_notification
from ..services.workflow import approve_draft_and_schedule


def _get_comment_by_short_id(db, short_id: str) -> Comment | None:
    """Look up a comment by short ID prefix."""
    if len(short_id) >= 8:
        comments = db.query(Comment).filter(Comment.escalated.is_(True)).all()
        for comment in comments:
            if str(comment.id).startswith(short_id):
                return comment
    return None

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Authorization
# ─────────────────────────────────────────────────────────────────────────────

def _is_authorized(update: Update) -> bool:
    """Check if the update is from an authorized chat."""
    if not settings.telegram_chat_id:
        return True
    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    return chat_id == str(settings.telegram_chat_id)


def _get_draft_by_id(db, draft_id: str) -> Draft | None:
    """Look up a draft by full UUID or short prefix."""
    # Try full UUID first
    try:
        parsed_id = uuid.UUID(draft_id)
        return db.query(Draft).filter(Draft.id == parsed_id).first()
    except ValueError:
        pass

    # Try matching by prefix (for callback data)
    if len(draft_id) >= 8:
        drafts = db.query(Draft).filter(
            Draft.status == DraftStatus.pending
        ).all()
        for draft in drafts:
            if str(draft.id).startswith(draft_id):
                return draft

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Command Handlers
# ─────────────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    if not _is_authorized(update):
        return

    welcome_text = """👋 LinkedIn Autoposter Bot

I help you manage your LinkedIn content workflow.

Commands:
/pending - List pending drafts
/approve <id> - Approve a draft for publishing
/reject <id> <reason> - Reject a draft
/preview <id> - View full draft content
/help - Show this message

You'll receive notifications when new drafts are ready for review."""

    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    if not _is_authorized(update):
        return
    await start(update, context)


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /pending command - list pending drafts."""
    if not _is_authorized(update):
        return

    db = SessionLocal()
    try:
        drafts = (
            db.query(Draft)
            .filter(Draft.status == DraftStatus.pending)
            .order_by(Draft.created_at.desc())
            .limit(5)
            .all()
        )
        if not drafts:
            await update.message.reply_text("✅ No pending drafts.")
            return

        lines = ["📋 Pending Drafts:\n"]
        for draft in drafts:
            short_id = str(draft.id)[:8]
            guardrail = "✅" if draft.guardrail_check_passed else "⚠️"
            lines.append(
                f"{guardrail} {short_id}... | {draft.sub_theme} | {draft.format.value}"
            )
        lines.append(f"\nUse /preview <id> to view full content.")
        await update.message.reply_text("\n".join(lines))
    finally:
        db.close()


async def preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /preview command - show full draft content."""
    if not _is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /preview <draft_id>")
        return

    draft_id = context.args[0]
    db = SessionLocal()
    try:
        draft = _get_draft_by_id(db, draft_id)
        if not draft:
            await update.message.reply_text("❌ Draft not found.")
            return

        text = format_draft_notification(draft)
        await update.message.reply_text(text)
    finally:
        db.close()


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /approve command - approve a pending draft."""
    if not _is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <draft_id>")
        return

    draft_id = context.args[0]
    db = SessionLocal()
    try:
        draft = _get_draft_by_id(db, draft_id)
        if not draft:
            await update.message.reply_text("❌ Draft not found.")
            return
        if draft.status != DraftStatus.pending:
            await update.message.reply_text("⚠️ Draft is not pending.")
            return

        post = approve_draft_and_schedule(db=db, draft=draft, scheduled_time=None)
        log_audit(
            db=db,
            actor="telegram",
            action="draft.approve",
            resource_type="draft",
            resource_id=str(draft.id),
        )

        scheduled_str = post.scheduled_time.strftime("%H:%M UTC") if post.scheduled_time else "Unknown"
        await update.message.reply_text(
            f"✅ Draft approved!\n\n"
            f"Scheduled for: {scheduled_str}\n"
            f"Draft ID: {draft.id}"
        )
    finally:
        db.close()


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reject command - reject a pending draft."""
    if not _is_authorized(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reject <draft_id> <reason>")
        return

    draft_id = context.args[0]
    reason = " ".join(context.args[1:])

    db = SessionLocal()
    try:
        draft = _get_draft_by_id(db, draft_id)
        if not draft:
            await update.message.reply_text("❌ Draft not found.")
            return
        if draft.status != DraftStatus.pending:
            await update.message.reply_text("⚠️ Draft is not pending.")
            return

        draft.status = DraftStatus.rejected
        draft.rejection_reason = reason
        db.commit()

        log_audit(
            db=db,
            actor="telegram",
            action="draft.reject",
            resource_type="draft",
            resource_id=str(draft.id),
            detail={"reason": reason},
        )

        await update.message.reply_text(
            f"❌ Draft rejected.\n\n"
            f"Reason: {reason}\n"
            f"Draft ID: {draft.id}"
        )
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Callback Query Handlers (Inline Keyboard)
# ─────────────────────────────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button callbacks."""
    query = update.callback_query
    await query.answer()

    if not _is_authorized(update):
        await query.edit_message_text("⚠️ Unauthorized.")
        return

    data = query.data
    if ":" not in data:
        await query.edit_message_text("⚠️ Invalid callback data.")
        return

    action, short_id = data.split(":", 1)

    db = SessionLocal()
    try:
        draft = _get_draft_by_id(db, short_id)
        if not draft:
            await query.edit_message_text("❌ Draft not found.")
            return

        if action == "approve":
            if draft.status != DraftStatus.pending:
                await query.edit_message_text("⚠️ Draft is no longer pending.")
                return

            post = approve_draft_and_schedule(db=db, draft=draft, scheduled_time=None)
            log_audit(
                db=db,
                actor="telegram",
                action="draft.approve",
                resource_type="draft",
                resource_id=str(draft.id),
            )

            scheduled_str = post.scheduled_time.strftime("%H:%M UTC") if post.scheduled_time else "Unknown"
            await query.edit_message_text(
                f"✅ Draft approved!\n\n"
                f"Scheduled for: {scheduled_str}\n"
                f"Draft ID: {draft.id}"
            )

        elif action == "reject":
            if draft.status != DraftStatus.pending:
                await query.edit_message_text("⚠️ Draft is no longer pending.")
                return

            # For inline reject, use a default reason
            draft.status = DraftStatus.rejected
            draft.rejection_reason = "Rejected via inline button"
            db.commit()

            log_audit(
                db=db,
                actor="telegram",
                action="draft.reject",
                resource_type="draft",
                resource_id=str(draft.id),
                detail={"reason": "Rejected via inline button"},
            )

            await query.edit_message_text(
                f"❌ Draft rejected.\n\n"
                f"Use /reject <id> <reason> for custom rejection reason.\n"
                f"Draft ID: {draft.id}"
            )

        elif action == "preview":
            text = format_draft_notification(draft)
            # Send as new message since preview can be long
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
            )

        elif action in ("resolve", "ignore"):
            # Handle comment escalation callbacks
            comment = _get_comment_by_short_id(db, short_id)
            if not comment:
                await query.edit_message_text("❌ Comment not found.")
                return

            if comment.manual_reply_sent:
                await query.edit_message_text("⚠️ This escalation has already been resolved.")
                return

            comment.manual_reply_sent = True
            comment.manual_reply_text = f"[{action.upper()}D via Telegram]"
            db.commit()

            log_audit(
                db=db,
                actor="telegram",
                action=f"comment.{action}",
                resource_type="comment",
                resource_id=str(comment.id),
            )

            if action == "resolve":
                await query.edit_message_text(
                    f"✅ Escalation resolved.\n\n"
                    f"Comment ID: {comment.id}"
                )
            else:
                await query.edit_message_text(
                    f"🚫 Escalation ignored.\n\n"
                    f"Comment ID: {comment.id}"
                )

        else:
            await query.edit_message_text("⚠️ Unknown action.")

    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# Bot Builder
# ─────────────────────────────────────────────────────────────────────────────

def build_bot():
    """Build and configure the Telegram bot application."""
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("preview", preview))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))

    # Callback query handler for inline keyboards
    app.add_handler(CallbackQueryHandler(handle_callback))

    return app


if __name__ == "__main__":
    bot = build_bot()
    bot.run_polling()
