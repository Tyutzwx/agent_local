# 测试qwen 

source "./config.cfg"

if [ -n "$LLM_MODEL_KEY" ]
then
  curl --location --request POST $LLM_MODEL_URL \
       --header 'Content-Type: application/json' \
       --data-raw '{
         "model": "'"$LLM_MODEL_ID"'",
	 "messages": [
	 {
            "role": "system",
            "content": "You are a helpful assistant."
         },
         {
            "role": "user",
            "content": "你好"
         }
	 ],
         "max_tokens": 512,
         "temperature": 0.7
  }'
else
  curl --location --request POST $LLM_MODEL_URL \
       --header 'Content-Type: application/json' \
       --header 'Authorization: Bearer "'"$LLM_MODEL_KEY"'"' \
       --data-raw '{
         "model": "'"$LLM_MODEL_ID"'",
         "messages": [
         {
            "role": "system",
            "content": "You are a helpful assistant."
         },
         {
            "role": "user",
            "content": "你好"
         }
         ],
         "max_tokens": 512,
         "temperature": 0.7
  }'
fi
