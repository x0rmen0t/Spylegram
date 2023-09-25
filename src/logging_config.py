import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler('file.log')
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)


# import logging
# import json
#
# logger = logging.getLogger(__name__)
#
# class JsonFormatter(logging.Formatter):
#     def format(self, record):
#         log_data = {
#             'levelname': record.levelname,
#             'asctime': self.formatTime(record),
#             'name': record.name,
#             'message': record.msg,
#             'module': record.module,
#             'filename': record.filename,
#             'lineno': record.lineno
#         }
#         return json.dumps(log_data)
#
# def setup_logging():
#     # Create and configure the logger
#
#     logger.setLevel(logging.DEBUG)
#
#     log_file = 'app.log'
#     file_handler = logging.FileHandler(log_file)
#     file_handler.setLevel(logging.WARNING)
#     file_formatter = JsonFormatter()
#     file_handler.setFormatter(file_formatter)
#     logger.addHandler(file_handler)
#
#     # Create a console handler
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     console_formatter = logging.Formatter('[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s')
#     console_handler.setFormatter(console_formatter)
#     logger.addHandler(console_handler)
#
#     # return logger
#
#
# setup_logging()



# import logging
# import json
#
# # Define a global logger object for your module
#
#
# class JsonFormatter(logging.Formatter):
#     def format(self, record):
#         log_data = {
#             'levelname': record.levelname,
#             'asctime': self.formatTime(record),
#             'name': record.name,
#             'message': record.msg,
#             'module': record.module,
#             'filename': record.filename,
#             'lineno': record.lineno
#         }
#         return json.dumps(log_data)
#
#
# def setup_logging():
#     # Configure the global logger, not a local one
#     logger.setLevel(logging.DEBUG)
#     json_formatter = JsonFormatter()
#     log_file = 'app.log'
#     file_handler = logging.FileHandler(log_file)
#     file_handler.setLevel(logging.WARNING)
#
#     file_handler.setFormatter(json_formatter)
#
#     logger.addHandler(file_handler)
#
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     console_formatter = logging.Formatter('[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s')
#     console_handler.setFormatter(console_formatter)
#     logger.addHandler(console_handler)
#
#     return logger
#
#
# # Call setup_logging only once at the beginning of your script/module
# setup_logging()
#
# # import logging
# # import json
# # from tqdm import tqdm
# #
# #
# # class JsonFormatter(logging.Formatter):
# #     def format(self, record):
# #         log_data = {
# #             'levelname': record.levelname,
# #             'asctime': self.formatTime(record),
# #             'name': record.name,
# #             'message': record.msg,
# #             'module': record.module,
# #             'filename': record.filename,
# #             'lineno': record.lineno
# #         }
# #         return json.dumps(log_data)
# #
# #
# # class TqdmLoggingHandler(logging.Handler):
# #     def __init__(self, level=logging.NOTSET):
# #         super().__init__(level)
# #
# #     def emit(self, record):
# #         try:
# #             tqdm.write(self.format(record))  # Write log messages to tqdm output
# #         except Exception:
# #             self.handleError(record)
# #
# #
# # def setup_logging():
# #     logger = logging.getLogger(__name__)
# #     logger.setLevel(logging.DEBUG)
# #
# #     json_formatter = JsonFormatter()
# #
# #     # Add a TqdmLoggingHandler to capture log messages and display them with tqdm
# #     tqdm_handler = TqdmLoggingHandler()
# #     tqdm_handler.setFormatter(json_formatter)
# #     logger.addHandler(tqdm_handler)
# #
# #     log_file = 'app.log'
# #     file_handler = logging.FileHandler(log_file)
# #     file_handler.setLevel(logging.WARNING)
# #     file_handler.setFormatter(json_formatter)
# #     logger.addHandler(file_handler)
# #
# #     console_handler = logging.StreamHandler()
# #     console_handler.setLevel(logging.INFO)
# #     console_formatter = logging.Formatter('[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s')
# #     console_handler.setFormatter(console_formatter)
# #     logger.addHandler(console_handler)
# #
# #     return logger
# #
# #
# # logger = setup_logging()
