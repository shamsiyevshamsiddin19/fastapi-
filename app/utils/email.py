import asyncio
import logging
import time

from ..config import settings

logger = logging.getLogger(__name__)


def send_welcome_email(email: str, username: str) -> None:
    """
    Yangi ro'yxatdan o'tgan foydalanuvchiga xush kelibsiz xatini yuborish.
    Haqiqiy loyihada SMTP/FastMail orqali yuboriladi, hozirda simulyatsiya
    va agar sozlamalar mavjud bo'lsa real yuborish imkoniyati ta'minlangan.
    """
    logger.info(f"Email yuborilmoqda: {email} (foydalanuvchi: {username})")

    # Agar real SMTP sozlamalari mavjud bo'lsa
    if settings.mail_username and settings.mail_password and settings.mail_from:
        try:
            from fastapi_mail import ConnectionConfig, FastMail, MessageSchema

            conf = ConnectionConfig(
                MAIL_USERNAME=settings.mail_username,
                MAIL_PASSWORD=settings.mail_password,
                MAIL_FROM=settings.mail_from,
                MAIL_PORT=settings.mail_port,
                MAIL_SERVER=settings.mail_server,
                MAIL_STARTTLS=True,
                MAIL_SSL_TLS=False,
                USE_CREDENTIALS=True,
            )
            message = MessageSchema(
                subject="Xush kelibsiz! 🎉",
                recipients=[email],
                body=f"""
                <h2>Salom, {username}!</h2>
                <p>Blog API ga xush kelibsiz!</p>
                <p>Hisobingiz muvaffaqiyatli yaratildi.</p>
                """,
                subtype="html",
            )
            fm = FastMail(conf)
            asyncio.run(fm.send_message(message))
            logger.info(f"Haqiqiy email muvaffaqiyatli yuborildi: {email}")
            return
        except (ImportError, OSError, RuntimeError) as exc:
            logger.warning(f"FastMail orqali yuborishda xatolik yuz berdi: {exc}. Simulyatsiyaga o'tilmoqda.")

    # Simulyatsiya (test muhitida tezkor, odatiy holatda 1 soniya)
    delay = 0.01 if settings.environment == "testing" else 1.0
    time.sleep(delay)
    logger.info(f"Email yuborildi: {email} → {username}")


def send_post_notification(author_email: str, title: str) -> None:
    """
    Yangi post yaratilganda muallifga bildirishnoma yuborish (Background Task).
    """
    logger.info(f"Post bildirishi yuborilmoqda: {author_email} → {title}")
    delay = 0.01 if settings.environment == "testing" else 0.5
    time.sleep(delay)
    logger.info(f"Post bildirishi muvaffaqiyatli yuborildi: {title}")


def write_log(action: str, user_id: int | None = None, details: str = "") -> None:
    """
    Faoliyat audit logini fonda yozish.
    """
    logger.info(f"LOG: user={user_id} | action={action} | {details}")
