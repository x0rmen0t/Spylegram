import logging

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler("spylegram.log")
file_handler.setFormatter(formatter)


def get_logger(logger_name: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.ERROR)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
