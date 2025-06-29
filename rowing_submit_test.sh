curl -X POST \
  http://localhost:8000/health/rowing/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: HandwritingRepair" \
  -d '{
    "image_url": "https://media.discordapp.net/attachments/1354033220450259005/1354734387765186612/Screenshot_20250327-193021.png?ex=67e7afb7&is=67e65e37&hm=9b3a5e31ea8153a33eb59e9c70b91e49130b54b6c59c2c75c1b58e11fcfcea37&=&format=webp&quality=lossless&width=211&height=960",
    "workout_date": "2025-03-29T10:30:00Z"
  }'
