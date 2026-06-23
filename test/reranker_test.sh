# 测试reranker

source "./config.cfg"


if [ -n "$RERANKER_MODEL_KEY" ]
then
  curl --location --request POST $RERANKER_MODEL_URL \
       --header 'Content-Type: application/json' \
       --data '{
	 "model": "'"$RERANKER_MODEL_ID"'",
         "query": "你好",
         "documents": ["A man is eating food.",
	   "A man is eating a piece of bread.",
           "The girl is carrying a baby.",
           "A man is riding a horse.",
           "A woman is playing violin.",
           "你好"]
  }'
else
  curl --location --request POST $RERANKER_MODEL_URL \
       --header 'Content-Type: application/json' \
       --header 'Authorization: Bearer "'"$RERANKER_MODEL_KEY"'"' \
       --data '{
         "model": "'"$RERANKER_MODEL_ID"'",
         "query": "你好",
         "documents": ["A man is eating food.",
           "A man is eating a piece of bread.",
           "The girl is carrying a baby.",
           "A man is riding a horse.",
           "A woman is playing violin.",
           "你好"]
  }'
fi
