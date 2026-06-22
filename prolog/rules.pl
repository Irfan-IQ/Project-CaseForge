% ---------------------------------
% Derived Legal Concepts
% ---------------------------------

has_opportunity(Defendant) :-
    saw_defendant_near_laundry(_, Defendant).

has_opportunity(Defendant) :-
    noted_unusual_defendant_presence(
        Defendant,
        _
    ).

has_motive(Defendant) :-
    defendant_acted_shifty(Defendant).

has_motive(Defendant) :-
    forensic_match(
        _,
        _,
        _
    ),
    defendant_acted_shifty(Defendant).

has_alibi(Defendant) :-
    valid_alibi(Defendant).


% ---------------------------------
% Witness Contradictions
% ---------------------------------

contradiction(Witness) :-
    location_at(Witness, Time, Place1),
    location_at(Witness, Time, Place2),
    Place1 \= Place2.


% ---------------------------------
% Verdict Logic
% ---------------------------------

guilty(Defendant) :-
    has_opportunity(Defendant),
    has_motive(Defendant),
    \+ has_alibi(Defendant).

not_guilty(Defendant) :-
    has_alibi(Defendant).

insufficient_evidence(Defendant) :-
    \+ has_opportunity(Defendant),
    \+ has_motive(Defendant).


% ---------------------------------
% Final Verdict
% ---------------------------------

verdict(Defendant, guilty) :-
    guilty(Defendant).

verdict(Defendant, not_guilty) :-
    not_guilty(Defendant).

verdict(Defendant, insufficient_evidence) :-
    insufficient_evidence(Defendant).
