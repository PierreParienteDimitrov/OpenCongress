"""
Custom search filter for Congress members.

Combines three strategies:
1. Exact substring matching on name fields (icontains)
2. Trigram similarity for typo-tolerant name matching (pg_trgm)
3. State name/abbreviation resolution with fuzzy matching

All three are OR'd together so any match surfaces results.
"""

from difflib import SequenceMatcher

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from rest_framework.filters import SearchFilter

from .constants import STATE_ABBREVS

# Pre-compute set of valid uppercase codes for fast abbreviation lookup
_VALID_CODES = {code.upper() for code in STATE_ABBREVS.values()}

# Minimum trigram similarity score for fuzzy name matching
_TRIGRAM_THRESHOLD = 0.15

# Minimum similarity ratio for fuzzy state name matching
_STATE_FUZZY_THRESHOLD = 0.7


def _fuzzy_state_match(query: str, state_name: str) -> bool:
    """Check if query fuzzy-matches a state name.

    Uses both full-string and word-level matching to handle typos
    in multi-word states (e.g. "njew york" → "new york").
    """
    # Full string match
    if SequenceMatcher(None, query, state_name).ratio() >= _STATE_FUZZY_THRESHOLD:
        return True

    # Word-level match: check if each query word matches a state word
    query_words = query.split()
    state_words = state_name.split()
    if not query_words:
        return False

    matched = 0
    for qw in query_words:
        for sw in state_words:
            if SequenceMatcher(None, qw, sw).ratio() >= _STATE_FUZZY_THRESHOLD:
                matched += 1
                break

    # Require at least half the query words to match state words,
    # and at least one word must match
    return matched >= 1 and matched / len(query_words) >= 0.5


def _resolve_state_codes(term: str) -> set[str]:
    """Resolve a search term to matching state codes.

    Matches on:
    - Full or partial state name (e.g. "new york", "new", "calif")
    - Fuzzy state name matching (e.g. "njew york" → NY, "califronia" → CA)
    - 2-letter abbreviation (e.g. "ny", "CA")
    """
    term_lower = term.lower()
    codes: set[str] = set()

    # Exact/partial match against state names
    for state_name, code in STATE_ABBREVS.items():
        if term_lower in state_name or state_name.startswith(term_lower):
            codes.add(code.upper())

    # Fuzzy match against state names
    # Catches typos like "njew york" → "new york", "califronia" → "california"
    if not codes:
        for state_name, code in STATE_ABBREVS.items():
            if _fuzzy_state_match(term_lower, state_name):
                codes.add(code.upper())

    # Direct abbreviation match (e.g. "ny" → "NY")
    term_upper = term.upper()
    if len(term_upper) == 2 and term_upper in _VALID_CODES:
        codes.add(term_upper)

    return codes


class MemberSearchFilter(SearchFilter):
    """Search filter with fuzzy matching via pg_trgm and state name resolution."""

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param, "").strip()
        if not search_term:
            return queryset

        # 1. Exact substring match on full_name
        #    (first_name/last_name are not populated in current data)
        q = Q(full_name__icontains=search_term)

        # 2. State name/abbreviation resolution
        state_codes = _resolve_state_codes(search_term)
        if state_codes:
            q |= Q(state__in=state_codes)

        # 3. Trigram similarity for typo-tolerant name matching
        queryset = queryset.annotate(
            search_similarity=TrigramSimilarity("full_name", search_term),
        )
        q |= Q(search_similarity__gte=_TRIGRAM_THRESHOLD)

        return queryset.filter(q)
