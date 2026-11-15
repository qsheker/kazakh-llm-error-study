#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "data/test/prompts_test.csv"
OUT_DIR = ROOT / "data/references"
ACCESS_DATE = "2026-11-15"


SOURCES = {
    "iupac_atom": ("IUPAC Gold Book: atom", "https://goldbook.iupac.org/terms/view/A00493", "the scientific meaning of atom"),
    "iupac_molecule": ("IUPAC Gold Book: molecule", "https://goldbook.iupac.org/terms/view/M04002", "the scientific meaning of molecule"),
    "noaa_pressure": ("NOAA JetStream: Air Pressure", "https://www.noaa.gov/jetstream/atmosphere/air-pressure", "air pressure, molecular density, and the decrease of pressure with height"),
    "openstax_heat": ("OpenStax Physics: Heat and Heat Transfer", "https://openstax.org/books/physics/pages/11-2-heat-specific-heat-and-heat-transfer", "conduction, convection, radiation, and insulating materials"),
    "usgs_weathering": ("USGS: Environmental Characteristics of Clays and Clay Mineral Deposits", "https://pubs.usgs.gov/info/clays/", "weathering, water, temperature, organisms, and soil-forming material"),
    "nasa_seasons": ("NASA Space Place: What Causes the Seasons", "https://spaceplace.nasa.gov/seasons/en/", "axial tilt, sunlight angle, and the distance misconception"),
    "nist_glossary": ("NIST Statistical Engineering Handbook Glossary", "https://www.itl.nist.gov/div898/handbook/glossary.htm", "sample, sample size, statistic, standard error, and related terms"),
    "nist_outliers": ("NIST Statistical Engineering Handbook: Detection of Outliers", "https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm", "how to identify and investigate unusual observations without deleting them automatically"),
    "eurostat_points": ("UNECE and Eurostat: Making Data Meaningful Part 1", "https://ec.europa.eu/eurostat/documents/64157/4374310/32-UNECE-making-data-meaningful-Part1-EN.pdf/82cf87d2-4bc9-431c-be96-2257cf77c810", "the distinction between percentage change and percentage-point change"),
    "loc_sources": ("Library of Congress: Getting Started with Primary Sources", "https://www.loc.gov/programs/teachers/getting-started-with-primary-sources/", "creator, context, purpose, audience, corroboration, and evidence-based historical inference"),
    "idea_democracy": ("International IDEA: Direct Democracy", "https://www.idea.int/publications/catalogue/direct-democracy-international-idea-handbook", "general mechanisms and limitations of direct-democratic decision making"),
    "unesco_mil": ("UNESCO: Global Standards for Media and Information Literacy Curricula", "https://www.unesco.org/sites/default/files/medias/files/2022/02/Global%20Standards%20for%20Media%20and%20Information%20Literacy%20Curricula%20Development%20Guidelines_EN.pdf", "source provenance, credibility, purpose, verification, and critical evaluation"),
    "python_names": ("Python documentation: Naming and binding", "https://docs.python.org/3/reference/executionmodel.html#naming-and-binding", "names, bindings, and changing program state"),
    "nist_hash": ("NIST SP 800-63B: Authentication and Lifecycle Management", "https://pages.nist.gov/800-63-4/sp800-63b.html", "salted password hashing and protected transmission"),
    "binary_search": ("NIST Dictionary of Algorithms and Data Structures: Binary Search", "https://xlinux.nist.gov/dads/HTML/binarySearch.html", "binary search on sorted data and repeated reduction of the search interval"),
    "ms_excel": ("Microsoft Support: SUMIF function", "https://support.microsoft.com/en-us/office/sumif-function-169b8c99-c05c-4483-a712-1697a653039b", "category-based spreadsheet totals and formula syntax"),
    "apple_trash": ("Apple Support: Delete files and folders on Mac", "https://support.apple.com/guide/mac-help/delete-files-and-folders-on-mac-mchlp1093/mac", "Trash, emptying Trash, and limits of ordinary deletion"),
    "egov": ("Electronic government of Kazakhstan", "https://egov.kz/cms/en", "official service discovery and use of the government portal"),
    "gov_hearings": ("Government of Kazakhstan: requirements for public hearings", "https://www.gov.kz/org/akk/documents/details/57153?lang=ru", "agenda publication, registration, speaking order, and official records"),
    "dot_access": ("US Department of Transportation: Traveling with a Disability", "https://www.transportation.gov/individuals/aviation-consumer-protection/traveling-disability", "checking carrier assistance and accessibility arrangements before travel"),
    "nara_research": ("US National Archives: Start Your Research", "https://www.archives.gov/research/start", "preparing a research topic and using archival catalogues and reference services"),
    "ada_events": ("ADA.gov: State and Local Governments", "https://www.ada.gov/topics/title-ii/", "effective communication and accessibility of public services and events"),
    "ready_weather": ("Ready.gov: Severe Weather", "https://www.ready.gov/severe-weather", "official alerts, household preparation, and communication planning"),
    "epa_hhw": ("US EPA: Household Hazardous Waste", "https://www.epa.gov/hw/household-hazardous-waste-hhw", "identifying household hazardous waste and checking local collection rules"),
    "epa_batteries": ("US EPA: Used Household Batteries", "https://www.epa.gov/recycle/used-household-batteries", "separating, protecting, and routing batteries to appropriate collection programs"),
    "cisa_wifi": ("CISA: Cybersecurity While Traveling", "https://niccs.cisa.gov/sites/default/files/documents/pdf/ncsam_cybersecuritywhiletraveling_508.pdf", "network-name verification and limits on sensitive activity over public Wi-Fi"),
    "cisa_phishing": ("CISA: Phishing Guidance", "https://www.cisa.gov/sites/default/files/2025-03/Phishing%20Guidance%20-%20Stopping%20the%20Attack%20Cycle%20at%20Phase%20One%20508.pdf", "phishing indicators, credential theft, and verification through trusted channels"),
    "ftc_shopping": ("US FTC: Online Shopping", "https://consumer.ftc.gov/articles/online-shopping", "seller checks, full cost, delivery, returns, records, and dispute escalation"),
    "ftc_resolution": ("US FTC: Solving Problems With a Business", "https://consumer.ftc.gov/articles/solving-problems-business-returns-refunds-and-other-resolutions", "preserving records, contacting the seller, and checking complaint routes and deadlines"),
}


