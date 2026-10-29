"""Register a dummy problem set in Firestore to check the API before real sets are generated.

Usage: cd api && uv run python ../scripts/seed_dummy_set.py --project <gcp-project> --grade pre2
"""

import argparse

from google.cloud import firestore

from eiken_api.models import ProblemSet


def dummy_set(grade: str) -> ProblemSet:
    set_id = f"{grade}_dummy"
    return ProblemSet.model_validate(
        {
            "id": set_id,
            "grade": grade,
            "enabled": True,
            "topic": "Recycling",
            "voice": "en-US-Chirp3-HD-Aoede",
            "passage": {
                "title": "Recycling at Home",
                "text": (
                    "Many people today are interested in protecting the environment. Some families sort their "
                    "garbage carefully at home, and by doing so, they can help reduce waste. Recycling is becoming "
                    "a part of daily life."
                ),
                "key_sentence": (
                    "Some families sort their garbage carefully at home, and by doing so, they can help reduce waste."
                ),
            },
            "questions": [
                {
                    "no": 1,
                    "type": "passage",
                    "text": "According to the passage, how can some families help reduce waste?",
                    "model_answer": "By sorting their garbage carefully at home.",
                },
                {
                    "no": 2,
                    "type": "picture_a",
                    "text": "Now, please look at the people in Picture A. They are doing different things. "
                    "Tell me as much as you can about what they are doing.",
                    "actions": [
                        "A man is carrying a box.",
                        "A woman is watering flowers.",
                        "A boy is riding a bicycle.",
                        "A girl is feeding a dog.",
                        "A man is washing a car.",
                    ],
                },
                {
                    "no": 3,
                    "type": "picture_b",
                    "text": "Now, look at the woman in Picture B. Please describe the situation.",
                    "model_answer": "She wants to open the door, but she can't because her hands are full.",
                },
                {
                    "no": 4,
                    "type": "opinion",
                    "text": "Do you think more people will recycle in the future?",
                    "follow_up_yes": "Why?",
                    "follow_up_no": "Why not?",
                },
                {
                    "no": 5,
                    "type": "personal",
                    "text": "Do you often cook at home?",
                    "follow_up_yes": "Please tell me more.",
                    "follow_up_no": "Why not?",
                },
            ],
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--grade", required=True)
    args = parser.parse_args()

    problem_set = dummy_set(args.grade)
    client = firestore.Client(project=args.project)
    client.collection("sets").document(problem_set.id).set(
        {**problem_set.model_dump(mode="json"), "created_at": firestore.SERVER_TIMESTAMP}
    )
    print(f"registered sets/{problem_set.id}")


if __name__ == "__main__":
    main()
