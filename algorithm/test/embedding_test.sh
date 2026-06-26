# 测试embedding

source "./config.cfg"


if [ -n "$EMBEDDING_MODEL_KEY" ]
then
  curl --location --request POST $EMBEDDING_MODEL_URL \
       --header 'Content-Type: application/json' \
       --data '{
	 "model": "'"$EMBEDDING_MODEL_ID"'",
	 "input": "你好"
  }'
else
  curl --location --request POST $EMBEDDING_MODEL_URL \
       --header 'Content-Type: application/json' \
       --header 'Authorization: Bearer "'"$EMBEDDING_MODEL_KEY"'"' \
       --data '{
         "model": "'"$EMBEDDING_MODEL_ID"'",
         "input": "你好"
  }'
fi
