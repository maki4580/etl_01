import logging
import logging.handlers
import datetime
import pytz
from enum import Enum

class LogLevel(Enum):
    """ログレベルを定義するEnum"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class CustomFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        """
        datetimeオブジェクトをyyyy-mm-ddTHH:MI:ss.sss形式でフォーマットする
        """
        jst = pytz.timezone('Asia/Tokyo')
        dt = datetime.datetime.fromtimestamp(record.created, tz=jst)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
          s = dt.isoformat(sep='T', timespec='milliseconds')
        return s

class Logger:
    def __init__(self, log_file_path, feature_name, level=LogLevel.INFO):
        """
        ログ出力設定の初期化

        Args:
            log_file_path (str): ログファイルのパス
            feature_name (str): 機能名
            level (LogLevel): ログレベル (LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL)
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level.value)
        self.feature_name = feature_name

        # ログのフォーマットを定義
        formatter = CustomFormatter('%(asctime)s [%(levelname)s] [%(feature)s] %(message)s',
                                      datefmt='%Y-%m-%dT%H:%M:%S.%f')
        # 機能名をログレコードに含めるためのフィルタを作成
        class FeatureFilter(logging.Filter):
            def __init__(self, feature_name):
                self.feature_name = feature_name

            def filter(self, record):
                record.feature = self.feature_name
                return True
        feature_filter = FeatureFilter(self.feature_name)

        # コンソール出力用のハンドラを設定
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(feature_filter)
        self.logger.addHandler(console_handler)

        # ファイル出力用のハンドラを設定
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MBでローテーション
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(feature_filter)
        self.logger.addHandler(file_handler)


    def debug(self, message):
        """デバッグログを出力"""
        self.logger.debug(message)

    def info(self, message):
        """情報ログを出力"""
        self.logger.info(message)

    def warning(self, message):
        """警告ログを出力"""
        self.logger.warning(message)

    def error(self, message):
        """エラーログを出力"""
        self.logger.error(message)

    def critical(self, message):
        """致命的なエラーログを出力"""
        self.logger.critical(message)


if __name__ == '__main__':
    # ログファイルのパス
    log_file = "app.log"

    # Loggerクラスのインスタンスを作成 (機能名を指定)
    logger = Logger(log_file, "SampleFeature", level=LogLevel.DEBUG)

    # ログ出力テスト
    logger.debug("これはデバッグメッセージです。")
    logger.info("これは情報メッセージです。")
    logger.warning("これは警告メッセージです。")
    logger.error("これはエラーメッセージです。")
    logger.critical("これは致命的なエラーメッセージです。")

    print(f"ログはコンソールと {log_file} に出力されました。")
    