CARD_DATA = {
    "E01": (["An atom is the smallest unit of an element that retains that element's chemical identity.", "A molecule contains two or more atoms bonded as one entity; water is H2O, while common oxygen gas is O2.", "A substance's properties depend on which atoms are present and how they are arranged."], ["Do not call every atom a molecule or describe a water molecule as a mixture of separate hydrogen and oxygen gases."], ["iupac_atom", "iupac_molecule"]),
    "E02": (["Air pressure is the force produced by moving air molecules colliding with surfaces.", "Higher altitude leaves less overlying air and lower molecular density, so pressure usually decreases.", "A daily-life example may use ears, sealed packages, or boiling, but it must preserve the cause-and-effect chain."], ["Do not claim pressure is zero on mountains or that altitude alone fixes an exact pressure regardless of weather."], ["noaa_pressure"]),
    "E03": (["Conductors transfer thermal energy readily; metals are common examples.", "Insulators slow heat transfer; wood, air, foam, and many plastics can serve as examples.", "The application must link material choice to the desired heat-transfer rate, not merely list objects."], ["Do not say an insulator prevents all heat transfer or that all metals behave identically."], ["openstax_heat"]),
    "E04": (["Weathering breaks or chemically changes rock at or near the surface.", "Water, temperature cycles, and organisms can contribute through physical and chemical processes.", "Soil develops over time from mineral material plus organic matter, water, air, and biological activity."], ["Do not present soil as instantly produced from rock or reduce all weathering to wind erosion."], ["usgs_weathering"]),
    "E05": (["A vacuum or low-conductivity layer reduces conduction and convection through the walls.", "Reflective surfaces can reduce radiative heat transfer.", "A tight lid limits air exchange, convection, and evaporation; a thermos slows heat flow in either direction."], ["Do not claim a thermos creates heat or keeps temperature unchanged forever."], ["openstax_heat"]),
    "E06": (["Earth's axial tilt, about 23 degrees, changes sunlight angle and day length through the orbit.", "The hemispheres experience opposite seasons at the same time.", "Earth's small annual distance variation is not the primary cause of ordinary seasons."], ["Do not attribute seasons mainly to Earth being nearer to or farther from the Sun."], ["nasa_seasons"]),
    "E07": (["The arithmetic mean is the sum divided by the number of observations.", "The median is the central ordered value, or the average of the two central values.", "A very large value pulls the mean more strongly than the median; the example must show both calculations."], ["Do not compute a median before sorting or imply that one measure is always preferable."], ["nist_glossary", "nist_outliers"]),
    "E08": (["A sample proportion varies randomly from trial to trial.", "With independent repeated trials, a larger sample usually makes the observed proportion more stable around the underlying probability.", "The coin example must compare proportions rather than guarantee an exact 50 percent outcome."], ["Do not claim that a larger sample removes randomness or bias automatically."], ["nist_glossary"]),
    "E09": (["A percentage-point difference subtracts two percentages directly.", "A percentage change divides the change by the starting value.", "For a rise from 20% to 25%, the difference is 5 percentage points and the relative increase is 25%."], ["Do not label a five-percentage-point increase as a five-percent increase in that example."], ["eurostat_points"]),
    "E10": (["Check variable definitions, units, time order, and axis scale before reading a trend.", "Compare successive points and the overall direction rather than relying on one interval.", "Investigate an outlier as possible error, random variation, or meaningful event; do not delete it automatically."], ["Do not infer causation from the line or hide a reversed, truncated, or nonuniform axis."], ["nist_outliers"]),
    "E11": (["Define the population and measure waiting time consistently from a stated start to end point.", "Sample several days and meal periods so one convenient interval does not stand for all conditions.", "Record time, interval, queue conditions, and waiting duration, then summarize center and spread with limitations."], ["Do not promise representativeness from one day or record identifiable student data without need."], ["nist_glossary"]),
    "E12": (["Correlation describes co-variation; it does not by itself establish that one variable caused the other.", "Alternative explanations include common causes, reverse direction, selection, and chance.", "A daily example must identify at least one plausible third variable."], ["Do not treat temporal order or a high correlation coefficient as sufficient proof of causation."], ["nist_glossary"]),
    "E13": (["Periodization divides a long historical sequence into analytical intervals.", "It helps organize change and continuity, but boundaries depend on the question, region, and evidence.", "Different historians may use different defensible boundaries for the same broad era."], ["Do not present period labels as natural universal facts or assume change happens everywhere on one date."], ["loc_sources"]),
    "E14": (["Industrial employment can attract migrants and increase urban population.", "Population growth can increase demand for housing, transport, water, sanitation, and public services.", "The chain must allow variation: industrialization can reshape existing cities or create new centers, with unequal effects."], ["Do not claim every industrial project produces identical urban growth or only positive outcomes."], ["loc_sources"]),
    "E15": (["Direct democracy lets eligible citizens decide specified questions themselves.", "Representative democracy delegates routine lawmaking or governance to elected representatives.", "A fair comparison must name participation mechanisms and one practical limitation of each."], ["Do not claim either form eliminates institutions, rules, minority rights, or implementation constraints."], ["idea_democracy"]),
    "E16": (["Identify the source, creator, date, context, intended audience, and purpose.", "Separate what the source directly shows from later inference.", "Compare the account with independent primary or secondary sources and explain contradictions."], ["Do not treat one source as complete, neutral, or self-authenticating."], ["loc_sources"]),
    "E17": (["Economic effects may include market access, travel costs, jobs, or land-value changes.", "Social effects may include access to services, mobility, noise, safety, or displacement.", "Environmental effects may include habitat fragmentation, runoff, emissions, or land disturbance; effects depend on route and mitigation."], ["Do not guarantee development, ignore trade-offs, or invent a local environmental assessment."], ["loc_sources"]),
    "E18": (["Historical explanations can combine long-term conditions, an immediate trigger, and human choices.", "Causes operate at different levels and may interact rather than form one simple chain.", "The response should distinguish contributing conditions from a trigger and avoid claiming inevitability."], ["Do not reduce a complex event to one person, one date, or one cause without evidence."], ["loc_sources"]),
    "E19": (["A thesis is a claim that the text asks the audience to accept.", "Evidence is relevant material used to support or test that claim.", "The example must include one contestable thesis and two genuinely different supporting items or reasons."], ["Do not present repetition of the thesis or popularity as evidence."], ["unesco_mil"]),
    "E20": (["Emotionally loaded wording can frame interpretation before the underlying facts are evaluated.", "The neutral and emotional headlines should refer to the same event while differing in evaluative language.", "Readers should inspect evidence, source, and context rather than infer truth from tone."], ["Do not claim emotional language always makes a statement false or that neutral wording guarantees accuracy."], ["unesco_mil"]),
    "E21": (["A news report primarily informs about an event; advertising primarily seeks a response such as purchase or support.", "Compare source disclosure, tone, evidence, omitted conditions, and calls to action.", "Readers should verify claims and distinguish independent evidence from testimonials or sponsored content."], ["Do not assume every news item is neutral or every advertisement is factually false."], ["unesco_mil"]),
    "E22": (["Trace the claim to its earliest available or primary source.", "Check author, publisher, date, context, and whether an image or quotation is reused misleadingly.", "Seek independent confirmation from sources that do not merely copy one another."], ["Do not use search-result rank, a verification badge, or share count as proof by itself."], ["unesco_mil"]),
    "E23": (["Preserve the same core scientific claim for both audiences.", "For children, define terms, use a concrete analogy, and limit secondary detail.", "For specialists, use precise terminology, methods, uncertainty, and evidence relevant to their expertise."], ["Do not change factual meaning, hide material uncertainty, or equate simplification with inaccuracy."], ["unesco_mil"]),
    "E24": (["Popularity measures reach or engagement, not evidential quality.", "Check the original source and compare the claim with independent credible evidence.", "Explain how repetition, coordinated sharing, or platform ranking can amplify unsupported content."], ["Do not claim that unpopular information is therefore true or that crowds never provide useful signals."], ["unesco_mil"]),
    "E25": (["A variable associates a name with a value or object used by a program.", "Assignment can create or update that association according to the language's rules.", "The everyday analogy must not imply that every language uses the same storage model."], ["Do not describe a variable name as the value itself or claim all programming variables have one permanent type."], ["python_names"]),
    "E26": (["Open applications and background processes compete for finite memory, CPU time, storage I/O, and other resources.", "Memory pressure can trigger compression or swapping, which is slower than direct RAM access.", "A diagnostic explanation should present these as likely causes, not a guaranteed diagnosis."], ["Do not claim that RAM and storage are the same or that closing any one program always solves the problem."], ["nist_glossary"]),
    "E27": (["Cryptographic hashing maps input to a fixed-size digest and is designed to resist practical reversal and collisions.", "Encryption transforms data with a key so authorized parties can decrypt it.", "Password storage should use a salted, costly password-hashing scheme; message confidentiality uses suitable encryption."], ["Do not describe ordinary fast hashing as sufficient password protection or claim encryption is irreversible."], ["nist_hash"]),
    "E28": (["Binary search requires a sorted sequence and compares the target with a middle element.", "Each comparison discards the half that cannot contain the target.", "The example must show interval boundaries shrinking until a match or empty interval."], ["Do not apply the procedure to unsorted data without preprocessing or claim it always finds a missing value."], ["binary_search"]),
    "E29": (["Use one row per transaction with date, category, description, and numeric amount in separate columns.", "Aggregate categories with SUMIF, a pivot table, or an equivalent formula based on explicit ranges.", "Check totals against the raw amount column and inspect blanks, text-formatted numbers, duplicates, and category spelling."], ["Do not hard-code summary totals or mix currencies without an explicit conversion rule."], ["ms_excel"]),
    "E30": (["Moving a file to Trash normally changes its location and leaves it recoverable until Trash is emptied.", "Backups or synchronized copies may persist after deletion from one device.", "Secure disposal depends on storage technology, encryption, account state, and the applicable platform procedure."], ["Do not promise that emptying Trash overwrites every physical copy or instruct destructive commands without verifying backups and target."], ["apple_trash"]),
    "P01": (["Identify the exact service before choosing a channel or office.", "Check required documents, eligibility, fee, appointment, and service status on an official government page.", "Share only necessary personal data through the verified channel and retain the application receipt or reference number."], ["Do not invent a universal document list, office address, fee, or processing time."], ["egov"]),
    "P02": (["Read the published topic, agenda, materials, date, format, and participation rules.", "Prepare a short evidence-based proposal linked to an agenda item.", "Verify registration and speaking requirements through the organizer's official notice."], ["Do not invent a deadline or imply that registration guarantees unlimited speaking time."], ["gov_hearings"]),
    "P03": (["Keep away from exposed wires, damaged poles, traffic, and other immediate hazards.", "Report the exact or approximate location, landmark, asset identifier, and observed condition through the responsible official channel.", "Record the request number and use it for follow-up; call emergency services only for an immediate danger."], ["Do not touch the equipment, attempt repair, or publish personal details unnecessarily."], ["egov"]),
    "P04": (["Follow the chair's speaking order and stated time limits.", "Address the proposal and evidence rather than a person's motives or identity.", "Ask clarifying questions, disclose relevant interests, and allow the official record to capture differing views."], ["Do not present harassment, threats, interruption, or personal attacks as acceptable participation."], ["gov_hearings"]),
    "P05": (["Confirm the exact certificate name and who may request it.", "Check required evidence, validity period, delivery method, and status only on the official portal or authority channel.", "Do not give credentials, codes, or unnecessary identity documents to an informal intermediary."], ["Do not invent one nationwide validity period or treat an unofficial messenger as the issuing authority."], ["egov"]),
    "P06": (["Use placeholders for affected address or area, start time, expected restoration, and responsible organization.", "State only the confirmed reason, if the official source provides one.", "Direct residents to the official update channel and include emergency guidance only when the authority supplies it."], ["Do not fabricate times, addresses, cause, compensation, or safety instructions."], ["egov"]),
    "P07": (["Check the ticket, station name, departure board, train number, time, and platform when displayed.", "Allow time for security, navigation, and platform changes.", "Ask identified station or carrier staff for assistance and recheck announcements."], ["Do not promise a fixed platform or boarding process across all stations."], ["dot_access"]),
    "P08": (["Contact the carrier through its official accessibility channel before travel when advance arrangement is useful or required.", "Describe the assistance needed for station access, boarding, seating, mobility equipment, and transfers.", "Record the confirmation and also plan for day-of-travel contact because procedures can change."], ["Do not guarantee availability, invent notice periods, or require disclosure beyond what the service needs."], ["dot_access"]),
    "P09": (["Record route, direction, stop, approximate time, vehicle identifier, and a neutral description of the item.", "Use the operator's official lost-property channel and retain the case number.", "Provide proof of ownership privately; avoid publishing serial numbers, addresses, or identity documents."], ["Do not contact a suspected finder aggressively or post excessive personal data publicly."], ["egov"]),
    "P10": (["Adapt speed to visibility, congestion, surface, and the most vulnerable users.", "Give an audible or visible warning early enough to avoid startling others, then pass with space only when safe.", "Keep to the designated side where marked and do not block the shared path."], ["Do not assert a universal speed limit or right-of-way rule without the local code and signs."], ["dot_access"]),
    "P11": (["Compare the ticket fare conditions with the operating carrier's current baggage page.", "Verify dimensions, weight, prohibited items, mobility aids, and special assistance for the exact itinerary and connections.", "Save the carrier's confirmation and recheck close to departure."], ["Do not invent baggage allowances, fees, medical-document rules, or universal notice periods."], ["dot_access"]),
    "P12": (["Use placeholders for affected route, stops, period, and source of the official change.", "State confirmed alternative stops or services only when supplied by the operator.", "Ask passengers to recheck the operator's official site or app before departure and allow extra time."], ["Do not speculate about the cause or invent a replacement route or restoration time."], ["dot_access"]),
    "P13": (["Define the research question, people, place, and date range before contacting the archive.", "Search the catalogue and note collection identifiers, access restrictions, registration, and appointment rules.", "Follow staff instructions for handling, supports, pencils, photography, and file order."], ["Do not assume every record is digitized, open, or available on demand."], ["nara_research"]),
    "P14": (["Check learning objectives, syllabus, dates, workload, prerequisites, cost, cancellation, and certificate conditions.", "Ask about physical, communication, and digital accessibility relevant to the participant.", "Read what personal data is collected, why, how long it is retained, and how to contact the organizer."], ["Do not invent accreditation, guarantee outcomes, or consent to unrelated data use by default."], ["ada_events"]),
    "P15": (["Stop using the equipment and prevent further risk without dismantling it.", "Tell staff what was observed, when, and under what normal use, distinguishing observation from speculation.", "Follow the venue's incident and replacement process and retain any reference number."], ["Do not attempt repair, hide damage, assign blame without evidence, or keep using unsafe equipment."], ["nara_research"]),
    "P16": (["Silence devices and move calls or conversations to the designated area.", "Use shared desks, power, books, and equipment carefully and leave space usable for the next person.", "Follow posted food, drink, reservation, and accessibility rules and ask staff about conflicts."], ["Do not present informal preferences as universal rules or confront other users aggressively."], ["nara_research"]),
    "P17": (["Ask which spoken and written languages the event uses.", "Ask whether live interpretation, captions, transcripts, hearing support, step-free access, or another accommodation is available.", "Confirm how and by when to request an accommodation, while avoiding assumptions about guaranteed provision."], ["Do not claim that automatic captions or informal translation meet every person's needs."], ["ada_events"]),
    "P18": (["Use placeholders for title, organizer, venue or platform, date, time, capacity, fee, and registration deadline.", "Direct readers to the official page for eligibility, accessibility, materials, cancellation, and data-use terms.", "Keep the notice descriptive and separate confirmed facts from optional preparation."], ["Do not invent availability, price, instructor credentials, or certificate status."], ["ada_events"]),
    "P19": (["Identify the waste type, label, condition, and quantity without opening or mixing containers.", "Check the local program's accepted materials, resident eligibility, packaging, appointment, and transport rules.", "Keep incompatible materials separate, secure containers upright, and follow label and authority instructions."], ["Do not give disposal instructions that override the product label or local hazardous-waste authority."], ["epa_hhw"]),
    "P20": (["Verify the alert and affected area through the official weather or emergency authority.", "Secure or bring in loose outdoor items only when it is safe, and stay away from windows and damaged lines.", "Charge communication devices and agree on contacts and a meeting or check-in plan."], ["Do not invent a local wind threshold, evacuation order, or all-clear time."], ["ready_weather"]),
    "P21": (["Keep people away from the wet or damaged area, especially near ceilings, lifts, wiring, and electrical equipment.", "Notify building management or the responsible emergency maintenance channel with location and observed severity.", "Do not touch electrical equipment or enter a flooded area; call emergency services for immediate danger."], ["Do not attempt plumbing or electrical repair without authority and competence."], ["ready_weather"]),
    "P22": (["Keep used batteries out of ordinary mixed recycling when the local program says so and route them to an accepted collection point.", "Protect exposed terminals and keep batteries from being crushed, punctured, heated, or mixed loose with metal objects.", "Check local rules because battery chemistry and collection programs differ."], ["Do not place damaged or swollen batteries in an ordinary collection box without specific local instructions."], ["epa_batteries"]),
    "P23": (["Find the issuing water utility, health authority, or local government notice and verify its authenticity.", "Confirm the exact affected area, start time, expected duration, permitted uses, and update channel.", "Distinguish a conservation restriction from a boil-water or do-not-use notice and follow the exact official wording."], ["Do not merge different notice types or invent health instructions and restoration times."], ["egov"]),
    "P24": (["Use placeholders for organizer, site, dates, hours, accepted materials, quantity limits, packaging, eligibility, and fees.", "Direct residents to the official notice for changes, hazardous exclusions, accessibility, and contact details.", "State only verified collection and transport instructions."], ["Do not invent accepted materials, hours, address, incentives, or disposal guarantees."], ["epa_hhw"]),
    "P25": (["Reach the service from a known official government domain or saved official application, not an unsolicited link.", "Use a private device or trusted connection where possible, protect credentials and one-time codes, and inspect the requested permissions.", "Sign out, close the session, save the official receipt, and remove downloaded personal files from shared devices."], ["Do not ask the user to share passwords, electronic-signature keys, or one-time codes with a helper."], ["egov", "cisa_phishing"]),
    "P26": (["Verify the seller identity and contact information across the site and independent sources.", "Check the complete price, currency, recurring charges, delivery terms, return conditions, warranty, and privacy terms before paying.", "Save the product description, order confirmation, receipt, and seller promises."], ["Do not treat reviews, a padlock icon, or a low price alone as proof of legitimacy."], ["ftc_shopping"]),
    "P27": (["Keep the original receipt and make a copy or photo that clearly shows the disputed line.", "Contact the seller through its official channel with the transaction details, specific error, and requested correction.", "Record dates and responses, then check the applicable official consumer-complaint route and payment-dispute terms if unresolved."], ["Do not alter the receipt, threaten staff, or publish payment and identity details."], ["ftc_resolution"]),
    "P28": (["Confirm the exact network name and login process with the venue before connecting.", "Avoid banking, payment, identity, and other sensitive transactions; prefer a trusted mobile connection.", "Disable file sharing and automatic connection, keep software current, and forget the network after use."], ["Do not claim HTTPS or a VPN makes an untrusted device or fraudulent site safe in every respect."], ["cisa_wifi"]),
    "P29": (["Check the receipt or order record, item condition, packaging requirements, deadline, exceptions, and seller's current official policy.", "Distinguish statutory rights, warranty claims, and a seller's voluntary return policy according to the applicable jurisdiction.", "Keep originals, submit the request promptly, and retain written confirmation."], ["Do not invent a universal return period or promise a refund regardless of condition and local law."], ["ftc_resolution"]),
    "P30": (["Use placeholders for organizer, venue or platform, date, time, capacity, registration deadline, accessibility, and contact channel.", "Tell participants to verify the official registration domain, organizer identity, privacy notice, and what personal data the form requests.", "Keep the announcement neutral and provide no unverified security promise or attendance benefit."], ["Do not invent event logistics, speakers, certificates, or request passwords and one-time codes."], ["cisa_phishing"]),
}


