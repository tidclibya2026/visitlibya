const ACCESS_PROFILES = Object.freeze({
  tripoli: Object.freeze({
    accessClass: "standard",
    roadFactor: 1,
    requires4x4: false,
    requiresGuide: false,
  }),

  benghazi: Object.freeze({
    accessClass: "standard",
    roadFactor: 1,
    requires4x4: false,
    requiresGuide: false,
  }),

  sabratha: Object.freeze({
    accessClass: "standard",
    roadFactor: 1,
    requires4x4: false,
    requiresGuide: false,
  }),

  "leptis-magna": Object.freeze({
    accessClass: "standard",
    roadFactor: 1,
    requires4x4: false,
    requiresGuide: false,
  }),

  "villa-sileen": Object.freeze({
    accessClass: "standard",
    roadFactor: 1.05,
    requires4x4: false,
    requiresGuide: false,
  }),

  "green-mountain": Object.freeze({
    accessClass: "regional",
    roadFactor: 1.15,
    requires4x4: false,
    requiresGuide: false,
  }),

  "bomba-bay": Object.freeze({
    accessClass: "regional",
    roadFactor: 1.2,
    requires4x4: false,
    requiresGuide: false,
  }),

  nafusa: Object.freeze({
    accessClass: "regional",
    roadFactor: 1.2,
    requires4x4: false,
    requiresGuide: false,
  }),

  ghadames: Object.freeze({
    accessClass: "long-distance",
    roadFactor: 1.25,
    requires4x4: false,
    requiresGuide: false,
  }),

  awjila: Object.freeze({
    accessClass: "remote",
    roadFactor: 1.35,
    requires4x4: false,
    requiresGuide: false,
  }),

  desert: Object.freeze({
    accessClass: "desert",
    roadFactor: 1.65,
    requires4x4: true,
    requiresGuide: true,
  }),

  acacus: Object.freeze({
    accessClass: "desert-expedition",
    roadFactor: 1.9,
    requires4x4: true,
    requiresGuide: true,
  }),
});


const UNKNOWN_PROFILE = Object.freeze({
  accessClass: "unknown",
  roadFactor: 1,
  requires4x4: false,
  requiresGuide: false,
});


function normalize(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase();
}


export function destinationAccessProfile(
  destination,
) {
  const roadAccess = normalize(destination?.planner_road_access);
  const roadCondition = normalize(destination?.planner_road_condition);
  if (roadAccess && roadAccess !== "unknown") {
    const requires4x4 = roadAccess === "four_wheel_drive";
    const requiresGuide = roadAccess === "guided_only";
    const difficult = roadCondition === "difficult" || roadCondition === "very_difficult";
    return {
      accessClass: requiresGuide ? "desert-expedition" : requires4x4 ? "desert" : difficult ? "remote" : "standard",
      roadFactor: requiresGuide ? 1.9 : requires4x4 ? 1.65 : difficult ? 1.35 : 1,
      requires4x4,
      requiresGuide,
    };
  }
  const slug =
    normalize(destination?.slug);

  return (
    ACCESS_PROFILES[slug] ??
    UNKNOWN_PROFILE
  );
}


export function adjustedRoadTravelMinutes(
  baseMinutes,
  destination,
) {
  const minutes =
    Number(baseMinutes);

  if (
    !Number.isFinite(minutes) ||
    minutes < 0
  ) {
    return null;
  }

  const profile =
    destinationAccessProfile(
      destination,
    );

  return (
    minutes *
    profile.roadFactor
  );
}


export function roadFeasibilityPenalty(
  destination,
) {
  const profile =
    destinationAccessProfile(
      destination,
    );

  switch (profile.accessClass) {
    case "standard":
      return 0;

    case "regional":
      return 3;

    case "long-distance":
      return 5;

    case "remote":
      return 10;

    case "desert":
      return 18;

    case "desert-expedition":
      return 25;

    default:
      return 0;
  }
}


export function roadFeasibilityEvidence(
  destination,
) {
  const profile =
    destinationAccessProfile(
      destination,
    );

  return {
    accessClass:
      profile.accessClass,

    roadFactor:
      profile.roadFactor,

    requires4x4:
      profile.requires4x4,

    requiresGuide:
      profile.requiresGuide,

    penalty:
      roadFeasibilityPenalty(
        destination,
      ),
  };
}


export function requiresSpecialAccess(
  destination,
) {
  const profile =
    destinationAccessProfile(
      destination,
    );

  return (
    profile.requires4x4 ||
    profile.requiresGuide
  );
}
