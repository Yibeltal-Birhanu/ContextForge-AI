import asyncio, os, httpx, json, time
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("OPENROUTER_API_KEY")

models = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]

prompt = (
    'Return valid JSON with fields: name (string), description (string), '
    'core_features (list of strings). '
    'Project: online supermarket.'
)


async def test_model(model):
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                },
            )
            elapsed = time.time() - start
            if resp.status_code != 200:
                return model, resp.status_code, str(resp.json())[:200], elapsed
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0].strip()
            parsed = json.loads(content)
            return model, 200, parsed, elapsed
    except Exception as e:
        return model, "error", str(e)[:200], time.time() - start


async def main():
    for m in models:
        result = await test_model(m)
        model, status, res, elapsed = result
        print(f"=== {model} ===")
        print(f"Status: {status} | Time: {elapsed:.1f}s")
        if status == 200:
            print(f"Keys: {list(res.keys())}")
            print(f"Name: {res.get('name')}")
        else:
            print(f"Error: {res}")
        print()


asyncio.run(main())
