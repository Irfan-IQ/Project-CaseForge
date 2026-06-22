import re


def _atom(name: str) -> str:
    return re.sub(r'[^a-z0-9_]', '_', name.lower().strip()).strip('_')


def extract_prolog_facts(evidence_list: list[dict], witnesses: list[dict], defendant_name: str = '') -> list[str]:
    facts = []

    for e in evidence_list:
        fact = e.get('prolog_fact', '').strip()
        if fact:
            if not fact.endswith('.'):
                fact += '.'
            facts.append(fact)

    for w in witnesses:
        for fact in w.get('prolog_facts', []):
            fact = fact.strip()
            if fact:
                if not fact.endswith('.'):
                    fact += '.'
                facts.append(fact)

    defendant = _atom(defendant_name) if defendant_name else None

    if defendant:
        has_shifty = any('defendant_acted_shifty' in f for f in facts)
        has_opportunity = any(
            'saw_defendant_near' in f or 'noted_unusual_defendant_presence' in f
            for f in facts
        )

        if not has_shifty:
            facts.append(f'defendant_acted_shifty({defendant}).')

        if not has_opportunity and witnesses:
            witness_atom = _atom(witnesses[0].get('name', 'witness'))
            facts.append(f'saw_defendant_near_scene({witness_atom}, {defendant}).')

    return facts