def source_lines(keys: list[str]) -> list[str]:
    lines = []
    for key in keys:
        title, url, support = SOURCES[key]
        lines.append(f"- {title}. {url} Accessed {ACCESS_DATE}. Supports: {support}.")
    return lines


def main() -> None:
    rows = list(csv.DictReader(PROMPTS.open(encoding="utf-8")))
    expected = {row["prompt_id"] for row in rows}
    if set(CARD_DATA) != expected:
        raise SystemExit(f"card mapping mismatch: missing={sorted(expected - set(CARD_DATA))}, extra={sorted(set(CARD_DATA) - expected)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for row in rows:
        prompt_id = row["prompt_id"]
        anchors, prohibited, sources = CARD_DATA[prompt_id]
        if row["task_type"] == "educational":
            variants = [
                "Examples and wording may differ if the same factual and causal relationships remain explicit.",
                "A concise answer may omit secondary detail, but it must preserve every prompt requirement and avoid false certainty.",
            ]
            label = "REFERENCE"
            generic_prohibited = "Do not invent quotations, named studies, laws, measurements, or local facts that the prompt does not supply."
        else:
            variants = [
                "The guidance may be localized only after checking the responsible authority or operator's current official channel.",
                "A neutral template may use clearly marked placeholders where the prompt intentionally withholds local details.",
            ]
            label = "CONSTRAINT"
            generic_prohibited = "Do not invent addresses, times, fees, deadlines, eligibility rules, contact details, or requests for unnecessary personal data."

        content = [
            f"# {label} CARD — {prompt_id}",
            "",
            "- Status: READY_FOR_THREE_PERSON_REVIEW",
            f"- Task type: {row['task_type']}",
            f"- Domain: {row['domain']}",
            f"- Task form: {row['task_form']}",
            "",
            "## Prompt",
            "",
            row["prompt_text"],
            "",
            "## Required content or factual anchors",
            "",
            *[f"- {item}" for item in anchors],
            "",
            "## Acceptable variants and exemptions",
            "",
            *[f"- {item}" for item in variants],
            "",
            "## Unsupported or prohibited claims",
            "",
            *[f"- {item}" for item in prohibited],
            f"- {generic_prohibited}",
            "",
            "## Sources",
            "",
            *source_lines(sources),
            "",
            "## Human review record",
            "",
            "- Reviewer decisions are stored separately in `protocol/signoffs/`; this card is not a team approval by itself.",
            "- Reviewers must verify the prompt, anchors, prohibited claims, and source support before signing the bundle hash.",
            "",
        ]
        (OUT_DIR / f"{prompt_id}.md").write_text("\n".join(content), encoding="utf-8")

    print(f"wrote={len(rows)} cards")


if __name__ == "__main__":
    main()
