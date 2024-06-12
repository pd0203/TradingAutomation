import os
from pybit import HTTP
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키와 시크릿 키 가져오기
bybit_api_key = os.getenv('BYBIT_API_KEY')
bybit_api_secret = os.getenv('BYBIT_API_SECRET')

# Bybit API에 연결
session = HTTP("https://api.bybit.com",
               api_key=bybit_api_key,
               api_secret=bybit_api_secret)
