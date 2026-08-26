# Planner authority mapping

The backend planner input is assembled from two independent authorities. `Destination`
owns identity, coordinates, municipality, region, translations, category, editorial
priority, activity, and publication state. `DestinationPlannerProfile` owns structured
operational planning data. The adapter never treats existence, review, or verification
of a planner profile as permission to publish a destination.

When no profile exists, `profile_state` is `missing` and every operational field is
`null`. The adapter does not copy the deterministic JavaScript defaults into authoritative
data. When a profile exists, its `unverified`, `reviewed`, or `verified` state is preserved
without changing any values or implying publication.

`planner_priority` is an operational ranking signal and is distinct from Destination's
`editorial_priority_order`. `meal_suitability` and `rest_suitability` describe suitability
of the place for those stops; the current frontend inserts meal and rest time from pace
and continuous-activity heuristics, so these scores do not replace scheduling rules.

`opening_hours` is emitted as the stored, recursively key-sorted JSON object with its
timezone. The current frontend reference only reads a single `opening_time` and
`closing_time` pair and treats absent or invalid values as unknown. A future planner
engine must interpret the governed backend structure explicitly and must preserve an
unknown classification when no usable window exists.

Road access, surface, condition, and access status are emitted verbatim. The frontend's
slug-specific road factors remain fallback heuristics; they are not imported as verified
facts. Canonical coordinates always come from Destination, never from the profile or the
frontend lookup tables.
