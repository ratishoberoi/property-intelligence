#!/usr/bin/env python
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
AREAS = {
    "Canary Wharf": (51.5054, -0.0235, "E14"),
    "Stratford": (51.5413, -0.0033, "E20"),
    "Greenwich": (51.4826, -0.0077, "SE10"),
    "Shoreditch": (51.5236, -0.0751, "EC2A"),
    "Islington": (51.5465, -0.1058, "N1"),
    "Camden": (51.5390, -0.1426, "NW1"),
    "Hackney": (51.5450, -0.0553, "E8"),
    "Chelsea": (51.4875, -0.1687, "SW3"),
    "Fulham": (51.4800, -0.1950, "SW6"),
    "Wimbledon": (51.4214, -0.2064, "SW19"),
    "Croydon": (51.3762, -0.0982, "CR0"),
    "Battersea": (51.4638, -0.1677, "SW11"),
    "Clapham": (51.4626, -0.1380, "SW4"),
}
AREA_RENT = {
    "Canary Wharf": 2850,
    "Stratford": 2350,
    "Greenwich": 2250,
    "Shoreditch": 3000,
    "Islington": 2800,
    "Camden": 2750,
    "Hackney": 2500,
    "Chelsea": 4200,
    "Fulham": 3300,
    "Wimbledon": 2600,
    "Croydon": 1750,
    "Battersea": 3200,
    "Clapham": 2850,
}
AMENITIES = ["transport", "gym", "concierge", "balcony", "garden", "parking", "pet-friendly", "river-view", "school", "workspace"]
PROPERTY_TYPES = ["flat", "house", "maisonette", "studio"]
EVENT_TYPES = [
    "ENQUIRY",
    "QUALIFIED",
    "PROPERTY_VIEW",
    "VIEWING_BOOKED",
    "VIEWING_CANCELLED",
    "FEEDBACK",
    "FOLLOW_UP",
    "APPLICATION_STARTED",
    "APPLICATION_SUBMITTED",
    "APPLICATION_REJECTED",
    "OFFER_MADE",
    "OFFER_ACCEPTED",
    "MESSAGE_RECEIVED",
    "MESSAGE_SENT",
    "NO_RESPONSE",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    parser.add_argument("--properties", type=int, default=2000)
    parser.add_argument("--applicants", type=int, default=1000)
    args = parser.parse_args()
    random.seed(SEED)
    np.random.seed(SEED)
    root = Path(__file__).resolve().parents[2]
    out = Path(args.out).resolve() if args.out else root / "data" / "processed"
    out.mkdir(parents=True, exist_ok=True)
    properties = generate_properties(args.properties)
    applicants = generate_applicants(args.applicants)
    properties, applicants = inject_demo_entities(properties, applicants)
    interactions, viewings, feedback, conversations, labels = generate_activity(properties, applicants)
    write(out, properties, applicants, interactions, viewings, feedback, conversations, labels)
    print(f"Generated synthetic dataset in {out}")
    print(f"properties={len(properties)} applicants={len(applicants)} interactions={len(interactions)} viewings={len(viewings)} feedback={len(feedback)} conversations={len(conversations)}")


def generate_properties(n: int) -> pd.DataFrame:
    rows = []
    today = date(2026, 8, 13)
    for idx in range(n):
        area = random.choice(list(AREAS))
        lat, lng, prefix = AREAS[area]
        bedrooms = int(np.random.choice([0, 1, 2, 3, 4], p=[0.08, 0.28, 0.38, 0.2, 0.06]))
        ptype = "studio" if bedrooms == 0 else random.choices(PROPERTY_TYPES[:-1], weights=[0.72, 0.2, 0.08])[0]
        base = AREA_RENT[area] + bedrooms * 430 + np.random.normal(0, 260)
        rent = int(max(950, round(base / 25) * 25))
        amenities = set(random.sample(AMENITIES, k=random.randint(3, 6)))
        furnished = random.random() < 0.72
        parking = "parking" in amenities or random.random() < 0.22
        garden = "garden" in amenities or (ptype == "house" and random.random() < 0.45)
        balcony = "balcony" in amenities or random.random() < 0.34
        pets = "pet-friendly" in amenities or random.random() < 0.28
        rows.append(
            {
                "property_id": f"P-{1000 + idx}",
                "postcode": f"{prefix} {random.randint(1, 9)}{random.choice('ABCDEFGH')}{random.choice('JKLMNP')}",
                "city": "London",
                "area": area,
                "property_type": ptype,
                "bedrooms": bedrooms,
                "bathrooms": max(1, min(3, bedrooms + random.choice([0, 0, 1]))),
                "rent_pcm": rent,
                "sale_price": "",
                "size_sqft": int(420 + max(bedrooms, 1) * 260 + np.random.normal(0, 80)),
                "furnished": furnished,
                "parking": parking,
                "garden": garden,
                "balcony": balcony,
                "pets_allowed": pets,
                "available_date": today + timedelta(days=random.randint(-20, 70)),
                "amenities": "|".join(sorted(amenities)),
                "description": describe_property(area, ptype, bedrooms, rent, amenities),
                "latitude": round(lat + np.random.normal(0, 0.012), 6),
                "longitude": round(lng + np.random.normal(0, 0.018), 6),
            }
        )
    return pd.DataFrame(rows)


def describe_property(area: str, ptype: str, bedrooms: int, rent: int, amenities: set[str]) -> str:
    amenity_text = ", ".join(sorted(amenities))
    return (
        f"A well-presented {bedrooms}-bed {ptype} in {area} priced at £{rent} pcm. "
        f"Highlights include {amenity_text}. Suitable for applicants prioritising practical access, clear tenancy terms and responsive management."
    )


def generate_applicants(n: int) -> pd.DataFrame:
    first = ["Sarah", "John", "Aisha", "Daniel", "Emily", "Mohammed", "Priya", "James", "Olivia", "Thomas", "Grace", "Sam"]
    last = ["Mitchell", "Smith", "Patel", "Khan", "Jones", "Brown", "Wilson", "Taylor", "Ahmed", "Davies", "Clarke", "Reed"]
    rows = []
    today = date(2026, 8, 13)
    for idx in range(n):
        areas = random.sample(list(AREAS), k=random.choice([1, 2, 2, 3]))
        bedrooms = int(np.random.choice([0, 1, 2, 3, 4], p=[0.05, 0.28, 0.42, 0.21, 0.04]))
        target_rent = int(np.mean([AREA_RENT[a] for a in areas]) + bedrooms * 420 + np.random.normal(0, 240))
        budget_max = int(round(max(1100, target_rent + random.randint(-200, 350)) / 50) * 50)
        budget_min = int(max(800, budget_max - random.randint(250, 600)))
        prefs = set(random.sample(AMENITIES, k=random.randint(2, 5)))
        pets = random.random() < 0.18
        parking = random.random() < 0.2
        if pets:
            prefs.add("pet-friendly")
        if parking:
            prefs.add("parking")
        rows.append(
            {
                "applicant_id": f"A-{1000 + idx}",
                "name": f"{random.choice(first)} {random.choice(last)}",
                "age_band": random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
                "budget_min": budget_min,
                "budget_max": budget_max,
                "preferred_areas": "|".join(areas),
                "bedrooms_required": bedrooms,
                "property_types": "|".join(["studio"] if bedrooms == 0 else random.sample(["flat", "house", "maisonette"], k=random.choice([1, 1, 2]))),
                "move_in_date": today + timedelta(days=random.randint(5, 90)),
                "employment_type": random.choice(["permanent", "contractor", "self-employed", "student", "relocating"]),
                "pets": pets,
                "children": random.random() < 0.22,
                "furnished_preference": random.choice(["any", "furnished", "unfurnished"]),
                "parking_required": parking,
                "amenities_preferences": "|".join(sorted(prefs)),
            }
        )
    return pd.DataFrame(rows)


def inject_demo_entities(properties: pd.DataFrame, applicants: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sarah = {
        "applicant_id": "A-DEMO-SARAH",
        "name": "Sarah Mitchell",
        "age_band": "25-34",
        "budget_min": 2500,
        "budget_max": 2800,
        "preferred_areas": "Canary Wharf|Stratford",
        "bedrooms_required": 2,
        "property_types": "flat",
        "move_in_date": date(2026, 9, 15),
        "employment_type": "permanent",
        "pets": False,
        "children": False,
        "furnished_preference": "furnished",
        "parking_required": False,
        "amenities_preferences": "transport|balcony|concierge|gym",
    }
    demo_props = [
        {
            "property_id": "P-DEMO-01",
            "postcode": "E14 5AB",
            "city": "London",
            "area": "Canary Wharf",
            "property_type": "flat",
            "bedrooms": 2,
            "bathrooms": 2,
            "rent_pcm": 2675,
            "sale_price": "",
            "size_sqft": 780,
            "furnished": True,
            "parking": False,
            "garden": False,
            "balcony": True,
            "pets_allowed": False,
            "available_date": date(2026, 9, 1),
            "amenities": "transport|balcony|concierge|gym|river-view",
            "description": "Modern furnished two-bedroom apartment in Canary Wharf with balcony, concierge, gym and strong transport links.",
            "latitude": 51.5058,
            "longitude": -0.0222,
        },
        {
            "property_id": "P-DEMO-02",
            "postcode": "E20 1CD",
            "city": "London",
            "area": "Stratford",
            "property_type": "flat",
            "bedrooms": 2,
            "bathrooms": 1,
            "rent_pcm": 2525,
            "sale_price": "",
            "size_sqft": 735,
            "furnished": True,
            "parking": False,
            "garden": False,
            "balcony": True,
            "pets_allowed": True,
            "available_date": date(2026, 8, 28),
            "amenities": "transport|balcony|workspace|gym",
            "description": "Bright two-bedroom Stratford flat below Sarah's budget ceiling, close to Elizabeth line and local amenities.",
            "latitude": 51.5411,
            "longitude": -0.004,
        },
    ]
    applicants = pd.concat([pd.DataFrame([sarah]), applicants[applicants.applicant_id != "A-DEMO-SARAH"]], ignore_index=True)
    properties = pd.concat([pd.DataFrame(demo_props), properties[~properties.property_id.isin(["P-DEMO-01", "P-DEMO-02"])]], ignore_index=True)
    return properties, applicants


def generate_activity(properties: pd.DataFrame, applicants: pd.DataFrame):
    interactions = []
    viewings = []
    feedback = []
    conversations = []
    labels = []
    base_time = datetime(2026, 5, 1, 9, 0, 0)
    view_id = 0
    fb_id = 0
    conv_id = 0
    inter_id = 0
    for _, applicant in applicants.iterrows():
        candidate_props = sample_properties(properties, applicant, 18 if applicant.applicant_id == "A-DEMO-SARAH" else 10)
        converted = False
        if applicant.applicant_id == "A-DEMO-SARAH":
            inter_id, view_id, fb_id, conv_id = add_demo_sarah_activity(
                interactions,
                viewings,
                feedback,
                conversations,
                inter_id,
                view_id,
                fb_id,
                conv_id,
                applicant,
                properties,
            )
            converted = True
        for prop in candidate_props:
            affinity = preference_affinity(applicant, prop)
            if random.random() > min(0.95, 0.18 + affinity * 0.75):
                continue
            ts = base_time + timedelta(days=random.randint(0, 100), hours=random.randint(0, 8))
            inter_id = add_interaction(interactions, inter_id, applicant, prop, ts, "PROPERTY_VIEW", affinity)
            if random.random() < 0.18 + affinity * 0.55:
                inter_id = add_interaction(interactions, inter_id, applicant, prop, ts + timedelta(hours=2), "VIEWING_BOOKED", affinity)
                view_id += 1
                viewing_id = f"V-{view_id}"
                status = "completed" if random.random() > 0.12 else "cancelled"
                viewings.append({"viewing_id": viewing_id, "applicant_id": applicant.applicant_id, "property_id": prop.property_id, "scheduled_at": ts + timedelta(days=random.randint(1, 10)), "status": status})
                if status == "cancelled":
                    inter_id = add_interaction(interactions, inter_id, applicant, prop, ts + timedelta(days=1), "VIEWING_CANCELLED", -0.3)
                    continue
                rating = int(np.clip(round(2 + affinity * 3 + np.random.normal(0, 0.8)), 1, 5))
                objections = objections_for(applicant, prop, rating)
                fb_id += 1
                feedback.append(
                    {
                        "feedback_id": f"F-{fb_id}",
                        "viewing_id": viewing_id,
                        "applicant_id": applicant.applicant_id,
                        "property_id": prop.property_id,
                        "timestamp": ts + timedelta(days=2),
                        "rating": rating,
                        "sentiment": round((rating - 3) / 2, 2),
                        "objections": "|".join(objections),
                        "comments": feedback_comment(rating, objections, prop.area),
                    }
                )
                inter_id = add_interaction(interactions, inter_id, applicant, prop, ts + timedelta(days=2), "FEEDBACK", (rating - 3) / 2)
                if rating >= 4 and random.random() < 0.12 + affinity * 0.45:
                    inter_id = add_interaction(interactions, inter_id, applicant, prop, ts + timedelta(days=3), "APPLICATION_STARTED", affinity)
                    if random.random() < 0.55 + affinity * 0.25:
                        inter_id = add_interaction(interactions, inter_id, applicant, prop, ts + timedelta(days=4), "APPLICATION_SUBMITTED", affinity)
                        converted = True
        inter_id, conv_id = add_conversations(interactions, conversations, inter_id, conv_id, applicant, candidate_props[:4], converted)
        labels.append({"applicant_id": applicant.applicant_id, "converted": int(converted), "intent_label": label_intent(interactions, applicant.applicant_id)})
    ensure_minimums(interactions, viewings, feedback, conversations, properties, applicants, inter_id, view_id, fb_id, conv_id)
    return pd.DataFrame(interactions), pd.DataFrame(viewings), pd.DataFrame(feedback), pd.DataFrame(conversations), pd.DataFrame(labels)


def add_demo_sarah_activity(interactions, viewings, feedback, conversations, inter_id, view_id, fb_id, conv_id, applicant, properties):
    """Anchor the portfolio demo in explicit Sarah/P-DEMO evidence."""
    demo_props = {row.property_id: row for row in properties[properties.property_id.isin(["P-DEMO-01", "P-DEMO-02"])].itertuples(index=False)}
    p_demo = demo_props["P-DEMO-01"]
    p_alt = demo_props["P-DEMO-02"]
    base = datetime(2026, 8, 8, 10, 0, 0)

    inter_id = add_interaction(interactions, inter_id, applicant, p_demo, base, "PROPERTY_VIEW", 0.94)
    inter_id = add_interaction(interactions, inter_id, applicant, p_demo, base + timedelta(hours=2), "VIEWING_BOOKED", 0.94)
    view_id += 1
    viewing_id = f"V-{view_id}"
    viewings.append(
        {
            "viewing_id": viewing_id,
            "applicant_id": applicant.applicant_id,
            "property_id": p_demo.property_id,
            "scheduled_at": base + timedelta(days=1),
            "status": "completed",
        }
    )
    fb_id += 1
    feedback.append(
        {
            "feedback_id": f"F-{fb_id}",
            "viewing_id": viewing_id,
            "applicant_id": applicant.applicant_id,
            "property_id": p_demo.property_id,
            "timestamp": base + timedelta(days=1, hours=3),
            "rating": 5,
            "sentiment": 0.85,
            "objections": "PRICE|TERMS",
            "comments": "Sarah liked the Canary Wharf location, balcony, gym and concierge, but asked for clarity on tenancy terms and value versus budget.",
        }
    )
    inter_id = add_interaction(interactions, inter_id, applicant, p_demo, base + timedelta(days=1, hours=3), "FEEDBACK", 0.85)
    inter_id = add_interaction(interactions, inter_id, applicant, p_demo, base + timedelta(days=2), "APPLICATION_STARTED", 0.92)
    inter_id = add_interaction(interactions, inter_id, applicant, p_demo, base + timedelta(days=3), "APPLICATION_SUBMITTED", 0.9)

    inter_id = add_interaction(interactions, inter_id, applicant, p_alt, base + timedelta(days=4), "PROPERTY_VIEW", 0.87)
    inter_id = add_interaction(interactions, inter_id, applicant, p_alt, base + timedelta(days=4, hours=1), "MESSAGE_RECEIVED", 0.72)
    for subject, body in [
        (
            "Tenancy terms for Canary Wharf apartment",
            "Sarah asked whether P-DEMO-01 can support a September move-in and straightforward tenancy terms.",
        ),
        (
            "Budget sensitivity and value comparison",
            "Sarah compared P-DEMO-01 with similar two-bedroom properties under £2800 and asked the agent to explain value versus cheaper Stratford options.",
        ),
        (
            "Transport and commute evidence",
            "Sarah said Canary Wharf and Stratford are preferred because reliable transport links are important for her commute.",
        ),
    ]:
        conv_id += 1
        conversations.append(
            {
                "conversation_id": f"C-{conv_id}",
                "applicant_id": applicant.applicant_id,
                "property_id": p_demo.property_id,
                "timestamp": base + timedelta(days=conv_id % 4),
                "direction": "inbound",
                "channel": "email",
                "subject": subject,
                "body": body,
                "sentiment": 0.72,
            }
        )
    return inter_id, view_id, fb_id, conv_id


def sample_properties(properties: pd.DataFrame, applicant, n: int):
    areas = str(applicant.preferred_areas).split("|")
    subset = properties[(properties.area.isin(areas)) & (properties.bedrooms.between(max(int(applicant.bedrooms_required) - 1, 0), int(applicant.bedrooms_required) + 1))]
    if len(subset) < n:
        subset = properties.sample(min(len(properties), n * 3), random_state=SEED)
    sampled = list(subset.sample(min(len(subset), n), random_state=random.randint(1, 100000)).itertuples(index=False))
    if applicant.applicant_id == "A-DEMO-SARAH":
        demo = list(properties[properties.property_id.isin(["P-DEMO-01", "P-DEMO-02"])].itertuples(index=False))
        seen = {prop.property_id for prop in demo}
        sampled = demo + [prop for prop in sampled if prop.property_id not in seen]
    return sampled[:n]


def applicant_display_name(applicant) -> str:
    index = getattr(applicant, "index", [])
    if hasattr(applicant, "__getitem__") and not callable(index) and "name" in index:
        return str(applicant["name"])
    return str(getattr(applicant, "name", "Applicant"))


def preference_affinity(applicant, prop) -> float:
    areas = str(applicant.preferred_areas).split("|")
    amenities = set(str(applicant.amenities_preferences).split("|"))
    prop_amenities = set(str(prop.amenities).split("|"))
    score = 0.2
    score += 0.25 if prop.area in areas else 0
    score += 0.18 if prop.rent_pcm <= int(applicant.budget_max) else -0.25
    score += 0.16 if prop.bedrooms == int(applicant.bedrooms_required) else -0.08
    score += 0.12 if prop.property_type in str(applicant.property_types).split("|") else -0.04
    score += 0.14 * (len(amenities & prop_amenities) / max(len(amenities), 1))
    score += 0.05 if (not bool(applicant.pets) or bool(prop.pets_allowed)) else -0.1
    score += 0.04 if (not bool(applicant.parking_required) or bool(prop.parking)) else -0.12
    return float(np.clip(score, 0, 1))


def add_interaction(rows, idx, applicant, prop, ts, event_type, signal):
    idx += 1
    rows.append(
        {
            "interaction_id": f"I-{idx}",
            "applicant_id": applicant.applicant_id,
            "property_id": prop.property_id if prop is not None else "",
            "timestamp": ts,
            "channel": random.choice(["email", "phone", "portal", "sms", "whatsapp"]),
            "event_type": event_type,
            "message": message_for(event_type, applicant, prop),
            "sentiment": round(float(np.clip(signal, -1, 1)), 2),
            "intent": "HIGH" if signal > 0.65 else "MEDIUM" if signal > 0.35 else "LOW",
        }
    )
    return idx


def add_conversations(interactions, conversations, inter_id, conv_id, applicant, props, converted):
    for prop in props:
        for _ in range(random.randint(1, 3)):
            conv_id += 1
            concern = random.choice(["transport", "price", "tenancy terms", "move-in date", "furnishing"])
            body = f"{applicant_display_name(applicant)} asked about {concern} for {prop.property_id} in {prop.area}. Agent responded with factual property details and next steps."
            conversations.append(
                {
                    "conversation_id": f"C-{conv_id}",
                    "applicant_id": applicant.applicant_id,
                    "property_id": prop.property_id,
                    "timestamp": datetime(2026, 8, 1) + timedelta(days=random.randint(0, 12)),
                    "direction": random.choice(["inbound", "outbound"]),
                    "channel": random.choice(["email", "sms", "whatsapp"]),
                    "subject": f"Question about {prop.area} property",
                    "body": body,
                    "sentiment": 0.35 if converted else 0.05,
                }
            )
            inter_id = add_interaction(interactions, inter_id, applicant, prop, conversations[-1]["timestamp"], "MESSAGE_RECEIVED", conversations[-1]["sentiment"])
    return inter_id, conv_id


def objections_for(applicant, prop, rating: int) -> list[str]:
    objections = []
    if prop.rent_pcm > int(applicant.budget_max) * 0.97:
        objections.append("PRICE")
    if "transport" not in str(prop.amenities) and random.random() < 0.35:
        objections.append("TRANSPORT")
    if rating <= 2:
        objections.append(random.choice(["SIZE", "CONDITION", "AREA"]))
    if random.random() < 0.12:
        objections.append("TERMS")
    return objections


def feedback_comment(rating: int, objections: list[str], area: str) -> str:
    if rating >= 4:
        return f"Positive viewing feedback. Applicant liked the layout and {area} location, with questions about tenancy terms."
    if "PRICE" in objections:
        return "Applicant liked aspects of the property but raised price sensitivity versus budget."
    return "Applicant had reservations and asked for better matching alternatives."


def message_for(event_type: str, applicant, prop) -> str:
    if event_type == "PROPERTY_VIEW":
        return f"{applicant_display_name(applicant)} viewed {prop.property_id} in {prop.area}."
    if event_type == "VIEWING_BOOKED":
        return f"Viewing booked for {prop.property_id}."
    if event_type == "APPLICATION_STARTED":
        return f"Application started for {prop.property_id}."
    if event_type == "APPLICATION_SUBMITTED":
        return f"Application submitted for {prop.property_id}."
    return f"{event_type} recorded for {prop.property_id if prop is not None else 'general applicant record'}."


def label_intent(interactions, applicant_id: str) -> str:
    count = sum(1 for row in interactions if row["applicant_id"] == applicant_id)
    apps = sum(1 for row in interactions if row["applicant_id"] == applicant_id and row["event_type"].startswith("APPLICATION"))
    if apps >= 1 and count >= 8:
        return "VERY_HIGH"
    if count >= 10:
        return "HIGH"
    if count >= 5:
        return "MEDIUM"
    if count >= 2:
        return "LOW"
    return "DORMANT"


def ensure_minimums(interactions, viewings, feedback, conversations, properties, applicants, inter_id, view_id, fb_id, conv_id) -> None:
    sarah = applicants[applicants.applicant_id == "A-DEMO-SARAH"].iloc[0]
    demo = properties[properties.property_id == "P-DEMO-01"].iloc[0]
    while len(interactions) < 15000:
        inter_id = add_interaction(interactions, inter_id, applicants.sample(1, random_state=random.randint(1, 999999)).iloc[0], properties.sample(1, random_state=random.randint(1, 999999)).iloc[0], datetime(2026, 7, 1) + timedelta(days=random.randint(0, 40)), random.choice(EVENT_TYPES), random.uniform(-0.2, 0.6))
    while len(viewings) < 3000:
        view_id += 1
        app = applicants.sample(1, random_state=random.randint(1, 999999)).iloc[0]
        prop = properties.sample(1, random_state=random.randint(1, 999999)).iloc[0]
        viewings.append({"viewing_id": f"V-{view_id}", "applicant_id": app.applicant_id, "property_id": prop.property_id, "scheduled_at": datetime(2026, 7, 1) + timedelta(days=random.randint(0, 70)), "status": "completed"})
    while len(feedback) < 2000:
        view = viewings[len(feedback) % len(viewings)]
        fb_id += 1
        feedback.append({"feedback_id": f"F-{fb_id}", "viewing_id": view["viewing_id"], "applicant_id": view["applicant_id"], "property_id": view["property_id"], "timestamp": datetime(2026, 8, 1), "rating": 4, "sentiment": 0.5, "objections": "PRICE" if random.random() < 0.25 else "", "comments": "Synthetic feedback generated from applicant-property affinity."})
    while len(conversations) < 5000:
        conv_id += 1
        conversations.append({"conversation_id": f"C-{conv_id}", "applicant_id": sarah.applicant_id, "property_id": demo.property_id, "timestamp": datetime(2026, 8, 10), "direction": "inbound", "channel": "email", "subject": "Similar properties under budget", "body": "Sarah asked for similar two-bedroom properties under £2800 near Canary Wharf with strong transport links.", "sentiment": 0.7})


def write(out: Path, *frames: pd.DataFrame) -> None:
    names = ["properties", "applicants", "interactions", "viewings", "feedback", "conversations", "labels"]
    for name, frame in zip(names, frames, strict=True):
        frame.to_csv(out / f"{name}.csv", index=False)
    (out / "SYNTHETIC_DATA_NOTICE.txt").write_text("All applicant, property and interaction data is synthetic and generated solely for demonstration.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
