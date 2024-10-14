import logging


def get_logger(name: str, file_name: str = "main") -> logging.Logger:
    py_logger = logging.getLogger(name)
    if not py_logger.hasHandlers():
        py_logger.setLevel(logging.DEBUG)

        py_handler = logging.FileHandler(f"logs/{file_name}.log", mode='a')
        py_formatter = logging.Formatter(
            "[%(asctime)s][%(name)s][%(levelname)s]: %(message)s")

        py_handler.setFormatter(py_formatter)
        py_logger.addHandler(py_handler)
    return py_logger


if __name__ == "__main__":
    py_logger = get_logger("logger.py")
    py_logger.info("Status - OK")
