:- consult('prolog/rules.pl').
:- consult('prolog/evidence.pl').

run_verdict(Defendant, Verdict) :-
    verdict(Defendant, Verdict).
