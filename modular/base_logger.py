import logging

class BaseLogger:
    """
    Base class for providing reusable logging with class-specific names.
    """

    @classmethod
    def get_logger(cls):
        """
        Returns a class-specific logger configured with handlers and formatters.
        Sets the default logging level to WARNING.
        """
        logger = logging.getLogger(cls.__name__)  # Use the class name as the logger name
        if not logger.handlers:  # Ensure the logger is configured only once
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False  # Prevent logs from propagating to the root logger
        
        # Set the default logging level to WARNING
        logger.setLevel(logging.WARNING)
        
        return logger