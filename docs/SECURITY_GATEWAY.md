# تأمين البوابة (Gateway)

## ما تم تفعيله في الكود

| طبقة | التفاصيل |
|------|-----------|
| مفتاح API | `GATEWAY_API_KEY` — إن وُجد يُطلب على `/v1/*` عبر `Authorization: Bearer` أو `X-API-Key` |
| Rate limit | `GATEWAY_RATE_LIMIT_PER_MINUTE` (افتراضي 60/دقيقة لكل IP) |
| CORS | `GATEWAY_CORS_ORIGINS` — قائمة محددة بدل `*` في الإنتاج |
| Headers | nosniff, frame deny, referrer, CSP صارم على استجابات API |
| Stats | `/v1/stats` يخضع لنفس المصادقة عند تفعيل المفتاح |
| Health | `/health` يبقى عاماً للـ load balancer |

## الإنتاج

```bash
GATEWAY_API_KEY=$(openssl rand -hex 32)
GATEWAY_CORS_ORIGINS=https://your-frontend.example
GATEWAY_RATE_LIMIT_PER_MINUTE=120
```

مرر نفس المفتاح لخدمة Agents عبر `GATEWAY_API_KEY_INTERNAL` عند الاستدعاء الداخلي.

## المراقبة

- API: `GET /v1/stats` → latency avg/p50/p95/p99، success rate، تكلفة، cooldown
- واجهة: `apps/web/monitor.html`
