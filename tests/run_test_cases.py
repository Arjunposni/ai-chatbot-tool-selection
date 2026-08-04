import json
from app.intent.hybrid import detect_intent_hybrid

with open("data/test_cases.json", "r") as f:
    test_cases = json.load(f)

for case in test_cases:
    query = case["query"]
    expected = case["expected_intent"]
    category = case["category"]

    result = detect_intent_hybrid(query, patient_id="p1")
    actual = result.get("intent")

    print(f"[{case['id']}] ({category}) {query}")
    print(f"    Expected: {expected}")
    print(f"    Actual:   {actual}")
    print(f"    Method:   {result.get('method')}")
    print(f"    Matched:  {result.get('matched')}")
    if not result.get("matched"):
        print(f"    Reason:   {result.get('reason')}")
    print()