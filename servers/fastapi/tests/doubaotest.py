import os

from volcenginesdkarkruntime import Ark


# For more information，please check this document（https://www.volcengine.com/docs/82379/1263279）
client = Ark(api_key="7b364b53-9f4b-4055-b0d2-b6e2ec08dcba")


if __name__ == "__main__":
    resp = client.chat.completions.create(
        model="doubao-seed-1-8-251228",
        messages=[{"content":"天空为什么是蓝色的？","role":"user"}],
        stream=True,
        thinking={"type":"disabled"},
    )
    for chunk in resp:
        print(chunk.choices[0].delta.content)
        

