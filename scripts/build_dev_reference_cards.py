#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "data/dev/prompts_dev.csv"
OUT_DIR = ROOT / "data/dev/references"
ACCESS_DATE = "2026-11-15"

SOURCES = {
    "usgs_water": ("USGS: The Water Cycle", "https://www.usgs.gov/special-topics/water-science-school/science/water-cycle"),
    "nps_photo": ("US National Park Service: Photosynthesis", "https://www.nps.gov/articles/000/photosynthesis.htm"),
    "openstax_fraction": ("OpenStax Prealgebra 2e: Fractions", "https://openstax.org/books/prealgebra-2e/pages/4-introduction-to-fractions"),
    "openstax_friction": ("OpenStax Physics: Friction", "https://openstax.org/books/physics/pages/5-1-friction"),
    "noaa_food": ("NOAA: Aquatic food webs", "https://www.noaa.gov/education/resource-collections/marine-life/aquatic-food-webs"),
    "nasa_rotation": ("NASA Space Place: All About Earth", "https://spaceplace.nasa.gov/all-about-earth/en/"),
    "loc_sources": ("Library of Congress: Getting Started with Primary Sources", "https://www.loc.gov/programs/teachers/getting-started-with-primary-sources/"),
    "unesco_mil": ("UNESCO: Media and Information Literacy", "https://www.unesco.org/en/media-information-literacy"),
    "nist_algorithm": ("NIST Dictionary of Algorithms and Data Structures", "https://xlinux.nist.gov/dads/"),
    "census_graphs": ("US Census Bureau: Types of Graphs", "https://www.census.gov/programs-surveys/sis/resources/maps/graphs.html"),
    "ala_library": ("American Library Association: Using Libraries", "https://www.ala.org/tools/libfactsheets/alalibraryfactsheet06"),
    "dot_transit": ("US Department of Transportation: Public Transportation", "https://www.transportation.gov/briefing-room/public-transportation"),
    "epa_recycle": ("US EPA: How Do I Recycle Common Recyclables", "https://www.epa.gov/recycle/how-do-i-recycle-common-recyclables"),
    "smithsonian_visit": ("Smithsonian: Visitor Guidelines", "https://www.si.edu/visit/tips"),
    "nps_leave": ("US National Park Service: Leave No Trace Seven Principles", "https://www.nps.gov/articles/leave-no-trace-seven-principles.htm"),
    "fema_cleanup": ("FEMA: Volunteering and Cleanup", "https://www.ready.gov/get-involved"),
    "ftc_privacy": ("US FTC: Protecting Your Personal Information", "https://consumer.ftc.gov/articles/protecting-your-personal-information-hackers-scammers"),
    "gov_meetings": ("Government of Kazakhstan: public hearings requirements", "https://www.gov.kz/org/akk/documents/details/57153?lang=ru"),
    "energy_saver": ("US Department of Energy: Reducing Electricity Use and Costs", "https://www.energy.gov/energysaver/reducing-electricity-use-and-costs"),
    "ada_access": ("ADA.gov: State and Local Governments", "https://www.ada.gov/topics/title-ii/"),
}

