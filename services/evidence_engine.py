def extract_prolog_facts(evidence_list: list[dict], witnesses: list[dict]) -> list[str]:
    facts = []

    for e in evidence_list:
        fact = e.get('prolog_fact', '').strip()
        if fact and not fact.endswith('.'):
            fact += '.'
        if fact:
            facts.append(fact)

    for w in witnesses:
        for fact in w.get('prolog_facts', []):
            fact = fact.strip()
            if fact and not fact.endswith('.'):
                fact += '.'
            if fact:
                facts.append(fact)

    return facts
