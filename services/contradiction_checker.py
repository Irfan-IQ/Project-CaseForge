from pyswip import Prolog


def run_verdict(case_facts: list[str], defendant: str = 'defendant') -> dict:
    prolog = Prolog()
    prolog.consult('prolog/rules.pl')

    with open('prolog/evidence.pl', 'w') as f:
        f.write('\n'.join(case_facts) + '\n')

    prolog.consult('prolog/evidence.pl')

    contradictions = list(prolog.query('contradiction(X)'))
    verdicts = list(prolog.query(f'verdict({defendant}, V)'))

    return {
        'contradictions': [str(c['X']) for c in contradictions],
        'verdict': str(verdicts[0]['V']) if verdicts else 'undecided',
    }
