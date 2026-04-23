import logging
import sys

def setup_logger():
    logger = logging.getLogger("ExpenseBot")
    logger.setLevel(logging.INFO)

    # Định dạng log theo yêu cầu: YYYY-MM-DD HH:MM:SS | LEVEL | message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        file_handler = logging.FileHandler("bot.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Không thể tạo file log: {e}")

    return logger

logger = setup_logger()
