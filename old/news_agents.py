from datetime import datetime, timedelta
from newsapi import NewsApiClient

api = NewsApiClient(api_key='dcc50abaec994513939365149361eee1')


# 현재 날짜와 1일전 날짜 계산
end_date = datetime.now().date()
start_date = end_date - timedelta(days=30)

ai_news = api.get_everything(q='NVIDIA OR nvidia OR 엔비디아',
                             from_param=start_date,
                             to=end_date,
                             sort_by='relevancy',
                             page_size=30)
# 결과 출력
for article in ai_news['articles']:
    print(f"제목: {article['title']}")
    print(f"링크: {article['url']}")
    print(f"출판 날짜: {article['publishedAt']}")
    print(f"설명: {article['description']}")
    print("\n" + "-"*50 + "\n")

print(f"총 {len(ai_news['articles'])}개의 기사를 찾았습니다.")