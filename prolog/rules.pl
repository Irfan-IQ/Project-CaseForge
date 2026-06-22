guilty(Defendant) :-
    has_opportunity(Defendant),
    has_motive(Defendant),
    \+ has_alibi(Defendant).

contradiction(Witness) :-
    location_at(Witness, Time, Place1),
    location_at(Witness, Time, Place2),
    Place1 \= Place2.

verdict(Defendant, guilty) :- guilty(Defendant).
verdict(Defendant, not_guilty) :- \+ guilty(Defendant).
