# Adobe Acrobat Sign Connector — Connector Discovery

**Official Documentation:** https://acrobat.adobe.com/us/en/sign.html  
**Base URL:** https://api.echosign.com/api/rest/v6  
**Auth Model:** OAuth 2.0 Bearer Token (Integration Key)  

## Основные сущности вендора
- соглашения (/agreements), библиотеки документов (/libraryDocuments), вебхуки (/webhooks), участники

## Лимиты и особенности API
- Соблюдение Rate Limits вендора, обработка HTTP 429 с экспоненциальным backoff.
- Валидация входных данных по Pydantic-схемам вендора до отправки запроса.
- Тестовая точка проверки подключения: `GET /api/rest/v6/baseUris`.