CARD_DATA = {
    "P01": (["Evaporation moves liquid water into the atmosphere as water vapor.", "Condensation forms clouds, and precipitation returns water to Earth's surface.", "The daily example must connect heating, evaporation or condensation, and later water return."], ["Do not describe clouds as containers filled directly from seas or claim all evaporated water immediately becomes rain."], "usgs_water"),
    "P02": (["Plants use light energy to convert water and carbon dioxide into sugars and release oxygen.", "Water enters through roots and carbon dioxide enters mainly through leaf openings.", "The example must explain the roles of light, water, and air rather than merely list them."], ["Do not say plants obtain their food directly from soil or that sunlight is a material absorbed as food."], "nps_photo"),
    "P03": (["The denominator is the number of equal parts in one whole; the numerator is the number of those parts considered.", "Fractions are comparable only with attention to the same whole.", "The example must divide one whole into equal parts and justify which fraction is larger."], ["Do not use unequal pieces as denominator parts or compare fractions by numerator alone."], "openstax_fraction"),
    "P04": (["Friction opposes relative motion or attempted motion between contacting surfaces.", "Useful examples may include walking, gripping, or braking.", "A hindering example must explain energy loss, wear, or resistance to movement."], ["Do not claim friction always stops motion or is always harmful."], "openstax_friction"),
    "P05": (["A food chain shows transfer of matter and energy from producers to consumers.", "The example must begin with a plant and use plausible feeding relationships.", "Reducing one link can change food availability and populations elsewhere in the chain."], ["Do not imply that every ecosystem has one isolated linear chain or that energy cycles back unchanged."], "noaa_food"),
    "P06": (["Day and night result from Earth rotating on its axis roughly once per day.", "The side facing the Sun is illuminated while the opposite side is in darkness.", "In the lamp-and-ball demonstration, the lamp stays fixed while the ball rotates."], ["Do not attribute ordinary day and night to Earth orbiting the Sun or to the Sun switching off."], "nasa_rotation"),
    "P07": (["A primary source was created during or by participants in the period studied; a secondary source analyzes evidence later.", "An old letter can be primary evidence, while a later history book is usually secondary.", "Comparison helps reveal context, perspective, omissions, and contradictions."], ["Do not treat every old object as automatically reliable or every later source as inferior."], "loc_sources"),
    "P08": (["A fact is a claim that can be checked against evidence; an opinion expresses a judgment or preference.", "The response must create two school-life examples and classify each with a reason.", "Some sentences mix checkable claims with evaluative language and should be separated when necessary."], ["Do not classify a claim as fact merely because many people believe it."], "unesco_mil"),
    "P09": (["An algorithm is a finite, ordered set of unambiguous steps for a task.", "The bookshelf example must give a repeatable ordering rule and a stopping condition.", "Changing step order or ignoring a condition can change the result."], ["Do not describe any vague suggestion or infinite loop as a complete algorithm."], "nist_algorithm"),
    "P10": (["A bar chart compares magnitudes across categories with separated bars.", "A line graph commonly shows change across an ordered sequence such as time.", "Each daily-life example must match the information structure and identify axes or categories."], ["Do not imply that a line between unrelated categories proves continuity or causation."], "census_graphs"),
    "P11": (["Explain how to search the catalogue, signs, shelves, or ask library staff.", "Tell the visitor to verify membership, borrowing, access, and local-use rules with that library.", "Use neutral placeholders instead of invented local details."], ["Do not invent a universal card requirement, fee, opening time, or loan period."], "ala_library"),
    "P12": (["Check route, direction, stop, and current service information before travel.", "Wait in the designated safe area, allow passengers to exit, and prepare for the intended stop.", "The prompt forbids a specific fare or schedule."], ["Do not invent a fare, timetable, universal boarding rule, or guaranteed accessibility feature."], "dot_transit"),
    "P13": (["Keep paper and plastic separate, reasonably clean and dry where the local program requires it.", "Check accepted materials, labels, caps, bags, and collection method with the local operator.", "Reduce and reuse remain valid before recycling."], ["Do not claim every numbered plastic is accepted or prescribe one universal preparation rule."], "epa_recycle"),
    "P14": (["Protect exhibits by following barriers, handling, food, and bag rules.", "Avoid blocking views or disturbing other visitors.", "Check the museum's current photography, flash, tripod, accessibility, and ticket rules before visiting."], ["Do not claim photography is always allowed or always prohibited."], "smithsonian_visit"),
    "P15": (["Keep shared areas clean, dispose of waste correctly, and leave natural objects and wildlife undisturbed.", "Respect noise, paths, other visitors, and posted restrictions.", "Plan for weather and site-specific safety without inventing local rules."], ["Do not encourage feeding wildlife, damaging plants, or treating a public space as exclusively reserved."], "nps_leave"),
    "P16": (["Use placeholders for the organizer's confirmed place, time, tools, clothing, and safety briefing.", "Assign tasks according to ability and separate hazardous findings for trained personnel.", "The prompt forbids invented address and time."], ["Do not ask volunteers to handle sharps, chemicals, wiring, or heavy hazards without competent supervision."], "fema_cleanup"),
    "P17": (["Contact staff through the library's official channel and give the approximate place, time, and neutral item description.", "Provide distinguishing details privately only when needed to establish ownership.", "Avoid publishing identity documents, passwords, financial data, or excessive contact details."], ["Do not post full serial numbers or sensitive personal data publicly."], "ftc_privacy"),
    "P18": (["Prepare one concise proposal with the problem, evidence, affected users, and a feasible next step.", "Listen to other positions, ask clarifying questions, and follow the meeting's speaking order.", "Confirm the recorded decision, responsible party, and next follow-up channel."], ["Do not present interruption, personal attacks, or an unrecorded promise as an official outcome."], "gov_meetings"),
    "P19": (["Turn off unnecessary lights and devices and use energy-saving settings where suitable.", "Manage heating, cooling, laundry, and standby loads through ordinary safe use.", "The prompt explicitly forbids electrical repair advice."], ["Do not instruct the reader to open, rewire, or repair electrical equipment."], "energy_saver"),
    "P20": (["Check the organizer's current official page for hours, tickets, location, and changes.", "Ask specifically about step-free routes, entrances, seating, toilets, communication access, and assistance relevant to the visitor.", "Use placeholders and direct questions rather than inventing venue facts."], ["Do not guarantee access, invent a schedule, or assume one accommodation suits everyone."], "ada_access"),
}


def main() -> None:
    with PROMPTS.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = {row["prompt_id"] for row in rows}
    if set(CARD_DATA) != expected:
        raise SystemExit(f"dev card mapping mismatch: missing={sorted(expected - set(CARD_DATA))}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for row in rows:
        anchors, prohibited, source_key = CARD_DATA[row["prompt_id"]]
        source_title, source_url = SOURCES[source_key]
        card_kind = "REFERENCE" if row["task_type"] == "edu" else "CONSTRAINT"
        lines = [
            f"# DEV {card_kind} CARD — {row['prompt_id']}",
            "",
            "- Status: CALIBRATION_ONLY_NOT_FOR_FINAL_ANALYSIS",
            f"- Task type: {row['task_type']}",
            "",
            "## Prompt",
            "",
            row["prompt_text"],
            "",
            "## Required content or factual anchors",
            "",
            *[f"- {item}" for item in anchors],
            "",
            "## Unsupported or prohibited claims",
            "",
            *[f"- {item}" for item in prohibited],
            "- Do not invent local addresses, prices, schedules, rules, or named evidence not supplied by the prompt.",
            "",
            "## Source",
            "",
            f"- {source_title}. {source_url} Accessed {ACCESS_DATE}.",
            "",
            "## Use limitation",
            "",
            "- This card is only for rater training and qualification on dev responses; it is excluded from confirmatory results.",
            "",
        ]
        (OUT_DIR / f"{row['prompt_id']}.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote={len(rows)} dev calibration cards")


if __name__ == "__main__":
    main()
