import asyncio, os, httpx, json, time
from dotenv import load_dotenv

load_dotenv()
KEY = os.getenv("OPENROUTER_API_KEY")

models = [
    "minimax/minimax-m3:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-4-31b-it:free",
]

prompt = (
    'Analyze this project idea and return JSON with fields: '
    'name, description, problem, target_users (list), core_features (list). '
    'Idea: I want to build an online supermarket where customers browse products and order online.'
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
    results = []
    for m in models:
        result = await test_model(m)
        results.append(result)

    for model, status, result, elapsed in results:
        print(f"=== {model} ===")
        print(f"Status: {status} | Time: {elapsed:.1f}s")
        if status == 200:
            print(f"Keys: {list(result.keys())}")
            print(f"Name: {result.get('name')}")
            print(f"Features: {result.get('core_features')}")
        else:
            print(f"Error: {result}")
        print()


asyncio.run(main())
